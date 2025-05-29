# ui/layouts.py
import streamlit as st
from typing import Dict, Any, Callable
from datetime import datetime
from .components.chat import ChatComponents
from .components.sidebar import SidebarComponents
from .components.inputs import InputComponents

class MainLayout:
    """Layout principal de l'application"""
    
    def __init__(self, services: Dict[str, Any]):
        self.services = services
        self.chat_components = ChatComponents()
        self.sidebar_components = SidebarComponents()
        self.input_components = InputComponents()
    
    def render(self, 
               on_message_send: Callable,
               on_file_upload: Callable,
               on_tool_action: Callable):
        """Rend le layout complet de l'application"""
        
        # Layout principal sans colonnes imbriquées
        # Utiliser la sidebar de Streamlit pour les outils
        with st.sidebar:
            self._render_sidebar(on_tool_action)
        
        # Zone principale pour le chat
        self._render_main_chat(on_message_send, on_file_upload)
    
    def _render_main_chat(self, on_message_send: Callable, on_file_upload: Callable):
        """Rend la zone principale du chat"""
        # Header
        st.markdown(
            self.chat_components.render_header(),
            unsafe_allow_html=True
        )
        
        # Container pour les messages
        messages_container = st.container(height=500)
        with messages_container:
            self._render_messages_area(on_message_send)
        
        # Séparateur
        st.markdown("---")
        
        # Zone d'input et actions
        message, file, send_clicked = self.input_components.render_chat_input()
        
        # Quick actions
        st.markdown(
            self.chat_components.render_quick_actions(),
            unsafe_allow_html=True
        )
        
        # Gérer les événements
        if message and send_clicked:
            on_message_send(message)
        
        if file:
            on_file_upload(file)
    
    def _render_messages_area(self, on_message_send: Callable):
        """Rend la zone des messages avec quick replies"""
        st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
        
        # Afficher tous les messages
        for i, msg in enumerate(st.session_state.get('chat_history', [])):
            html, needs_buttons = self.chat_components.render_message(msg, i)
            st.markdown(html, unsafe_allow_html=True)
            
            # Quick replies pour les messages bot
            if msg['role'] == 'assistant' and msg.get('type') != 'bpss_prompt':
                quick_reply = self.chat_components.render_quick_replies_for_bot(i)
                if quick_reply:
                    if quick_reply == "extract_budget":
                        st.session_state.pending_action = {
                            'type': 'extract_budget',
                            'message_index': i
                        }
                        st.rerun()
                    else:
                        on_message_send(quick_reply)
            
            # Message BPSS prompt
            elif needs_buttons:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🛠️ Lancer l'outil Excel BPSS", 
                               key=f"bpss_yes_{i}",
                               type="primary"):
                        st.session_state.show_bpss_tool = True
                        st.rerun()
                with col2:
                    if st.button("Non merci", key=f"bpss_no_{i}"):
                        on_message_send("Non merci, continue")
        
        # Indicateur de frappe
        if st.session_state.get('is_typing', False):
            st.markdown(
                self.chat_components.render_typing_indicator(),
                unsafe_allow_html=True
            )
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_sidebar(self, on_tool_action: Callable):
        """Rend la sidebar avec les outils"""
        st.markdown("# 🛠️ Outils Budgétaires")
        
        # Vérifier si l'outil BPSS doit être ouvert
        bpss_expanded = st.session_state.get('show_bpss_tool', False)
        
        # BPSS Tool
        self.sidebar_components.render_tool_section(
            title="Outil BPSS Excel",
            icon="📊",
            key="bpss",
            render_content=lambda: self._handle_tool_action(
                self.sidebar_components.render_bpss_tool(self.services),
                on_tool_action
            ),
            expanded=bpss_expanded
        )
        
        # Excel Module (Mesures Catégorielles)
        self.sidebar_components.render_tool_section(
            title="Mesures Catégorielles",
            icon="📈",
            key="excel",
            render_content=lambda: self._handle_tool_action(
                self.sidebar_components.render_excel_module(self.services),
                on_tool_action
            ),
            expanded=True
        )
        
        # JSON Helper
        self.sidebar_components.render_tool_section(
            title="JSON Helper",
            icon="📄",
            key="json",
            render_content=lambda: self._handle_tool_action(
                self.sidebar_components.render_json_helper(self.services),
                on_tool_action
            ),
            expanded=False
        )
        
        # History Section
        st.markdown("---")
        history_action = self.sidebar_components.render_history_section(
            self.services['chat_handler']
        )
        if history_action:
            on_tool_action(history_action)
        
        # Réinitialiser le flag BPSS
        if bpss_expanded:
            st.session_state.show_bpss_tool = False
    
    def _handle_tool_action(self, action: Dict, callback: Callable):
        """Gère les actions des outils"""
        if action:
            callback(action)