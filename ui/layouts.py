# ui/layouts.py - Version avec Drag & Drop corrigé
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
        """Rend la zone principale du chat avec drag & drop"""
        
        # Zone de drop overlay (doit être avant tout le reste)
        st.markdown("""
        <div id="drop-overlay" style="
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 85, 164, 0.95);
            z-index: 9999;
            pointer-events: all;
        ">
            <div style="
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                padding: 3rem;
                border-radius: 20px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.2);
                text-align: center;
                border: 3px dashed #0055A4;
            ">
                <div style="font-size: 4rem; margin-bottom: 1rem;">📎</div>
                <div style="font-size: 2rem; color: #0055A4; font-weight: bold; margin-bottom: 0.5rem;">
                    Déposez votre fichier ici
                </div>
                <div style="color: #666; font-size: 1.1rem;">
                    Formats supportés : PDF, DOCX, TXT, MSG, XLSX, JSON
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Header
        st.markdown(
            self.chat_components.render_header(),
            unsafe_allow_html=True
        )
        
        # Container pour les messages
        chat_container = st.container(height=500)
        
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
        
        # JavaScript amélioré pour drag & drop
        st.markdown("""
        <script>
        (function() {
            let dragCounter = 0;
            let dropOverlay = null;
            let initialized = false;
            
            function initDragDrop() {
                if (initialized) return;
                initialized = true;
                
                console.log('Initializing drag and drop...');
                
                // Récupérer l'overlay
                dropOverlay = document.getElementById('drop-overlay');
                if (!dropOverlay) {
                    console.error('Drop overlay not found!');
                    return;
                }
                
                // Empêcher le comportement par défaut sur tout le document
                ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                    document.addEventListener(eventName, function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                    }, false);
                });
                
                // Gérer l'entrée dans la zone (document entier)
                document.addEventListener('dragenter', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Vérifier si c'est un fichier
                    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
                        const item = e.dataTransfer.items[0];
                        if (item.kind === 'file') {
                            dragCounter++;
                            if (dragCounter === 1 && dropOverlay) {
                                console.log('Showing drop overlay');
                                dropOverlay.style.display = 'block';
                            }
                        }
                    }
                }, false);
                
                // Gérer le survol
                document.addEventListener('dragover', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    e.dataTransfer.dropEffect = 'copy';
                }, false);
                
                // Gérer la sortie
                document.addEventListener('dragleave', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    dragCounter--;
                    if (dragCounter <= 0) {
                        dragCounter = 0;
                        if (dropOverlay) {
                            console.log('Hiding drop overlay');
                            dropOverlay.style.display = 'none';
                        }
                    }
                }, false);
                
                // Gérer le drop
                document.addEventListener('drop', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    console.log('File dropped!');
                    dragCounter = 0;
                    
                    if (dropOverlay) {
                        dropOverlay.style.display = 'none';
                    }
                    
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                        handleFileDrop(files[0]);
                    }
                }, false);
                
                // Gérer aussi le drop sur l'overlay
                if (dropOverlay) {
                    dropOverlay.addEventListener('drop', function(e) {
                        e.preventDefault();
                        e.stopPropagation();
                        
                        console.log('File dropped on overlay!');
                        dragCounter = 0;
                        dropOverlay.style.display = 'none';
                        
                        const files = e.dataTransfer.files;
                        if (files.length > 0) {
                            handleFileDrop(files[0]);
                        }
                    }, false);
                }
            }
            
            function handleFileDrop(file) {
                console.log('Handling file:', file.name);
                
                // Vérifier le type de fichier
                const allowedTypes = ['.pdf', '.docx', '.txt', '.msg', '.xlsx', '.json'];
                const fileExt = '.' + file.name.split('.').pop().toLowerCase();
                
                if (!allowedTypes.includes(fileExt)) {
                    showNotification('Type de fichier non supporté: ' + fileExt, 'error');
                    return;
                }
                
                // Chercher tous les inputs file possibles
                const fileInputs = document.querySelectorAll('input[type="file"]');
                let fileInput = null;
                
                // Trouver le bon input (celui qui accepte nos types de fichiers)
                for (let input of fileInputs) {
                    const accept = input.getAttribute('accept');
                    if (accept && accept.includes(fileExt)) {
                        fileInput = input;
                        break;
                    }
                }
                
                if (!fileInput) {
                    console.error('No suitable file input found');
                    showNotification('Erreur: impossible de trouver l\'input file', 'error');
                    return;
                }
                
                // Créer un nouveau FileList avec le fichier
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                fileInput.files = dataTransfer.files;
                
                // Déclencher l'événement change
                const event = new Event('change', { bubbles: true });
                fileInput.dispatchEvent(event);
                
                // Déclencher aussi un input event pour Streamlit
                const inputEvent = new Event('input', { bubbles: true });
                fileInput.dispatchEvent(inputEvent);
                
                // Notification de succès
                showNotification('Fichier ajouté: ' + file.name, 'success');
            }
            
            function showNotification(message, type = 'success') {
                const notification = document.createElement('div');
                const bgColor = type === 'success' ? '#0055A4' : '#dc3545';
                
                notification.style.cssText = `
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    background: ${bgColor};
                    color: white;
                    padding: 1rem 1.5rem;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    z-index: 10000;
                    font-size: 1rem;
                    animation: slideIn 0.3s ease-out;
                    max-width: 300px;
                `;
                notification.textContent = message;
                document.body.appendChild(notification);
                
                setTimeout(() => {
                    notification.style.animation = 'fadeOut 0.3s ease-out';
                    setTimeout(() => notification.remove(), 300);
                }, 3000);
            }
            
            // CSS pour les animations
            if (!document.getElementById('drag-drop-styles')) {
                const style = document.createElement('style');
                style.id = 'drag-drop-styles';
                style.textContent = `
                    @keyframes slideIn {
                        from { transform: translateX(100%); opacity: 0; }
                        to { transform: translateX(0); opacity: 1; }
                    }
                    @keyframes fadeOut {
                        from { opacity: 1; }
                        to { opacity: 0; }
                    }
                    
                    /* S'assurer que l'overlay est au-dessus de tout */
                    #drop-overlay {
                        pointer-events: all !important;
                    }
                `;
                document.head.appendChild(style);
            }
            
            // Fonction pour le scroll automatique
            function autoScroll() {
                const containers = document.querySelectorAll('[data-testid="stVerticalBlock"]');
                containers.forEach(container => {
                    if (container.style.height === '500px' || 
                        window.getComputedStyle(container).height === '500px') {
                        container.scrollTop = container.scrollHeight;
                    }
                });
            }
            
            // Initialiser après un court délai pour s'assurer que le DOM est prêt
            setTimeout(initDragDrop, 100);
            
            // Réessayer périodiquement au cas où le DOM change
            setInterval(function() {
                if (!initialized || !document.getElementById('drop-overlay')) {
                    initialized = false;
                    initDragDrop();
                }
            }, 1000);
            
            // Auto-scroll
            setInterval(autoScroll, 1000);
        })();
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