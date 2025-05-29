# ui/components/inputs.py
import streamlit as st
from typing import Tuple, Optional, Any  # <-- Ajout de l'import Any

class InputComponents:
    """Composants pour les entrées utilisateur"""
    
    @staticmethod
    def render_chat_input() -> Tuple[Optional[str], Optional[Any], bool]:
        """
        Rend la zone de saisie du chat
        Retourne: (message, fichier, bouton_envoi_cliqué)
        """
        # Container pour l'input
        st.markdown('<div class="chat-input-container">', unsafe_allow_html=True)
        
        # Layout en colonnes
        input_col, actions_col = st.columns([5, 1])
        
        with input_col:
            # Zone de texte principale
            user_input = st.text_area(
                "Message",
                key="user_message_input",
                placeholder="Tapez votre message... (Shift+Enter pour nouvelle ligne)",
                height=80,
                label_visibility="collapsed",
                max_chars=2000
            )
        
        with actions_col:
            # Boutons d'action
            col_attach, col_send = st.columns(2)
            
            with col_attach:
                # Upload de fichier avec icône
                uploaded_file = st.file_uploader(
                    "📎",
                    type=['pdf', 'docx', 'txt', 'msg', 'xlsx', 'json'],
                    key="file_upload_chat",
                    label_visibility="collapsed",
                    help="Joindre un fichier"
                )
            
            with col_send:
                # Bouton d'envoi
                send_clicked = st.button(
                    "➤",
                    key="send_button",
                    help="Envoyer le message",
                    type="primary"
                )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Validation de l'input
        message_to_send = None
        if send_clicked and user_input and user_input.strip():
            message_to_send = user_input.strip()
        
        return message_to_send, uploaded_file, send_clicked
    
    @staticmethod
    def render_search_input() -> Optional[str]:
        """Rend une barre de recherche"""
        search = st.text_input(
            "🔍 Rechercher",
            key="search_input",
            placeholder="Rechercher dans l'historique...",
            label_visibility="collapsed"
        )
        return search if search else None