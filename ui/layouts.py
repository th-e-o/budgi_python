# ui/layouts.py - Version avec Drag & Drop corrigé et logo
import streamlit as st
from typing import Dict, Any, Callable
from datetime import datetime
from .components.chat import ChatComponents
from .components.sidebar import SidebarComponents
from .components.inputs import InputComponents
import base64
from pathlib import Path

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
    
    def _get_logo_base64(self):
        """Convertit le logo en base64 pour l'intégrer dans le HTML"""
        logo_path = Path("logo.png")
        if logo_path.exists():
            with open(logo_path, "rb") as f:
                logo_bytes = f.read()
                return base64.b64encode(logo_bytes).decode()
        return None
    
    def _render_main_chat(self, on_message_send: Callable, on_file_upload: Callable):
        """Rend la zone principale du chat avec drag & drop"""
        
        # Zone de drop overlay AVANT tout le reste avec un z-index très élevé
        st.markdown("""
        <div id="drop-zone-overlay" style="
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 85, 164, 0.95);
            z-index: 999999;
            pointer-events: all;
            backdrop-filter: blur(4px);
        ">
            <div style="
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: white;
                padding: 4rem;
                border-radius: 24px;
                box-shadow: 0 20px 50px rgba(0,0,0,0.3);
                text-align: center;
                border: 4px dashed #0055A4;
                animation: pulse 2s infinite;
            ">
                <div style="font-size: 5rem; margin-bottom: 1.5rem;">📁</div>
                <div style="font-size: 2.5rem; color: #0055A4; font-weight: bold; margin-bottom: 1rem;">
                    Déposez votre fichier ici
                </div>
                <div style="color: #666; font-size: 1.2rem;">
                    Formats supportés : PDF, DOCX, TXT, MSG, XLSX, JSON
                </div>
            </div>
        </div>
        
        <style>
            @keyframes pulse {
                0% { transform: translate(-50%, -50%) scale(1); }
                50% { transform: translate(-50%, -50%) scale(1.05); }
                100% { transform: translate(-50%, -50%) scale(1); }
            }
            
            /* S'assurer que l'overlay est vraiment au-dessus de tout */
            #drop-zone-overlay {
                pointer-events: all !important;
            }
            
            /* Zone de drop invisible sur toute la page */
            .drop-zone-area {
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                z-index: 1;
                pointer-events: none;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Zone de drop invisible sur toute la page
        st.markdown('<div class="drop-zone-area" id="main-drop-zone"></div>', unsafe_allow_html=True)
        
        # Header avec logo
        logo_base64 = self._get_logo_base64()
        header_html = self.chat_components.render_header()
        
        if logo_base64:
            # Remplacer l'emoji robot par le logo avec un style amélioré
            header_html = header_html.replace(
                '<div class="bot-avatar">🤖</div>',
                f'''<div class="bot-avatar" style="
                    padding: 0;
                    background: transparent;
                    box-shadow: none;
                    overflow: hidden;
                ">
                    <img src="data:image/png;base64,{logo_base64}" 
                         style="width: 50px; height: 50px; object-fit: cover; border-radius: 50%;"
                         alt="BudgiBot">
                </div>'''
            )
        
        st.markdown(header_html, unsafe_allow_html=True)
        
        # Container pour les messages avec scroll automatique
        messages_container = st.container(height=500)
        
        with messages_container:
            self._render_messages_area(on_message_send)
            
            # Placeholder pour forcer le scroll
            scroll_anchor = st.empty()
            with scroll_anchor:
                st.markdown('<div id="chat-bottom-anchor" style="height: 1px;"></div>', unsafe_allow_html=True)
        
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
                key="file_upload_drop",
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
        
        # JavaScript amélioré pour drag & drop - Version complètement refaite
        st.markdown("""
        <script>
        // Drag and Drop Handler v2
        (function() {
            let dragCounter = 0;
            let dropOverlay = null;
            let fileInput = null;
            let isInitialized = false;
            
            function initDragDrop() {
                if (isInitialized) return;
                
                console.log('🚀 Initializing drag and drop v2...');
                
                // Trouver l'overlay
                dropOverlay = document.getElementById('drop-zone-overlay');
                if (!dropOverlay) {
                    console.error('Drop overlay not found, retrying...');
                    setTimeout(initDragDrop, 500);
                    return;
                }
                
                // Trouver l'input file
                const inputs = document.querySelectorAll('input[type="file"]');
                for (let input of inputs) {
                    if (input.accept && input.accept.includes('.pdf')) {
                        fileInput = input;
                        break;
                    }
                }
                
                if (!fileInput) {
                    console.error('File input not found, retrying...');
                    setTimeout(initDragDrop, 500);
                    return;
                }
                
                console.log('✅ Drop overlay and file input found');
                isInitialized = true;
                
                // Prévenir le comportement par défaut du navigateur
                ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                    document.body.addEventListener(eventName, preventDefaults, false);
                    window.addEventListener(eventName, preventDefaults, false);
                });
                
                // Événements de drag sur le document entier
                document.body.addEventListener('dragenter', handleDragEnter, false);
                document.body.addEventListener('dragover', handleDragOver, false);
                document.body.addEventListener('dragleave', handleDragLeave, false);
                document.body.addEventListener('drop', handleDrop, false);
                
                // Événements sur l'overlay aussi
                dropOverlay.addEventListener('dragenter', preventDefaults, false);
                dropOverlay.addEventListener('dragover', preventDefaults, false);
                dropOverlay.addEventListener('dragleave', preventDefaults, false);
                dropOverlay.addEventListener('drop', handleDrop, false);
                
                console.log('✅ Drag and drop fully initialized');
            }
            
            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            function handleDragEnter(e) {
                preventDefaults(e);
                
                // Vérifier si c'est un fichier qui est dragué
                if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
                    const item = e.dataTransfer.items[0];
                    if (item.kind === 'file') {
                        dragCounter++;
                        console.log('📥 Drag enter, counter:', dragCounter);
                        
                        if (dragCounter === 1) {
                            showDropOverlay();
                        }
                    }
                }
            }
            
            function handleDragOver(e) {
                preventDefaults(e);
                e.dataTransfer.dropEffect = 'copy';
            }
            
            function handleDragLeave(e) {
                preventDefaults(e);
                dragCounter--;
                console.log('📤 Drag leave, counter:', dragCounter);
                
                if (dragCounter <= 0) {
                    dragCounter = 0;
                    hideDropOverlay();
                }
            }
            
            function handleDrop(e) {
                preventDefaults(e);
                console.log('📦 File dropped!');
                
                dragCounter = 0;
                hideDropOverlay();
                
                const files = e.dataTransfer.files;
                if (files && files.length > 0) {
                    handleFileDrop(files[0]);
                }
            }
            
            function showDropOverlay() {
                if (dropOverlay) {
                    console.log('👁️ Showing drop overlay');
                    dropOverlay.style.display = 'block';
                    dropOverlay.style.opacity = '0';
                    setTimeout(() => {
                        dropOverlay.style.transition = 'opacity 0.3s ease';
                        dropOverlay.style.opacity = '1';
                    }, 10);
                }
            }
            
            function hideDropOverlay() {
                if (dropOverlay) {
                    console.log('🙈 Hiding drop overlay');
                    dropOverlay.style.opacity = '0';
                    setTimeout(() => {
                        dropOverlay.style.display = 'none';
                    }, 300);
                }
            }
            
            function handleFileDrop(file) {
                console.log('📎 Processing file:', file.name, 'Type:', file.type);
                
                // Vérifier le type de fichier - accepter tous les types supportés
                const allowedExtensions = ['.pdf', '.docx', '.txt', '.msg', '.xlsx', '.json'];
                const fileName = file.name.toLowerCase();
                let fileExt = '';
                
                // Trouver l'extension qui correspond
                for (let ext of allowedExtensions) {
                    if (fileName.endsWith(ext)) {
                        fileExt = ext;
                        break;
                    }
                }
                
                // Si pas d'extension trouvée, essayer avec le dernier point
                if (!fileExt) {
                    const lastDot = fileName.lastIndexOf('.');
                    if (lastDot > -1) {
                        fileExt = fileName.substring(lastDot);
                    }
                }
                
                if (!fileExt || !allowedExtensions.includes(fileExt)) {
                    showNotification('❌ Type de fichier non supporté: ' + (fileExt || 'inconnu'), 'error');
                    return;
                }
                
                if (!fileInput) {
                    showNotification('❌ Erreur: input file non trouvé', 'error');
                    return;
                }
                
                // Créer un nouveau FileList
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                fileInput.files = dataTransfer.files;
                
                // Déclencher l'événement change
                const changeEvent = new Event('change', { bubbles: true });
                fileInput.dispatchEvent(changeEvent);
                
                // Forcer une mise à jour Streamlit
                const inputEvent = new InputEvent('input', { bubbles: true });
                fileInput.dispatchEvent(inputEvent);
                
                // Cliquer sur l'input pour forcer Streamlit à détecter
                fileInput.click();
                
                showNotification('✅ Fichier ajouté: ' + file.name, 'success');
            }
            
            function showNotification(message, type = 'success') {
                const notification = document.createElement('div');
                const bgColor = type === 'success' ? '#0055A4' : '#EF4135';
                
                notification.innerHTML = `
                    <div style="
                        position: fixed;
                        bottom: 30px;
                        right: 30px;
                        background: ${bgColor};
                        color: white;
                        padding: 1.2rem 1.8rem;
                        border-radius: 12px;
                        box-shadow: 0 8px 24px rgba(0,0,0,0.2);
                        z-index: 1000000;
                        font-size: 1.1rem;
                        font-weight: 500;
                        animation: slideInRight 0.3s ease-out;
                        max-width: 350px;
                        display: flex;
                        align-items: center;
                        gap: 0.8rem;
                    ">
                        <span style="font-size: 1.5rem;">${type === 'success' ? '✅' : '❌'}</span>
                        <span>${message}</span>
                    </div>
                `;
                
                document.body.appendChild(notification);
                
                setTimeout(() => {
                    notification.style.animation = 'slideOutRight 0.3s ease-out';
                    setTimeout(() => notification.remove(), 300);
                }, 3000);
            }
            
            // CSS pour les animations et le scroll
            if (!document.getElementById('drag-drop-styles-v2')) {
                const style = document.createElement('style');
                style.id = 'drag-drop-styles-v2';
                style.textContent = `
                    @keyframes slideInRight {
                        from { transform: translateX(100%); opacity: 0; }
                        to { transform: translateX(0); opacity: 1; }
                    }
                    @keyframes slideOutRight {
                        from { transform: translateX(0); opacity: 1; }
                        to { transform: translateX(100%); opacity: 0; }
                    }
                    
                    /* S'assurer que notre overlay est vraiment au-dessus */
                    #drop-zone-overlay {
                        pointer-events: all !important;
                        position: fixed !important;
                        z-index: 999999 !important;
                    }
                    
                    /* Style pour la zone de drop active */
                    body.drag-active {
                        position: relative;
                    }
                    
                    /* Forcer le scroll du container */
                    [data-testid="stVerticalBlock"] > div[style*="height: 500px"] {
                        scroll-behavior: smooth !important;
                    }
                `;
                document.head.appendChild(style);
            }
            
            // Fonction pour le scroll automatique
            function scrollToBottom() {
                // Chercher le container avec hauteur fixe
                const containers = document.querySelectorAll('[data-testid="stVerticalBlock"] > div');
                containers.forEach(container => {
                    if (container.style.height === '500px' || 
                        window.getComputedStyle(container).height === '500px') {
                        // Scroll to bottom
                        container.scrollTop = container.scrollHeight;
                        console.log('📜 Scrolled to bottom');
                    }
                });
                
                // Alternative: chercher l'ancre
                const anchor = document.getElementById('chat-bottom-anchor');
                if (anchor) {
                    anchor.scrollIntoView({ behavior: 'smooth', block: 'end' });
                }
            }
            
            // Observer pour détecter les nouveaux messages
            const messageObserver = new MutationObserver((mutations) => {
                let hasNewMessage = false;
                mutations.forEach(mutation => {
                    if (mutation.addedNodes.length > 0) {
                        mutation.addedNodes.forEach(node => {
                            if (node.nodeType === 1 && (
                                node.classList?.contains('message-wrapper') ||
                                node.querySelector?.('.message-wrapper')
                            )) {
                                hasNewMessage = true;
                            }
                        });
                    }
                });
                
                if (hasNewMessage) {
                    setTimeout(scrollToBottom, 100);
                }
            });
            
            // Observer le container de messages
            setTimeout(() => {
                const containers = document.querySelectorAll('[data-testid="stVerticalBlock"] > div');
                containers.forEach(container => {
                    if (container.style.height === '500px') {
                        messageObserver.observe(container, {
                            childList: true,
                            subtree: true
                        });
                        console.log('👀 Observing message container for scroll');
                    }
                });
            }, 1000);
            
            // Initialisation avec retry
            setTimeout(initDragDrop, 100);
            
            // Réinitialiser si Streamlit recharge
            const observer = new MutationObserver(() => {
                if (!document.getElementById('drop-zone-overlay') && isInitialized) {
                    console.log('🔄 Reinitializing drag and drop...');
                    isInitialized = false;
                    setTimeout(initDragDrop, 100);
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
            
            // Debug: Log pour vérifier que le script est chargé
            console.log('✨ Drag and drop script loaded');
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
        """Rend la sidebar avec les outils et le logo"""
        # Logo en haut de la sidebar avec style amélioré
        logo_path = Path("logo.png")
        if logo_path.exists():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(str(logo_path), width=120)
            
            # Titre sous le logo
            st.markdown("""
                <div style="text-align: center; margin-bottom: 1rem;">
                    <h2 style="color: #0055A4; margin: 0;">BudgiBot</h2>
                    <p style="color: #666; font-size: 0.9rem; margin: 0;">Assistant Budgétaire</p>
                </div>
            """, unsafe_allow_html=True)
            st.markdown("---")
        
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