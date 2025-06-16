import logging
from datetime import datetime
from typing import Dict, List
from fastapi import UploadFile

from backend.core.communication.ConnectionManager import ConnectionManager
from backend.core.excel_handler.excel_handler import UpdatedExcelHandler
from backend.core.excel_handler.excel_update_builder import ExcelUpdateBuilder

logger = logging.getLogger("ExcelSyncManager")


class ExcelSyncManager:
    """
    Orchestrates data synchronization for a SINGLE client session.
    Manages pending operations for user validation for that session.
    """

    def __init__(self, client_id: str, handler: UpdatedExcelHandler, conn_manager: ConnectionManager):
        self.client_id = client_id
        self.handler = handler
        self.conn_manager = conn_manager
        self.pending_operations: Dict[str, Dict] = {}
        logger.info(f"ExcelSyncManager initialized for Client ID: {self.client_id}")

    def new_update_builder(self) -> ExcelUpdateBuilder:
        """Creates a new, clean builder for defining a transaction."""
        return ExcelUpdateBuilder(self)

    async def commit_updates(self, operations: List[Dict], validate: bool):
        """Commits the operations, handling validation and targeted communication."""
        if not operations:
            return

        ui_ops = [{
            "id": op['id'],
            "type": op['frontend_type'].name,
            "description": op['description'],
            "payload": op['ui_payload']
        } for op in operations]

        if validate:
            self.pending_operations.clear()
            for op in operations:
                self.pending_operations[op['id']] = op

            logger.info(f"Sending {len(ui_ops)} operations for validation to Client ID: {self.client_id}")
            await self.conn_manager.send_to(self.client_id, 'propose_updates', {"operations": ui_ops})
        else:
            # Apply updates to the handler without validation
            handler_ops = [{
                "type": op['backend_type'],
                "description": op['description'],
                "payload": op['handler_payload']
            } for op in operations]
            task = self.handler.apply_updates(handler_ops)

            logger.info(f"Sending {len(ui_ops)} direct update operations to Client ID: {self.client_id}")
            await self.conn_manager.send_to(self.client_id, 'apply_direct_updates', {"operations": ui_ops})
            await self.conn_manager.send_to(self.client_id, "chat_message", {
                "role": "assistant", "content": "✅ Mise à jour directe appliquée.",
                "timestamp": datetime.now().isoformat()
            })

            # Finish the task in the background
            await task

    async def _broadcast_full_update(self, message: str):
        """
        Sends a full workbook update to THIS client.
        Used after validation when the client's state might be out of sync.
        """
        from core.ExcelToUniverConverterOpt import \
            ExcelToUniverConverterOpt  # Local import to avoid circular dependency
        if not self.handler.has_workbook(): return

        converter = ExcelToUniverConverterOpt(self.handler.workbook)
        updated_data = converter.convert()
        await self.conn_manager.send_to(self.client_id, 'workbook_update', updated_data)
        await self.conn_manager.send_to(self.client_id, "chat_message", {
            "role": "assistant", "content": f"✅ {message}", "timestamp": datetime.now().isoformat()
        })

    async def process_uploaded_file(self, file: UploadFile) -> str:
        """Traite un fichier uploadé et retourne son contenu textuel"""
        try:
            # Récupérer le service de chat de la session
            session_id = self._get_session_id()
            chat_service = SESSION_CHAT_SERVICES.get(session_id)
            
            if not chat_service:
                raise Exception("Service de chat non initialisé")
            
            # Lire le contenu du fichier
            file_content_bytes = await file.read()
            
            # Traiter directement depuis les bytes
            file_content_text = chat_service._read_file_content_from_bytes(
                file_content_bytes, file.filename
            )
            
            return file_content_text
            
        except Exception as e:
            logger.error(f"Erreur traitement fichier {file.filename}: {str(e)}")
            raise
    
    async def process_with_llm(self, context: Dict) -> str:
        """Traite le contexte avec le LLM (sans contexte Excel)"""
        try:
            session_id = self._get_session_id()
            chat_service = SESSION_CHAT_SERVICES.get(session_id)
            
            if not chat_service:
                raise Exception("Service de chat non initialisé")
            
            # Construire le message simple pour le LLM
            llm_message = self._build_simple_message(context)
            
            # Traiter avec le LLM
            llm_response = await chat_service.process_user_message(
                llm_message, context['chat_history']
            )
            
            return llm_response
            
        except Exception as e:
            logger.error(f"Erreur traitement LLM: {str(e)}")
            raise
    
    def _build_simple_message(self, context: Dict) -> str:
        """Construit un message simple avec fichier et message utilisateur"""
        parts = []
        
        # Message utilisateur
        if context.get('user_message'):
            parts.append(f"Question de l'utilisateur : {context['user_message']}")
        
        # Informations sur le fichier
        if context.get('file_name'):
            parts.append(f"\nFichier envoyé : {context['file_name']}")
            
            # Contenu du fichier
            if context.get('file_content'):
                parts.append(f"\nContenu du fichier :")
                
                # Aperçu du contenu
                content = context['file_content']
                if len(content) > 1000:
                    parts.append(f"{content[:1000]}...")
                else:
                    parts.append(content)
        
        return "\n".join(parts)
    
    async def send_user_message_to_chat(self, file_name: str, message: str):
        """Envoie le message utilisateur au chat"""
        user_message_content = f"📄 Fichier envoyé : {file_name}"
        if message:
            user_message_content += f"\nMessage : {message}"
        
        await self.conn_manager.send_to(self.client_id, "chat_message", {
            "role": "user",
            "content": user_message_content,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "file_name": file_name
        })
    
    async def send_llm_response(self, response: str):
        """Envoie la réponse du LLM au chat"""
        await self.conn_manager.send_to(self.client_id, "chat_message", {
            "role": "assistant",
            "content": response,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
    
    async def send_error_to_chat(self, error_message: str):
        """Envoie un message d'erreur au chat"""
        await self.conn_manager.send_to(self.client_id, "chat_message", {
            "role": "assistant",
            "content": f"❌ {error_message}",
            "error": True,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
    
    def _get_session_id(self) -> str:
        """Récupère l'ID de session pour ce sync manager"""
        for session_id, manager in SESSION_SYNC_MANAGERS.items():
            if manager.client_id == self.client_id:
                return session_id
        raise Exception("Session non trouvée")

    # --- Handlers for Incoming WebSocket Messages ---

    async def handle_cell_update(self, payload: Dict):
        """Handles a direct cell edit from the UI."""
        logger.info(f"Received cell update from Client ID: {self.client_id}, Payload: {payload}")
        self.handler.apply_component_update(payload)

    async def handle_validate_op(self, payload):
        """
        Handles user validated and rejected requests of the following format:

            {
                "accepted": ["9c2e0ed6-f744-4eea-84fe-1c63e9645e92"],
                "refused": ["ddbeaa31-89d4-41a8-b53b-04147a087455"]
            }
        """
        accepted_ops = []
        for op_id in payload.get('accepted', []):
            op = self.pending_operations.pop(op_id, None)
            if op:
                handler_op = {
                    "type": op['backend_type'],
                    "description": op['description'],
                    "payload": op['handler_payload']
                }
                accepted_ops.append(handler_op)

        await self.handler.apply_updates(accepted_ops)

        self.pending_operations.clear()
        message = f"✅ {len(accepted_ops)} modifications validées et appliquées."
        await self.conn_manager.send_to(self.client_id, "chat_message", {
            "role": "assistant",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })