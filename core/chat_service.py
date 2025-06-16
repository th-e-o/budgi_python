import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime

from core.llm_client import MistralClient
from core.file_handler import FileHandler
from modules.budget_extractor import BudgetExtractor

logger = logging.getLogger(__name__)

class ChatService:
    """Service principal pour gérer les interactions chat avec le LLM"""
    
    def __init__(self):
        self.llm_client = MistralClient()
        self.file_handler = FileHandler()
        self.budget_extractor = BudgetExtractor()
        
    async def process_user_message(self, message_content: str, 
                                 frontend_history: List[Dict]) -> str:
        """
        Traite un message utilisateur et retourne la réponse du LLM
        
        Args:
            message_content: Le contenu du message utilisateur
            frontend_history: L'historique des messages depuis le frontend
            
        Returns:
            La réponse du LLM
        """
        try:
            # Préparer les messages pour l'API LLM (format standard)
            api_messages = self._prepare_messages_for_llm(frontend_history, message_content)
            
            # Appeler le LLM
            llm_response = await self.llm_client.chat(api_messages)
            
            if llm_response:
                return llm_response
            else:
                return "Désolé, je n'ai pas pu traiter votre demande. Veuillez réessayer."
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {str(e)}", exc_info=True)
            return f"Une erreur s'est produite: {str(e)}"
    
    async def process_file_content_directly(self, file_content_raw: bytes, file_name: str, 
                                          user_message: str, frontend_history: List[Dict]) -> str:
        """
        Traite directement le contenu d'un fichier sans créer de fichier temporaire
        
        Args:
            file_content_raw: Le contenu brut du fichier (bytes)
            file_name: Le nom du fichier
            user_message: Le message utilisateur (peut être vide)
            frontend_history: L'historique des messages depuis le frontend
            
        Returns:
            La réponse du LLM
        """
        try:
            # Lire le contenu selon le type de fichier
            file_content_text = self._read_file_content_from_bytes(file_content_raw, file_name)
            
            # Traiter le fichier selon son type
            processed_content = await self._process_file_content(
                file_content_text, file_name, user_message
            )
            
            # Préparer les messages pour l'API LLM
            api_messages = self._prepare_messages_for_llm(frontend_history, processed_content)
            
            # Appeler le LLM
            llm_response = await self.llm_client.chat(api_messages)
            
            if llm_response:
                return llm_response
            else:
                return "Désolé, je n'ai pas pu traiter votre fichier. Veuillez réessayer."
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du fichier: {str(e)}", exc_info=True)
            return f"Erreur lors du traitement du fichier: {str(e)}"
    
    def _read_file_content_from_bytes(self, file_content: bytes, file_name: str) -> str:
        """Lit le contenu d'un fichier à partir des bytes selon son extension"""
        file_ext = Path(file_name).suffix.lower()
        
        try:
            if file_ext == '.txt':
                return self._read_text_from_bytes(file_content)
            elif file_ext == '.pdf':
                return self._read_pdf_from_bytes(file_content)
            elif file_ext == '.docx':
                return self._read_docx_from_bytes(file_content)
            elif file_ext == '.msg':
                return self._read_msg_from_bytes(file_content)
            else:
                return "(Format de fichier non pris en charge)"
        except Exception as e:
            logger.error(f"Erreur lecture fichier {file_name}: {str(e)}")
            return f"(Erreur lors de la lecture du fichier: {str(e)})"
    
    def _read_text_from_bytes(self, content: bytes) -> str:
        """Lit un fichier texte depuis les bytes avec détection d'encodage"""
        import chardet
        
        # Détecter l'encodage
        result = chardet.detect(content)
        encoding = result['encoding'] or 'utf-8'
        
        # Décoder avec l'encodage détecté
        return content.decode(encoding, errors='replace')
    
    def _read_pdf_from_bytes(self, content: bytes) -> str:
        """Lit un fichier PDF depuis les bytes"""
        import PyPDF2
        import io
        
        text_content = []
        pdf_file = io.BytesIO(content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        for page in pdf_reader.pages:
            text_content.append(page.extract_text())
        
        return '\n'.join(text_content)
    
    def _read_docx_from_bytes(self, content: bytes) -> str:
        """Lit un fichier DOCX depuis les bytes"""
        import docx
        import io
        
        doc_file = io.BytesIO(content)
        doc = docx.Document(doc_file)
        
        text_content = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_content.append(paragraph.text)
        
        return '\n'.join(text_content)
    
    def _read_msg_from_bytes(self, content: bytes) -> str:
        """Lit un fichier MSG depuis les bytes"""
        import extract_msg
        import tempfile
        import os
        
        # Pour les fichiers MSG, on doit malheureusement créer un fichier temporaire
        # car extract_msg ne supporte pas les BytesIO
        with tempfile.NamedTemporaryFile(delete=False, suffix='.msg') as tmp_file:
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            msg = extract_msg.Message(tmp_file_path)
            
            # Récupération sécurisée des champs
            subject = msg.subject or "(Aucun sujet)"
            sender = msg.sender or "(Expéditeur inconnu)"
            
            # Récupération des destinataires
            recipients = []
            if hasattr(msg, 'recipients') and msg.recipients:
                for recipient in msg.recipients:
                    if hasattr(recipient, 'email') and recipient.email:
                        recipients.append(recipient.email)
                    elif hasattr(recipient, 'name') and recipient.name:
                        recipients.append(recipient.name)
            recipients_str = "; ".join(recipients) if recipients else "(Destinataires inconnus)"
            
            # Date
            date = str(msg.date) if hasattr(msg, 'date') and msg.date else "(Date inconnue)"
            
            # Corps du message
            body = ""
            if hasattr(msg, 'body') and msg.body:
                body = msg.body
            elif hasattr(msg, 'htmlBody') and msg.htmlBody:
                # Si pas de body texte, essayer de récupérer le HTML
                import re
                # Nettoyer le HTML basiquement
                html_body = msg.htmlBody
                # Enlever les balises HTML
                body = re.sub('<[^<]+?>', '', html_body)
                # Remplacer les entités HTML courantes
                body = body.replace('&nbsp;', ' ')
                body = body.replace('&lt;', '<')
                body = body.replace('&gt;', '>')
                body = body.replace('&amp;', '&')
                body = body.replace('&quot;', '"')
            
            if not body.strip():
                body = "(Aucun contenu dans l'email)"
            
            # Pièces jointes
            attachments = []
            if hasattr(msg, 'attachments') and msg.attachments:
                for attachment in msg.attachments:
                    if hasattr(attachment, 'longFilename'):
                        attachments.append(attachment.longFilename)
                    elif hasattr(attachment, 'filename'):
                        attachments.append(attachment.filename)
            
            attachments_str = ""
            if attachments:
                attachments_str = f"\n\nPièces jointes ({len(attachments)}):\n" + "\n".join(f"- {att}" for att in attachments)
            
            content_str = f"""Type de message : Mail
Sujet : {subject}
De : {sender}
À : {recipients_str}
Date : {date}

--- Contenu du message ---

{body}{attachments_str}"""
            
            # Fermer le message pour libérer les ressources
            msg.close()
            
            return content_str
            
        except Exception as e:
            logger.error(f"Erreur extraction MSG: {str(e)}")
            return f"(Impossible de lire le fichier MSG: {str(e)})"
        finally:
            # Nettoyer le fichier temporaire
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    def _prepare_messages_for_llm(self, frontend_history: List[Dict], 
                            new_message: str) -> List[Dict]:
        """
        Prépare les messages pour l'API LLM en filtrant l'historique frontend
        
        Args:
            frontend_history: Historique complet du frontend
            new_message: Nouveau message à ajouter
            
        Returns:
            Liste des messages formatés pour l'API LLM
        """
        # ✅ AJOUTER : Debug de l'historique reçu
        logger.info(f"Frontend history reçu: {len(frontend_history)} messages")
        for i, msg in enumerate(frontend_history):
            logger.info(f"  Message {i}: {msg.get('role')} - {msg.get('content', '')[:50]}...")
        
        # Filtrer l'historique pour ne garder que role et content
        api_messages = []
        
        # Prendre les derniers messages (limiter pour éviter de surcharger l'API)
        recent_history = frontend_history[-10:] if len(frontend_history) > 10 else frontend_history
        
        # Traitement correct de l'historique
        for msg in recent_history:
            if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                # Vérifier que le rôle est valide
                role = msg['role']
                if role in ['user', 'assistant', 'system']:
                    clean_msg = {
                        'role': role,
                        'content': str(msg['content'])  # S'assurer que c'est une string
                    }
                    api_messages.append(clean_msg)
                else:
                    logger.warning(f"Rôle invalide dans l'historique: {role}")
            else:
                logger.warning(f"Message invalide dans l'historique: {msg}")
        
        # Ajouter le nouveau message en tant qu'utilisateur
        if new_message and new_message.strip():
            api_messages.append({
                'role': 'user',
                'content': str(new_message)
            })
        
        # Debug des messages préparés pour l'API
        logger.info(f"Messages préparés pour LLM: {len(api_messages)} total")
        for i, msg in enumerate(api_messages):
            logger.info(f"  API Message {i}: {msg['role']} - {msg['content'][:50]}...")
        
        # Vérifier que nous avons des messages valides
        if not api_messages:
            logger.warning("Aucun message valide pour l'API LLM")
            return [{
                'role': 'user',
                'content': new_message or "Message vide"
            }]
        
        # S'assurer qu'on ne dépasse pas les limites de l'API
        if len(api_messages) > 20:  # Limite raisonnable
            logger.info(f"Trop de messages ({len(api_messages)}), limitation à 20")
            api_messages = api_messages[-20:]
        
        return api_messages
    
    async def _process_file_content(self, file_content: str, file_name: str, 
                                  user_message: str) -> str:
        """Traite le contenu d'un fichier selon son type"""
        file_ext = Path(file_name).suffix.lower()
        
        # Message de base avec le fichier
        base_message = f"Fichier envoyé : {file_name}\n"
        
        if user_message and user_message.strip():
            base_message += f"Question : {user_message}\n\n"
        
        # Traitement spécifique selon le type de fichier
        if file_ext in ['.pdf', '.docx', '.txt', '.msg']:
            # Pour les documents texte, essayer d'extraire des données budgétaires
            budget_data = await self._try_extract_budget_data(file_content)
            
            if budget_data:
                base_message += f"📊 **Données budgétaires détectées ({len(budget_data)} entrées):**\n\n"
                for i, entry in enumerate(budget_data[:5], 1):  # Limiter à 5 pour l'affichage
                    base_message += f"{i}. **{entry.get('Description', 'N/A')}**\n"
                    base_message += f"   - Montant: {entry.get('Montant', 'N/A')} {entry.get('Unité', '')}\n"
                    base_message += f"   - Nature: {entry.get('Nature', 'N/A')}\n"
                    if entry.get('Date'):
                        base_message += f"   - Date: {entry.get('Date')}\n"
                    base_message += "\n"
                
                if len(budget_data) > 5:
                    base_message += f"... et {len(budget_data) - 5} autres entrées\n\n"
            
            # Ajouter un extrait du contenu original
            preview_length = 500
            if len(file_content) > preview_length:
                base_message += f"**Extrait du contenu:**\n{file_content[:preview_length]}...\n\n"
            else:
                base_message += f"**Contenu complet:**\n{file_content}\n\n"
                
        elif file_ext == '.xlsx':
            base_message += "Fichier Excel chargé dans l'interface. Vous pouvez maintenant poser des questions sur les données ou demander une analyse.\n\n"
            
        else:
            base_message += f"**Contenu du fichier ({file_ext}):**\n{file_content}\n\n"
        
        return base_message
    
    async def _try_extract_budget_data(self, content: str) -> Optional[List[Dict]]:
        """Essaie d'extraire des données budgétaires du contenu"""
        try:
            budget_data = await self.budget_extractor.extract_budget_data(content)
            return budget_data if budget_data else None
        except Exception as e:
            logger.warning(f"Échec extraction données budgétaires: {str(e)}")
            return None