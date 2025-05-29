# core/chat_handler.py
from typing import List, Dict, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)

class ChatHandler:
    """Gère l'historique et le traitement des conversations"""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
    
    def add_message(self, messages: List[Dict], role: str, content: str, **kwargs) -> List[Dict]:
        """Ajoute un message à l'historique"""
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        # Ajouter des métadonnées supplémentaires si fournies
        message.update(kwargs)
        
        messages.append(message)
        
        # Limiter la taille de l'historique
        if len(messages) > self.max_history:
            messages = messages[-self.max_history:]
        
        return messages
    
    def export_history(self, messages: List[Dict]) -> str:
        """Exporte l'historique en format texte"""
        export_lines = []
        export_lines.append(f"=== BudgiBot - Export de conversation ===")
        export_lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        export_lines.append("=" * 50)
        export_lines.append("")
        
        for msg in messages:
            timestamp = msg.get('timestamp', '')
            role = "Vous" if msg['role'] == 'user' else "BudgiBot"
            content = msg['content']
            
            export_lines.append(f"[{timestamp}] {role}:")
            export_lines.append(content)
            export_lines.append("")
            export_lines.append("-" * 30)
            export_lines.append("")
        
        return '\n'.join(export_lines)
    
    def filter_messages_for_api(self, messages: List[Dict]) -> List[Dict]:
        """Filtre les messages pour l'API (enlève les métadonnées)"""
        filtered = []
        for msg in messages:
            # Ne garder que role et content pour l'API
            filtered_msg = {
                'role': msg['role'],
                'content': msg['content']
            }
            filtered.append(filtered_msg)
        return filtered
    
    def get_last_file_content(self, messages: List[Dict]) -> Optional[str]:
        """Récupère le contenu du dernier fichier envoyé"""
        for msg in reversed(messages):
            if msg.get('meta') == 'fichier_content':
                return msg['content']
        return None
    
    def find_user_message_for_extraction(self, messages: List[Dict], bot_index: int) -> Optional[str]:
        """Trouve le message utilisateur associé à une réponse bot"""
        # Chercher le message utilisateur précédent
        for i in range(bot_index - 1, -1, -1):
            if messages[i]['role'] == 'user':
                content = messages[i]['content']
                
                # Si c'est un message de fichier, récupérer le contenu
                if content.startswith("Fichier envoyé :"):
                    return self.get_last_file_content(messages)
                else:
                    return content
        
        return None