# ui/components/chat.py - Version corrigée sans quick actions
import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional

class ChatComponents:
    """Composants UI pour le chat"""
    
    @staticmethod
    def render_header():
        """Affiche le header du chat"""
        return """
        <div class="chat-header">
            <div class="bot-avatar">🤖</div>
            <div class="bot-info">
                <h2>BudgiBot</h2>
                <div class="bot-status">
                    <span class="status-dot"></span>
                    <span>En ligne - Prêt à vous aider</span>
                </div>
            </div>
        </div>
        """
    
    @staticmethod
    def render_message(message: Dict, index: int = 0):
        """Affiche un message dans le chat"""
        timestamp = message.get('timestamp', datetime.now().strftime("%H:%M"))
        role_class = 'user' if message['role'] == 'user' else 'bot'
        
        if message.get('type') == 'bpss_prompt':
            # Message spécial avec boutons interactifs
            html = f"""
            <div class="message-wrapper bot">
                <div class="message-bubble bot">
                    <div>{message['content']}</div>
                    <span class="message-time">{timestamp}</span>
                </div>
            </div>
            """
            return html, True  # Flag pour indiquer qu'il faut des boutons
        else:
            return f"""
            <div class="message-wrapper {role_class}">
                <div class="message-bubble {role_class}">
                    <div>{message['content']}</div>
                    <span class="message-time">{timestamp}</span>
                </div>
            </div>
            """, False
    
    @staticmethod
    def render_typing_indicator():
        """Affiche l'indicateur de frappe"""
        return """
        <div class="message-wrapper bot">
            <div class="typing-indicator">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
        </div>
        """
    
    @staticmethod
    def render_quick_replies_for_bot(message_index: int):
        """
        Affiche les quick replies sous un message bot
        Similaire à l'application R
        """
        # Créer un conteneur unique pour chaque ensemble de boutons
        with st.container():
            cols = st.columns(4)
            
            with cols[0]:
                if st.button("Peux-tu détailler ?", 
                           key=f"detail_{message_index}",
                           use_container_width=True):
                    return "Peux-tu détailler ?"
            
            with cols[1]:
                if st.button("Donne-moi un exemple", 
                           key=f"example_{message_index}",
                           use_container_width=True):
                    return "Donne-moi un exemple"
            
            with cols[2]:
                if st.button("Résume", 
                           key=f"resume_{message_index}",
                           use_container_width=True):
                    return "Résume"
            
            with cols[3]:
                if st.button("Extrait les données budgétaires",
                           key=f"extract_{message_index}",
                           use_container_width=True):
                    return "extract_budget"
        
        return None
    
    @staticmethod
    def render_quick_actions():
        """Affiche les actions rapides - DÉSACTIVÉ"""
        # Retourner une chaîne vide pour ne rien afficher
        return ""
    
    @staticmethod
    def render_file_preview(filename: str):
        """Affiche un aperçu de fichier"""
        # Déterminer l'icône selon l'extension
        extension = filename.split('.')[-1].lower()
        icons = {
            'pdf': '📄',
            'xlsx': '📊',
            'docx': '📝',
            'txt': '📃',
            'msg': '📧',
            'json': '📋'
        }
        icon = icons.get(extension, '📎')
        
        return f"""
        <div class="file-preview">
            <span class="file-icon">{icon}</span>
            <span>{filename}</span>
        </div>
        """