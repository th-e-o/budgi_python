import streamlit as st
from typing import Tuple, Optional, Any

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
        input_col, actions_col = st.columns([4, 1])
        
        # Obtenir la clé dynamique
        input_key = f"user_message_input_{st.session_state.get('message_input_key', 0)}"
        
        with input_col:
            # Zone de texte principale avec clé dynamique
            user_input = st.text_area(
                "Message",
                key=input_key,
                placeholder="Tapez votre message... (Enter pour envoyer, Shift+Enter pour nouvelle ligne)",
                height=80,
                label_visibility="collapsed",
                max_chars=6000,
                value=""  # Toujours vide car nouvelle clé
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
        
        # JavaScript pour gérer la touche Enter
        st.markdown(f"""
        <script>
        // Attendre que le DOM soit prêt
        setTimeout(function() {{
            const textarea = document.querySelector('textarea[data-testid="{input_key}"]');
            if (!textarea) {{
                // Chercher par aria-label si data-testid ne fonctionne pas
                const textareas = document.querySelectorAll('textarea');
                for (let ta of textareas) {{
                    if (ta.getAttribute('aria-label') === 'Message') {{
                        setupEnterHandler(ta);
                        break;
                    }}
                }}
            }} else {{
                setupEnterHandler(textarea);
            }}
            
            function setupEnterHandler(textarea) {{
                if (!textarea.hasAttribute('data-enter-setup')) {{
                    textarea.setAttribute('data-enter-setup', 'true');
                    textarea.addEventListener('keydown', function(e) {{
                        if (e.key === 'Enter' && !e.shiftKey) {{
                            e.preventDefault();
                            // Trouver et cliquer sur le bouton d'envoi
                            const sendBtn = document.querySelector('button[kind="primary"]');
                            if (sendBtn) {{
                                sendBtn.click();
                            }}
                        }}
                    }});
                }}
            }}
        }}, 100);
        </script>
        """, unsafe_allow_html=True)
        
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