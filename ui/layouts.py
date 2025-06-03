# ui/layouts.py - Simplified and Modern UI
import streamlit as st
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from .components.chat import ChatComponents
from .components.inputs import InputComponents
import base64
from pathlib import Path
import pandas as pd

class MainLayout:
    """Modern simplified layout focused on chat and Excel functionality"""
    
    def __init__(self, services: Dict[str, Any]):
        self.services = services
        self.chat_components = ChatComponents()
        self.input_components = InputComponents()
    
    def render(self, 
               on_message_send: Callable,
               on_file_upload: Callable,
               on_tool_action: Callable):
        """Renders the complete modern application layout"""
        
        # Initialize layout state
        if 'layout_mode' not in st.session_state:
            st.session_state.layout_mode = 'chat'  # Start with chat view
        
        # Top navigation bar
        self._render_top_navbar()
        
        # Reduce vertical spacing
        st.markdown("<div style='margin-top: -2rem;'></div>", unsafe_allow_html=True)
        
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
        
        # Drag and drop overlay
        self._render_drag_drop_overlay()
    
    def _render_top_navbar(self):
        """Renders simplified top navigation bar"""
        # Get current layout mode for active state
        current_layout = st.session_state.get('layout_mode', 'chat')
        
        # Create columns for navbar
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 0.75rem; height: 56px;">
                <div style="width: 36px; height: 36px; border-radius: 8px; background: #0055A4; color: white; display: flex; align-items: center; justify-content: center; font-size: 1.25rem;">🤖</div>
                <span style="font-size: 1.25rem; font-weight: 600; color: #1e293b;">BudgiBot</span>
                <span style="font-size: 0.875rem; color: #64748b;">Assistant Budgétaire</span>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Use Streamlit native buttons in columns
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            
            with btn_col1:
                if st.button("💬", key="nav_chat", help="Chat", 
                           type="primary" if current_layout == 'chat' else "secondary"):
                    st.session_state.layout_mode = 'chat'
                    st.rerun()
            
            with btn_col2:
                if st.button("⚡", key="nav_split", help="Vue partagée",
                           type="primary" if current_layout == 'split' else "secondary"):
                    st.session_state.layout_mode = 'split'
                    st.rerun()
            
            with btn_col3:
                if st.button("📊", key="nav_excel", help="Excel",
                           type="primary" if current_layout == 'excel' else "secondary"):
                    st.session_state.layout_mode = 'excel'
                    st.rerun()
        
        # Add a separator line
        st.markdown("<hr style='margin: 0; border: none; border-bottom: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
    
    def _render_chat_panel(self, on_message_send: Callable, on_file_upload: Callable, 
                          full_width: bool = False):
        """Renders modern chat panel"""
        panel_class = "chat-panel-full" if full_width else "chat-panel"
        
        st.markdown(f'<div class="{panel_class}">', unsafe_allow_html=True)
        
        # Chat header
        st.markdown(self.chat_components.render_header(), unsafe_allow_html=True)
        
        # Messages container
        messages_container = st.container(height=600 if full_width else 500)
        with messages_container:
            # Always render messages area (welcome is now a regular message)
            self._render_messages_area(on_message_send)
        
        # Modern input area
        self._render_chat_input(on_message_send, on_file_upload)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_excel_panel(self, on_tool_action: Callable, full_width: bool = False):
        """Renders simplified Excel panel"""
        panel_class = "excel-panel-full" if full_width else "excel-panel"
        
        st.markdown(f'<div class="{panel_class}">', unsafe_allow_html=True)
        
        # Simplified Excel header with fewer tabs
        active_tab = st.session_state.get('excel_tab', 'data')
        st.markdown(f"""
        <div class="excel-header">
            <h3>📊 Espace Excel</h3>
            <div class="excel-tabs">
                <button class="excel-tab {'active' if active_tab == 'data' else ''}" 
                        onclick="window.setExcelTab('data')">Données</button>
                <button class="excel-tab {'active' if active_tab == 'analysis' else ''}" 
                        onclick="window.setExcelTab('analysis')">Extraction</button>
                <button class="excel-tab {'active' if active_tab == 'tools' else ''}" 
                        onclick="window.setExcelTab('tools')">BPSS</button>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Tab content
        if active_tab == 'data':
            self._render_excel_data_tab()
        elif active_tab == 'analysis':
            self._render_excel_analysis_tab(on_tool_action)
        elif active_tab == 'tools':
            self._render_excel_tools_tab(on_tool_action)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Tab switching JavaScript
        st.markdown("""
        <script>
        window.setExcelTab = function(tab) {
            const inputs = window.parent.document.querySelectorAll('input');
            for (let input of inputs) {
                if (input.getAttribute('aria-label') === 'excel_tab_input') {
                    input.value = tab;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    break;
                }
            }
        };
        </script>
        """, unsafe_allow_html=True)
        
        # Hidden input for tab state
        new_tab = st.text_input("excel_tab_input", value=active_tab,
                               key="excel_tab_input", label_visibility="hidden")
        if new_tab != active_tab:
            st.session_state.excel_tab = new_tab
            st.rerun()
    
    def _render_excel_data_tab(self):
        """Renders Excel data visualization tab - simplified"""
        if not st.session_state.get('excel_workbook'):
            # Clean upload area
            uploaded = st.file_uploader(
                "📂 Charger un fichier Excel",
                type=['xlsx'],
                key="excel_upload_main",
                help="Glissez-déposez ou cliquez pour parcourir"
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
            # Sheet management
            wb = st.session_state.excel_workbook
            sheets = wb.sheetnames
            
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                selected_sheet = st.selectbox(
                    "Sélectionner une feuille",
                    sheets,
                    key="sheet_selector_main"
                )
            
            with col2:
                if st.button("📊 Parser", help="Analyser les formules"):
                    with st.spinner("Analyse en cours..."):
                        self._handle_parse_formulas()
            
            with col3:
                st.download_button(
                    "💾",
                    data=self.services['excel_handler'].save_workbook_to_bytes(wb),
                    file_name=f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Exporter le fichier"
                )
            
            # Display data
            if selected_sheet:
                try:
                    df = self.services['excel_handler'].sheet_to_dataframe(wb, selected_sheet)
                    
                    # Simple info
                    st.caption(f"📊 {len(df)} lignes × {len(df.columns)} colonnes")
                    
                    # Data editor
                    edited_df = st.data_editor(
                        df,
                        use_container_width=True,
                        height=400,
                        num_rows="dynamic",
                        key=f"excel_editor_{selected_sheet}"
                    )
                    
                    # Save button only if changes detected
                    if not df.equals(edited_df):
                        if st.button("💾 Sauvegarder les modifications", type="primary", use_container_width=True):
                            self.services['excel_handler'].dataframe_to_sheet(
                                edited_df, wb, selected_sheet
                            )
                            st.success("✅ Modifications sauvegardées!")
                            st.rerun()
                        
                except Exception as e:
                    st.error(f"Erreur affichage: {str(e)}")
    
    def _render_excel_analysis_tab(self, on_tool_action: Callable):
        """Renders simplified analysis tab"""
        # Check prerequisites
        if not st.session_state.get('current_file'):
            st.info("📂 Chargez d'abord un fichier dans l'onglet Données ou via le chat")
            return
        
        # JSON configuration for mapping
        json_file = st.file_uploader(
            "📄 Configuration JSON pour mapping automatique (optionnel)", 
            type=['json'], 
            key="json_analysis",
            help="Permet de mapper automatiquement les données extraites vers les cellules Excel"
        )
        
        if json_file:
            import json
            try:
                data = json.load(json_file)
                st.session_state.json_data = data
                tags_count = len(data.get('tags', []))
                st.success(f"✅ Configuration JSON chargée ({tags_count} cellules cibles)")
            except Exception as e:
                st.error(f"Erreur JSON: {str(e)}")
        
        # Main extraction button
        st.markdown("---")
        
        if st.button("🎯 Extraire les données budgétaires", 
                    type="primary", 
                    use_container_width=True,
                    disabled=not st.session_state.get('current_file')):
            on_tool_action({'action': 'extract_budget'})
        
        # Display extracted data if available
        if st.session_state.get('extracted_data'):
            st.markdown("### 💰 Données extraites")
            
            df = pd.DataFrame(st.session_state.extracted_data)
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Entrées", len(df))
            with col2:
                total = df['Montant'].sum() if 'Montant' in df.columns else 0
                st.metric("Total", f"{total:,.0f} €")
            with col3:
                axes = df['Axe'].nunique() if 'Axe' in df.columns else 0
                st.metric("Axes", axes)
            
            # Editable data
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="dynamic",
                height=300,
                key="budget_data_editor"
            )
            
            # Action buttons
            col1, col2 = st.columns(2)
            with col1:
                csv = edited_df.to_csv(index=False)
                st.download_button(
                    "📥 Exporter CSV",
                    data=csv,
                    file_name=f"budget_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col2:
                if st.session_state.get('json_data') and st.session_state.get('excel_workbook'):
                    if st.button("🎯 Mapper vers Excel", use_container_width=True, type="secondary"):
                        on_tool_action({'action': 'map_budget_cells'})
                        
            # Save changes if modified
            if not df.equals(edited_df):
                if st.button("💾 Sauvegarder les modifications", use_container_width=True):
                    st.session_state.extracted_data = edited_df.to_dict('records')
                    st.success("✅ Données mises à jour!")
    
    def _render_excel_tools_tab(self, on_tool_action: Callable):
        """Renders simplified BPSS tool"""
        st.markdown("### 🛠️ Outil BPSS")
        st.caption("Traitement automatique des fichiers budgétaires (PP-E-S, DPP18, BUD45)")
        
        with st.form("bpss_form_excel"):
            col1, col2, col3 = st.columns(3)
            with col1:
                year = st.number_input("Année", value=2025, min_value=2020, max_value=2030)
            with col2:
                ministry = st.text_input("Ministère", value="38")
            with col3:
                program = st.text_input("Programme", value="150")
            
            st.markdown("#### 📁 Fichiers requis")
            col1, col2, col3 = st.columns(3)
            with col1:
                ppes = st.file_uploader("PP‑E‑S", type=['xlsx'], key="bpss_ppes_excel")
            with col2:
                dpp18 = st.file_uploader("DPP18", type=['xlsx'], key="bpss_dpp18_excel")
            with col3:
                bud45 = st.file_uploader("BUD45", type=['xlsx'], key="bpss_bud45_excel")
            
            # Visual feedback for file status
            files_ready = all([ppes, dpp18, bud45])
            
            if st.form_submit_button(
                "🚀 Lancer le traitement", 
                use_container_width=True, 
                type="primary" if files_ready else "secondary",
                disabled=not files_ready
            ):
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
    
    def _render_chat_input(self, on_message_send: Callable, on_file_upload: Callable):
        """Renders simplified chat input"""
        col1, col2 = st.columns([10, 1])
        
        with col1:
            prompt = st.chat_input(
                "Tapez votre message ou glissez un fichier...",
                key="chat_input_modern",
                max_chars=2000
            )
        
        with col2:
            uploaded_file = st.file_uploader(
                "📎",
                type=['pdf', 'docx', 'txt', 'msg', 'xlsx', 'json'],
                key="file_upload_chat_modern",
                label_visibility="collapsed",
                help="Joindre un fichier"
            )
        
        # Handle inputs
        if prompt:
            on_message_send(prompt)
        
        if uploaded_file:
            # Prevent duplicate uploads
            file_key = f"{uploaded_file.name}_{uploaded_file.size}"
            if 'last_file_key' not in st.session_state or st.session_state.last_file_key != file_key:
                st.session_state.last_file_key = file_key
                on_file_upload(uploaded_file)
    
    def _render_messages_area(self, on_message_send: Callable):
        """Renders messages area - simplified"""
        for i, msg in enumerate(st.session_state.get('chat_history', [])):
            # Skip hidden system messages
            if msg.get('meta') == 'file_content':
                continue
            
            # Render message
            html, _ = self.chat_components.render_message(msg, i)
            st.markdown(html, unsafe_allow_html=True)
            
            # Quick actions for assistant messages
            if msg['role'] == 'assistant' and i == len(st.session_state.chat_history) - 1:
                # Only show quick actions for the last assistant message
                if st.session_state.get('current_file'):
                    col1, col2, col3 = st.columns([1, 1, 3])
                    with col1:
                        if st.button("📊 Extraire", key=f"quick_extract_{i}"):
                            st.session_state.pending_action = {'type': 'extract_budget'}
                            st.rerun()
                    with col2:
                        if st.button("🛠️ BPSS", key=f"quick_bpss_{i}"):
                            st.session_state.excel_tab = 'tools'
                            st.session_state.layout_mode = 'excel'
                            st.rerun()
        
        # Typing indicator
        if st.session_state.get('is_typing', False):
            st.markdown(self.chat_components.render_typing_indicator(), unsafe_allow_html=True)
    
    def _render_drag_drop_overlay(self):
        """Renders drag and drop overlay"""
        st.markdown("""
        <div id="drop-overlay" class="drop-overlay">
            <div class="drop-content">
                <div class="drop-icon">
                    <span style="font-size: 100px;">📥</span>
                </div>
                <h2>Déposez votre fichier ici</h2>
                <p>PDF, DOCX, XLSX, JSON, TXT, MSG</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def _handle_parse_formulas(self):
        """Handle formula parsing with progress"""
        if not st.session_state.get('current_file'):
            st.error("Aucun fichier à analyser")
            return
            
        try:
            from modules.excel_parser.parser_v3 import ExcelFormulaParser
            import tempfile
            
            # Save file temporarily
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
                tmp.write(st.session_state.current_file['raw_bytes'])
                temp_path = tmp.name
            
            # Parse formulas
            parser = ExcelFormulaParser()
            result = parser.parse_excel_file(temp_path, emit_script=True)
            
            # Clean up
            import os
            os.unlink(temp_path)
            
            # Show results
            stats = result['statistics']
            st.success(f"✅ Analyse terminée: {stats['success']}/{stats['total']} formules converties")
            
            # Store results
            st.session_state.parsed_formulas = result
            
        except Exception as e:
            st.error(f"Erreur: {str(e)}")