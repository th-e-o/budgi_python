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
        msg = extract_msg.Message(file_path)
        
        subject = msg.subject or "(Aucun sujet)"
        sender = msg.sender or "(Expéditeur inconnu)"
        
        # Récupération des destinataires
        recipients = []
        if msg.recipients:
            for recipient in msg.recipients:
                if hasattr(recipient, 'email') and recipient.email:
                    recipients.append(recipient.email)
        recipients_str = "; ".join(recipients) if recipients else "(Destinataires inconnus)"
        
        date = str(msg.date) if msg.date else "(Date inconnue)"
        body = msg.body or "(Aucun contenu dans l'email)"
        
        content = f"""Type de message : Mail
Sujet : {subject}
De : {sender}
À : {recipients_str}
Date : {date}

--- Contenu du message ---

{body}"""
        
        # Fermer le message pour libérer les ressources
        msg.close()
        
        return content