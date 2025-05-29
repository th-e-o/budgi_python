# ui/layouts.py - Modern UI with Enhanced Excel Display
import streamlit as st
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from .components.chat import ChatComponents
from .components.sidebar import SidebarComponents
from .components.inputs import InputComponents
import base64
from pathlib import Path
import pandas as pd

class MainLayout:
    """Modern layout with dual-pane design for chat and Excel"""
    
    def __init__(self, services: Dict[str, Any]):
        self.services = services
        self.chat_components = ChatComponents()
        self.sidebar_components = SidebarComponents()
        self.input_components = InputComponents()
    
    def render(self, 
               on_message_send: Callable,
               on_file_upload: Callable,
               on_tool_action: Callable):
        """Renders the complete modern application layout"""
        
        # Initialize layout state
        if 'layout_mode' not in st.session_state:
            st.session_state.layout_mode = 'split'  # 'chat', 'excel', 'split'
        
        # Top navigation bar
        self._render_top_navbar()
        
        # Main content area based on layout mode
        if st.session_state.layout_mode == 'split':
            # Modern split view
            chat_col, excel_col = st.columns([1, 1], gap="medium")
            
            with chat_col:
                self._render_chat_panel(on_message_send, on_file_upload)
            
            with excel_col:
                self._render_excel_panel(on_tool_action)
        
        elif st.session_state.layout_mode == 'chat':
            # Full chat view
            self._render_chat_panel(on_message_send, on_file_upload, full_width=True)
            
        elif st.session_state.layout_mode == 'excel':
            # Full Excel view
            self._render_excel_panel(on_tool_action, full_width=True)
        
        # Floating action buttons
        self._render_floating_actions(on_tool_action)
        
        # Drag and drop overlay
        self._render_drag_drop_overlay()
    
    def _render_top_navbar(self):
        """Renders modern top navigation bar"""
        # Get logo first
        logo_base64 = self._get_logo_base64() or ""
        
        # Build navbar HTML with proper escaping
        navbar_html = f"""
        <div class="top-navbar">
            <div class="navbar-content">
                <div class="navbar-brand">
                    {'<img src="data:image/png;base64,' + logo_base64 + '" class="navbar-logo" alt="BudgiBot">' if logo_base64 else '<div class="navbar-logo-placeholder">🤖</div>'}
                    <span class="navbar-title">BudgiBot</span>
                    <span class="navbar-subtitle">Assistant Budgétaire Intelligent</span>
                </div>
                
                <div class="navbar-controls">
                    <div class="layout-switcher">
                        <button class="layout-btn" data-layout="chat" title="Vue Chat">
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
                            </svg>
                        </button>
                        <button class="layout-btn active" data-layout="split" title="Vue Partagée">
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="3" width="18" height="18" rx="2"></rect>
                                <line x1="12" y1="3" x2="12" y2="21"></line>
                            </svg>
                        </button>
                        <button class="layout-btn" data-layout="excel" title="Vue Excel">
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="3" width="18" height="18" rx="2"></rect>
                                <line x1="3" y1="9" x2="21" y2="9"></line>
                                <line x1="3" y1="15" x2="21" y2="15"></line>
                                <line x1="9" y1="3" x2="9" y2="21"></line>
                                <line x1="15" y1="3" x2="15" y2="21"></line>
                            </svg>
                        </button>
                    </div>
                    
                    <div class="navbar-actions">
                        <button class="nav-action-btn" id="notifications-btn">
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                                <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                            </svg>
                            <span class="notification-badge">2</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
        """
        
        st.markdown(navbar_html, unsafe_allow_html=True)
        
        # JavaScript for layout switching
        st.markdown("""
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            const layoutBtns = document.querySelectorAll('.layout-btn');
            layoutBtns.forEach(btn => {
                btn.addEventListener('click', function() {
                    const layout = this.dataset.layout;
                    // Remove active class from all buttons
                    layoutBtns.forEach(b => b.classList.remove('active'));
                    this.classList.add('active');
                    
                    // Update Streamlit state
                    const layoutInput = document.querySelector('input[aria-label="layout_mode_input"]');
                    if (layoutInput) {
                        layoutInput.value = layout;
                        layoutInput.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                });
            });
        });
        </script>
        """, unsafe_allow_html=True)
        
        # Hidden input for layout mode
        layout_mode = st.text_input("layout_mode_input", value=st.session_state.layout_mode, 
                                   key="layout_mode_input", label_visibility="hidden")
        if layout_mode != st.session_state.layout_mode:
            st.session_state.layout_mode = layout_mode
            st.rerun()
    
    def _render_chat_panel(self, on_message_send: Callable, on_file_upload: Callable, 
                          full_width: bool = False):
        """Renders modern chat panel"""
        panel_class = "chat-panel-full" if full_width else "chat-panel"
        
        st.markdown(f'<div class="{panel_class}">', unsafe_allow_html=True)
        
        # Chat header
        self._render_chat_header()
        
        # Messages container with enhanced scrolling
        messages_container = st.container(height=600 if full_width else 500)
        with messages_container:
            self._render_messages_area(on_message_send)
        
        # Modern input area
        self._render_chat_input(on_message_send, on_file_upload)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_excel_panel(self, on_tool_action: Callable, full_width: bool = False):
        """Renders modern Excel panel with enhanced visualization"""
        panel_class = "excel-panel-full" if full_width else "excel-panel"
        
        st.markdown(f'<div class="{panel_class}">', unsafe_allow_html=True)
        
        # Excel header with tabs
        st.markdown("""
        <div class="excel-header">
            <h3>📊 Espace Excel</h3>
            <div class="excel-tabs">
                <button class="excel-tab active" data-tab="data">Données</button>
                <button class="excel-tab" data-tab="formulas">Formules</button>
                <button class="excel-tab" data-tab="analysis">Analyse</button>
                <button class="excel-tab" data-tab="tools">Outils</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Tab content
        if 'excel_tab' not in st.session_state:
            st.session_state.excel_tab = 'data'
        
        if st.session_state.excel_tab == 'data':
            self._render_excel_data_tab()
        elif st.session_state.excel_tab == 'formulas':
            self._render_excel_formulas_tab(on_tool_action)
        elif st.session_state.excel_tab == 'analysis':
            self._render_excel_analysis_tab(on_tool_action)
        elif st.session_state.excel_tab == 'tools':
            self._render_excel_tools_tab(on_tool_action)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Tab switching JavaScript
        st.markdown("""
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            const tabs = document.querySelectorAll('.excel-tab');
            tabs.forEach(tab => {
                tab.addEventListener('click', function() {
                    tabs.forEach(t => t.classList.remove('active'));
                    this.classList.add('active');
                    
                    const tabName = this.dataset.tab;
                    const tabInput = document.querySelector('input[aria-label="excel_tab_input"]');
                    if (tabInput) {
                        tabInput.value = tabName;
                        tabInput.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                });
            });
        });
        </script>
        """, unsafe_allow_html=True)
        
        # Hidden input for tab state
        excel_tab = st.text_input("excel_tab_input", value=st.session_state.excel_tab,
                                 key="excel_tab_input", label_visibility="hidden")
        if excel_tab != st.session_state.excel_tab:
            st.session_state.excel_tab = excel_tab
            st.rerun()
    
    def _render_excel_data_tab(self):
        """Renders Excel data visualization tab"""
        if not st.session_state.get('excel_workbook'):
            # Upload area
            st.markdown("""
            <div class="excel-upload-area">
                <div class="upload-icon">📂</div>
                <h4>Glissez un fichier Excel ici</h4>
                <p>ou cliquez pour parcourir</p>
            </div>
            """, unsafe_allow_html=True)
            
            uploaded = st.file_uploader(
                "Upload Excel", 
                type=['xlsx'],
                key="excel_upload_main",
                label_visibility="hidden"
            )
            
            if uploaded:
                try:
                    wb = self.services['excel_handler'].load_workbook_from_bytes(uploaded.getbuffer())
                    st.session_state.excel_workbook = wb
                    st.session_state.current_file = {
                        'name': uploaded.name,
                        'content': uploaded.getbuffer(),
                        'raw_bytes': uploaded.getbuffer()
                    }
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur: {str(e)}")
        else:
            # Sheet selector with modern design
            wb = st.session_state.excel_workbook
            sheets = wb.sheetnames
            
            col1, col2 = st.columns([3, 1])
            with col1:
                selected_sheet = st.selectbox(
                    "Feuille",
                    sheets,
                    key="sheet_selector_main",
                    label_visibility="hidden"
                )
            
            with col2:
                st.download_button(
                    "💾 Exporter",
                    data=self.services['excel_handler'].save_workbook_to_bytes(wb),
                    file_name=f"budgibot_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            # Display data with enhanced styling
            if selected_sheet:
                try:
                    df = self.services['excel_handler'].sheet_to_dataframe(wb, selected_sheet)
                    
                    # Info bar
                    st.markdown(f"""
                    <div class="excel-info-bar">
                        <span>📊 {len(df)} lignes × {len(df.columns)} colonnes</span>
                        <span>📄 Feuille: {selected_sheet}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Enhanced data editor
                    edited_df = st.data_editor(
                        df,
                        use_container_width=True,
                        height=400,
                        num_rows="dynamic",
                        key=f"excel_editor_{selected_sheet}"
                    )
                    
                    # Save changes button
                    if st.button("💾 Sauvegarder les modifications", type="primary", use_container_width=True):
                        self.services['excel_handler'].dataframe_to_sheet(
                            edited_df, wb, selected_sheet
                        )
                        st.success("✅ Modifications sauvegardées!")
                        
                except Exception as e:
                    st.error(f"Erreur affichage: {str(e)}")
    
    def _render_excel_formulas_tab(self, on_tool_action: Callable):
        """Renders Excel formulas tab"""
        if not st.session_state.get('excel_workbook'):
            st.info("📂 Chargez d'abord un fichier Excel dans l'onglet Données")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔍 Analyser les formules", use_container_width=True, type="primary"):
                on_tool_action({'action': 'parse_excel'})
        
        with col2:
            if st.button("🔧 Appliquer les formules", use_container_width=True):
                on_tool_action({'action': 'apply_formulas'})
        
        # Display parsed formulas
        if st.session_state.get('parsed_formulas'):
            result = st.session_state.parsed_formulas
            stats = result['statistics']
            
            # Statistics cards
            st.markdown(f"""
            <div class="stats-cards">
                <div class="stat-card">
                    <div class="stat-value">{stats['total']}</div>
                    <div class="stat-label">Formules totales</div>
                </div>
                <div class="stat-card success">
                    <div class="stat-value">{stats['success']}</div>
                    <div class="stat-label">Converties</div>
                </div>
                <div class="stat-card error">
                    <div class="stat-value">{stats['errors']}</div>
                    <div class="stat-label">Erreurs</div>
                </div>
                <div class="stat-card info">
                    <div class="stat-value">{stats['success_rate']}%</div>
                    <div class="stat-label">Taux de succès</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Formula list
            if result['formulas']:
                st.markdown("### 📝 Formules converties")
                for i, formula in enumerate(result['formulas'][:20]):
                    if formula.r_code and not formula.r_code.startswith('#'):
                        with st.expander(f"{formula.sheet}!{formula.address}: {formula.formula[:50]}..."):
                            st.code(formula.r_code, language='python')
    
    def _render_excel_analysis_tab(self, on_tool_action: Callable):
        """Renders Excel analysis tab"""
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Extraire données budgétaires", use_container_width=True, type="primary"):
                on_tool_action({'action': 'extract_budget'})
        
        with col2:
            if st.button("🎯 Mapper aux cellules", use_container_width=True):
                if st.session_state.get('extracted_data') and st.session_state.get('json_data'):
                    on_tool_action({'action': 'map_budget_cells'})
                else:
                    st.warning("Extrayez d'abord les données et chargez un JSON")
        
        # Display extracted data
        if st.session_state.get('extracted_data'):
            st.markdown("### 💰 Données budgétaires extraites")
            
            df = pd.DataFrame(st.session_state.extracted_data)
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="dynamic",
                height=300
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Sauvegarder", use_container_width=True):
                    st.session_state.extracted_data = edited_df.to_dict('records')
                    st.success("Données sauvegardées!")
            
            with col2:
                csv = edited_df.to_csv(index=False)
                st.download_button(
                    "📥 Exporter CSV",
                    data=csv,
                    file_name=f"budget_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    
    def _render_excel_tools_tab(self, on_tool_action: Callable):
        """Renders Excel tools tab"""
        # BPSS Tool
        st.markdown("### 🛠️ Outil BPSS")
        with st.form("bpss_form_excel"):
            col1, col2, col3 = st.columns(3)
            with col1:
                year = st.number_input("Année", value=2025, min_value=2000, max_value=2100)
            with col2:
                ministry = st.text_input("Code Ministère", value="38")
            with col3:
                program = st.text_input("Code Programme", value="150")
            
            st.markdown("#### 📁 Fichiers requis")
            col1, col2, col3 = st.columns(3)
            with col1:
                ppes = st.file_uploader("PP‑E‑S", type=['xlsx'], key="bpss_ppes_excel")
            with col2:
                dpp18 = st.file_uploader("DPP 18", type=['xlsx'], key="bpss_dpp18_excel")
            with col3:
                bud45 = st.file_uploader("BUD 45", type=['xlsx'], key="bpss_bud45_excel")
            
            if st.form_submit_button("🚀 Lancer BPSS", use_container_width=True, type="primary"):
                if all([ppes, dpp18, bud45]):
                    on_tool_action({
                        'action': 'process_bpss',
                        'data': {
                            'year': year,
                            'ministry': ministry,
                            'program': program,
                            'files': {
                                'ppes': ppes,
                                'dpp18': dpp18,
                                'bud45': bud45
                            }
                        }
                    })
                else:
                    st.error("Veuillez charger tous les fichiers requis")
        
        # JSON Helper
        st.markdown("### 📄 Configuration JSON")
        json_file = st.file_uploader("Charger JSON", type=['json'], key="json_excel")
        if json_file:
            import json
            try:
                data = json.load(json_file)
                st.session_state.json_data = data
                
                labels = self.services['json_helper'].extract_labels(data)
                st.success(f"✅ {len(labels)} labels trouvés")
                
                if st.button("🔍 Analyser labels", use_container_width=True):
                    on_tool_action({'action': 'analyze_labels', 'data': data})
                    
            except Exception as e:
                st.error(f"Erreur JSON: {str(e)}")
    
    def _render_chat_header(self):
        """Renders modern chat header"""
        logo_base64 = self._get_logo_base64()
        header_html = """
        <div class="modern-chat-header">
            <div class="chat-header-content">
                <img src="data:image/png;base64,{logo}" class="chat-logo" alt="BudgiBot">
                <div class="chat-header-info">
                    <h3>Assistant BudgiBot</h3>
                    <span class="chat-status">
                        <span class="status-indicator"></span>
                        En ligne • Prêt à vous aider
                    </span>
                </div>
            </div>
            <div class="chat-header-actions">
                <button class="header-action-btn" title="Historique">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <polyline points="12 6 12 12 16 14"/>
                    </svg>
                </button>
                <button class="header-action-btn" title="Paramètres">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="3"/>
                        <path d="M12 1v6m0 6v6m9-9h-6m-6 0H3"/>
                    </svg>
                </button>
            </div>
        </div>
        """
        st.markdown(header_html.format(logo=logo_base64 or ""), unsafe_allow_html=True)
    
    def _render_chat_input(self, on_message_send: Callable, on_file_upload: Callable):
        """Renders modern chat input area"""
        st.markdown('<div class="modern-chat-input">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 8, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "📎",
                type=['pdf', 'docx', 'txt', 'msg', 'xlsx', 'json'],
                key="file_upload_chat_modern",
                label_visibility="collapsed",
                help="Joindre un fichier"
            )
        
        with col2:
            prompt = st.chat_input(
                "Tapez votre message...",
                key="chat_input_modern",
                max_chars=2000
            )
        
        with col3:
            # Voice input button (placeholder)
            st.markdown("""
            <button class="voice-input-btn" title="Entrée vocale">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                    <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                    <line x1="12" y1="19" x2="12" y2="23"/>
                    <line x1="8" y1="23" x2="16" y2="23"/>
                </svg>
            </button>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Handle inputs
        if prompt:
            on_message_send(prompt)
        
        if uploaded_file:
            if 'last_uploaded_file' not in st.session_state or \
               st.session_state.last_uploaded_file != uploaded_file.name:
                st.session_state.last_uploaded_file = uploaded_file.name
                on_file_upload(uploaded_file)
    
    def _render_floating_actions(self, on_tool_action: Callable):
        """Renders floating action buttons"""
        st.markdown("""
        <div class="floating-actions">
            <button class="fab fab-primary" id="quick-extract" title="Extraction rapide">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                    <line x1="16" y1="13" x2="8" y2="13"/>
                    <line x1="16" y1="17" x2="8" y2="17"/>
                    <polyline points="10 9 9 9 8 9"/>
                </svg>
            </button>
            <button class="fab fab-secondary" id="new-chat" title="Nouvelle conversation">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="12" y1="5" x2="12" y2="19"/>
                    <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
            </button>
        </div>
        
        <script>
        document.addEventListener('DOMContentLoaded', function() {
            document.getElementById('quick-extract')?.addEventListener('click', function() {
                // Trigger extract budget action
                const btn = document.querySelector('button:contains("Extraire données budgétaires")');
                if (btn) btn.click();
            });
            
            document.getElementById('new-chat')?.addEventListener('click', function() {
                // Clear chat history
                if (confirm('Commencer une nouvelle conversation ?')) {
                    window.location.reload();
                }
            });
        });
        </script>
        """, unsafe_allow_html=True)
    
    def _render_drag_drop_overlay(self):
        """Renders modern drag and drop overlay"""
        st.markdown("""
        <div id="drop-overlay" class="drop-overlay">
            <div class="drop-content">
                <div class="drop-icon">
                    <svg width="100" height="100" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                        <path d="M7 18a4.6 4.4 0 0 1 0-9 5 4.65 0 0 1 11.03.1h.57a3.4 3.4 0 0 1 .1 6.8"/>
                        <polyline points="12 13 12 21"/>
                        <polyline points="9 18 12 21 15 18"/>
                    </svg>
                </div>
                <h2>Déposez votre fichier ici</h2>
                <p>PDF, DOCX, XLSX, JSON, TXT, MSG</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_messages_area(self, on_message_send: Callable):
        """Renders messages area with modern styling"""
        for i, msg in enumerate(st.session_state.get('chat_history', [])):
            if msg.get('meta') == 'file_content':
                continue
            
            html, needs_buttons = self.chat_components.render_message(msg, i)
            st.markdown(html, unsafe_allow_html=True)
            
            # Quick replies
            if msg['role'] == 'assistant' and not needs_buttons:
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
        
        # Typing indicator
        if st.session_state.get('is_typing', False):
            st.markdown(self.chat_components.render_typing_indicator(), unsafe_allow_html=True)
    
    def _get_logo_base64(self) -> Optional[str]:
        """Converts logo to base64"""
        logo_path = Path("logo.png")
        if logo_path.exists():
            with open(logo_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        return None