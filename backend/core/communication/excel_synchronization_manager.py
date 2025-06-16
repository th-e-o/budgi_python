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
        self._session_id = None
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

    async def process_uploaded_file(self, file) -> str:
        """Traite un fichier uploadé et retourne son contenu textuel"""
        try:
            logger.info(f"process_uploaded_file appelé pour: {file.filename}")
            
            # ✅ CORRECTION : Pas besoin de SESSION_CHAT_SERVICES pour l'instant
            # On va faire une version simple qui lit juste le fichier
            
            # Lire le fichier
            file_content_bytes = await file.read()
            logger.info(f"Fichier lu: {len(file_content_bytes)} bytes")
            
            # Version simple : décoder en UTF-8
            try:
                file_content_text = file_content_bytes.decode('utf-8', errors='replace')
                logger.info(f"Contenu décodé: {len(file_content_text)} caractères")
                return file_content_text
            except Exception as decode_error:
                logger.error(f"Erreur décodage: {decode_error}")
                return f"Erreur lors du décodage du fichier: {str(decode_error)}"
            
        except Exception as e:
            logger.error(f"Erreur process_uploaded_file: {str(e)}", exc_info=True)
            raise
    
    async def process_with_llm(self, context: dict) -> str:
        """Traite le contexte avec le LLM - Version simple"""
        try:
            logger.info(f"process_with_llm appelé")
            
            # ✅ VERSION SIMPLE : Pas de LLM pour l'instant, juste un résumé
            file_name = context.get('file_name', 'Fichier inconnu')
            user_message = context.get('user_message', '')
            file_content = context.get('file_content', '')
            
            # Construire une réponse simple
            response_parts = [
                f"📄 **Fichier analysé : {file_name}**",
                f"📏 **Taille du contenu :** {len(file_content)} caractères"
            ]
            
            if user_message:
                response_parts.append(f"💬 **Votre message :** {user_message}")
            
            if file_content:
                # Aperçu du contenu
                preview = file_content[:300] + "..." if len(file_content) > 300 else file_content
                response_parts.append(f"📋 **Aperçu du contenu :**\n```\n{preview}\n```")
            
            response = "\n\n".join(response_parts)
            response += "\n\n✨ *Chat-LLM en cours d'intégration - Version test*"
            
            logger.info(f"Réponse générée: {len(response)} caractères")
            return response
            
        except Exception as e:
            logger.error(f"Erreur process_with_llm: {str(e)}", exc_info=True)
            return f"❌ Erreur lors du traitement : {str(e)}"
    
    async def send_user_message_to_chat(self, file_name: str, message: str):
        """Envoie le message utilisateur au chat"""
        try:
            user_content = f"📄 Fichier envoyé : {file_name}"
            if message:
                user_content += f"\nMessage : {message}"
            
            await self.conn_manager.send_to(self.client_id, "chat_message", {
                "role": "user",
                "content": user_content,
                "timestamp": datetime.utcnow().isoformat(),
                "file_name": file_name
            })
            logger.info(f"Message utilisateur envoyé: {file_name}")
            
        except Exception as e:
            logger.error(f"Erreur send_user_message_to_chat: {str(e)}", exc_info=True)
    
    async def send_llm_response(self, response: str):
        """Envoie la réponse du LLM au chat"""
        try:
            await self.conn_manager.send_to(self.client_id, "chat_message", {
                "role": "assistant",
                "content": response,
                "timestamp": datetime.datetime.utcnow().isoformat()
            })
            logger.info(f"Réponse envoyée: {len(response)} caractères")
            
        except Exception as e:
            logger.error(f"Erreur send_llm_response: {str(e)}", exc_info=True)
    
    async def send_error_to_chat(self, error_message: str):
        """Envoie un message d'erreur au chat"""
        try:
            await self.conn_manager.send_to(self.client_id, "chat_message", {
                "role": "assistant",
                "content": f"❌ {error_message}",
                "error": True,
                "timestamp": datetime.datetime.utcnow().isoformat()
            })
            logger.info(f"Erreur envoyée au chat: {error_message}")
            
        except Exception as e:
            logger.error(f"Erreur send_error_to_chat: {str(e)}", exc_info=True)

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