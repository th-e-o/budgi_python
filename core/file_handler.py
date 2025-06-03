# core/file_handler.py - Version corrigée pour les mails
import os
from pathlib import Path
from typing import Optional, Union
import PyPDF2
import docx
import extract_msg
import chardet
import logging

logger = logging.getLogger(__name__)

class FileHandler:
    """Gère la lecture de différents types de fichiers"""
    
    @staticmethod
    def read_file(file_path: Union[str, Path], file_name: str) -> str:
        """Lit le contenu d'un fichier selon son extension"""
        file_ext = Path(file_name).suffix.lower()
        
        try:
            if file_ext == '.txt':
                return FileHandler._read_text_file(file_path)
            elif file_ext == '.pdf':
                return FileHandler._read_pdf_file(file_path)
            elif file_ext == '.docx':
                return FileHandler._read_docx_file(file_path)
            elif file_ext == '.msg':
                return FileHandler._read_msg_file(file_path)
            else:
                return "(Format de fichier non pris en charge)"
        except Exception as e:
            logger.error(f"Erreur lecture fichier {file_name}: {str(e)}")
            return f"(Erreur lors de la lecture du fichier: {str(e)})"
    
    @staticmethod
    def _read_text_file(file_path: Union[str, Path]) -> str:
        """Lit un fichier texte avec détection d'encodage"""
        # Détecter l'encodage
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding'] or 'utf-8'
        
        # Lire avec l'encodage détecté
        with open(file_path, 'r', encoding=encoding, errors='replace') as f:
            return f.read()
    
    @staticmethod
    def _read_pdf_file(file_path: Union[str, Path]) -> str:
        """Lit un fichier PDF"""
        content = []
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                content.append(page.extract_text())
        return '\n'.join(content)
    
    @staticmethod
    def _read_docx_file(file_path: Union[str, Path]) -> str:
        """Lit un fichier DOCX"""
        doc = docx.Document(file_path)
        content = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                content.append(paragraph.text)
        return '\n'.join(content)
    
    @staticmethod
    def _read_msg_file(file_path: Union[str, Path]) -> str:
        """Lit un fichier MSG (email Outlook)"""
        try:
            msg = extract_msg.Message(file_path)
            
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
            
            content = f"""Type de message : Mail
Sujet : {subject}
De : {sender}
À : {recipients_str}
Date : {date}

--- Contenu du message ---

{body}{attachments_str}"""
            
            # Fermer le message pour libérer les ressources
            msg.close()
            
            logger.info(f"Mail extrait avec succès: {len(body)} caractères")
            return content
            
        except Exception as e:
            logger.error(f"Erreur extraction MSG: {str(e)}")
            # Essayer une approche alternative
            try:
                import email
                with open(file_path, 'rb') as f:
                    msg_data = f.read()
                    # Tenter de parser comme un fichier email standard
                    msg = email.message_from_bytes(msg_data)
                    
                    subject = msg.get('Subject', '(Aucun sujet)')
                    sender = msg.get('From', '(Expéditeur inconnu)')
                    recipients = msg.get('To', '(Destinataires inconnus)')
                    date = msg.get('Date', '(Date inconnue)')
                    
                    # Extraire le corps
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                                break
                    else:
                        body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
                    
                    return f"""Type de message : Mail
Sujet : {subject}
De : {sender}
À : {recipients}
Date : {date}

--- Contenu du message ---

{body}"""
            except:
                return f"(Impossible de lire le fichier MSG: {str(e)})"