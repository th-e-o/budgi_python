# ui/layouts.py - Version complète avec tous les imports
import streamlit as st
from typing import Dict, Any, Callable  # Import manquant ajouté
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
    
    # Modifications pour ui/layouts.py - Ajout du drag & drop

def _render_main_chat(self, on_message_send: Callable, on_file_upload: Callable):
    """Rend la zone principale du chat avec drag & drop"""
    # Header
    st.markdown(
        self.chat_components.render_header(),
        unsafe_allow_html=True
    )
    
    # Container pour les messages avec ID unique pour le scroll et drag & drop
    chat_container = st.container(height=500)
    
    # Zone de drag & drop invisible sur tout le chat
    st.markdown("""
    <div id="chat-drop-zone" style="
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        z-index: -1;
        pointer-events: none;
    ">
        <div id="drop-overlay" style="
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 85, 164, 0.1);
            border: 3px dashed #0055A4;
            z-index: 9999;
            pointer-events: none;
            display: flex;
            align-items: center;
            justify-content: center;
        ">
            <div style="
                background: white;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                text-align: center;
            ">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📎</div>
                <div style="font-size: 1.5rem; color: #0055A4; font-weight: bold;">
                    Déposez votre fichier ici
                </div>
                <div style="color: #666; margin-top: 0.5rem;">
                    PDF, DOCX, TXT, MSG, XLSX, JSON
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with chat_container:
        self._render_messages_area(on_message_send)
        
        # Anchor pour forcer le scroll en bas
        st.markdown('<div id="chat-bottom"></div>', unsafe_allow_html=True)
    
    # Zone d'input avec colonnes pour le fichier
    col1, col2 = st.columns([10, 1])
    
    with col1:
        # st.chat_input gère automatiquement Enter et l'effacement
        prompt = st.chat_input(
            "Tapez votre message...",
            key="chat_input",
            max_chars=2000
        )
    
    with col2:
        # Upload de fichier (sera aussi utilisé par le drag & drop)
        uploaded_file = st.file_uploader(
            "📎",
            type=['pdf', 'docx', 'txt', 'msg', 'xlsx', 'json'],
            key="file_upload",
            label_visibility="collapsed",
            help="Joindre un fichier ou glisser-déposer"
        )
    
    # Gérer l'envoi du message
    if prompt:
        on_message_send(prompt)
    
    # Gérer l'upload de fichier
    if uploaded_file:
        # Vérifier si c'est un nouveau fichier
        if 'last_uploaded_file' not in st.session_state or \
           st.session_state.last_uploaded_file != uploaded_file.name:
            st.session_state.last_uploaded_file = uploaded_file.name
            on_file_upload(uploaded_file)
    
    # JavaScript pour drag & drop et scroll
    st.markdown("""
    <script>
    // Configuration du drag & drop
    function setupDragDrop() {
        let dragCounter = 0;
        const dropOverlay = document.getElementById('drop-overlay');
        
        // Empêcher le comportement par défaut
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            document.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        // Gérer l'entrée dans la zone
        ['dragenter', 'dragover'].forEach(eventName => {
            document.addEventListener(eventName, function(e) {
                if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
                    dragCounter++;
                    if (dropOverlay && dragCounter === 1) {
                        dropOverlay.style.display = 'flex';
                    }
                }
            }, false);
        });
        
        // Gérer la sortie de la zone
        document.addEventListener('dragleave', function(e) {
            dragCounter--;
            if (dragCounter === 0 && dropOverlay) {
                dropOverlay.style.display = 'none';
            }
        }, false);
        
        // Gérer le drop
        document.addEventListener('drop', function(e) {
            dragCounter = 0;
            if (dropOverlay) {
                dropOverlay.style.display = 'none';
            }
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                // Trouver l'input file de Streamlit
                const fileInput = document.querySelector('input[type="file"][accept*=".pdf"]');
                if (fileInput) {
                    // Créer un nouveau FileList avec le fichier
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(files[0]);
                    fileInput.files = dataTransfer.files;
                    
                    // Déclencher l'événement change
                    const event = new Event('change', { bubbles: true });
                    fileInput.dispatchEvent(event);
                    
                    // Notification visuelle
                    showDropNotification(files[0].name);
                }
            }
        }, false);
    }
    
    // Notification après drop
    function showDropNotification(filename) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #0055A4;
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
        `;
        notification.innerHTML = `📎 ${filename} ajouté`;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'fadeOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
    
    // Styles pour les animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }
    `;
    document.head.appendChild(style);
    
    // Scroll automatique
    function autoScroll() {
        const containers = document.querySelectorAll('[data-testid="stVerticalBlock"]');
        containers.forEach(container => {
            if (container.style.height === '500px' || 
                window.getComputedStyle(container).height === '500px') {
                container.scrollTop = container.scrollHeight;
            }
        });
        
        const anchor = document.getElementById('chat-bottom');
        if (anchor) {
            anchor.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
    }
    
    // Initialisation
    setupDragDrop();
    autoScroll();
    
    // Observer pour nouveaux messages
    const observer = new MutationObserver(autoScroll);
    const chatContainer = document.querySelector('[data-testid="stVerticalBlock"][style*="height: 500px"]');
    if (chatContainer) {
        observer.observe(chatContainer, { childList: true, subtree: true });
    }
    
    // Backup: scroll périodique
    setInterval(autoScroll, 1000);
    </script>
    """, unsafe_allow_html=True)
    
    def _render_messages_area(self, on_message_send: Callable):
        """Rend la zone des messages avec quick replies"""
        st.markdown('<div class="chat-messages">', unsafe_allow_html=True)
        
        # Afficher tous les messages
        for i, msg in enumerate(st.session_state.get('chat_history', [])):
            # Ignorer les messages système cachés
            if msg.get('meta') == 'file_content':
                continue
                
            html, needs_buttons = self.chat_components.render_message(msg, i)
            st.markdown(html, unsafe_allow_html=True)
            
            # Quick replies pour les messages bot
            if msg['role'] == 'assistant' and msg.get('type') != 'bpss_prompt':
                quick_reply = self.chat_components.render_quick_replies_for_bot(i)
                if quick_reply:
                    if quick_reply == "extract_budget":
                        # Stocker l'index du message pour l'extraction
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