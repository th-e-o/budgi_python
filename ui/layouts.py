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
        
        # Layout en 2 colonnes
        chat_col, tools_col = st.columns([2, 1])
        
        # Colonne du chat
        with chat_col:
            self._render_chat_column(on_message_send, on_file_upload)
        
        # Colonne des outils
        with tools_col:
            self._render_tools_column(on_tool_action)
    
    def _render_chat_column(self, on_message_send: Callable, on_file_upload: Callable):
        """Rend la colonne du chat"""
        # Container principal
        chat_container = st.container()
        
        with chat_container:
            # Header
            st.markdown(
                self.chat_components.render_header(),
                unsafe_allow_html=True
            )
            
            # Messages
            self._render_messages_area(on_message_send)
            
            # Input
            message, file, send_clicked = self.input_components.render_chat_input()
            
            # Quick actions (comme dans l'app R)
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
        messages_container = st.container()
        
        with messages_container:
            st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
            
            # Afficher tous les messages
            for i, msg in enumerate(st.session_state.get('chat_history', [])):
                html, needs_buttons = self.chat_components.render_message(msg, i)
                st.markdown(html, unsafe_allow_html=True)
                
                # Si c'est un message bot (pas user), ajouter les quick replies
                if msg['role'] == 'assistant' and msg.get('type') != 'bpss_prompt':
                    # Quick replies comme dans l'app R
                    quick_reply = self.chat_components.render_quick_replies_for_bot(i)
                    if quick_reply:
                        if quick_reply == "extract_budget":
                            # Action spéciale pour l'extraction
                            st.session_state.pending_action = {
                                'type': 'extract_budget',
                                'message_index': i
                            }
                            st.rerun()
                        else:
                            # Message normal
                            on_message_send(quick_reply)
                
                # Si c'est un message BPSS prompt
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
    
    def _render_tools_column(self, on_tool_action: Callable):
        """Rend la colonne des outils"""
        st.markdown("### 🛠️ Outils Budgétaires")
        
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
            expanded=True  # Ouvert par défaut comme dans l'app R
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
        
        # Réinitialiser le flag BPSS après affichage
        if bpss_expanded:
            st.session_state.show_bpss_tool = False
    
    def _handle_tool_action(self, action: Dict, callback: Callable):
        """Gère les actions des outils"""
        if action:
            callback(action)