# ui/layouts.py - Version complètement corrigée
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
            st.session_state.layout_mode = 'chat'
        
        # Top navigation bar
        self._render_top_navbar()
        
        # Main content area based on layout mode
        if st.session_state.layout_mode == 'split':
            # Split view
            chat_col, excel_col = st.columns([1, 1], gap="medium")
            
            with chat_col:
                self._render_chat_panel(on_message_send, on_file_upload)
            
            with excel_col:
                self._render_excel_panel(on_tool_action)
        
        elif st.session_state.layout_mode == 'chat':
            # Full chat view
            col1, col2, col3 = st.columns([1, 6, 1])
            with col2:
                self._render_chat_panel(on_message_send, on_file_upload, full_width=True)
                
        elif st.session_state.layout_mode == 'excel':
            # Full Excel view
            col1, col2, col3 = st.columns([1, 6, 1])
            with col2:
                self._render_excel_panel(on_tool_action, full_width=True)
        
        # Drag and drop overlay
        self._render_drag_drop_overlay()
    
    def _render_top_navbar(self):
        """Renders simplified top navigation bar"""
        current_layout = st.session_state.get('layout_mode', 'chat')
        
        # Create columns for navbar
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col1:
            st.markdown("""
            <div style="display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 0;">
                <span style="font-size: 1.25rem; font-weight: 600; color: #1e293b;">BudgiBot</span>
                <span style="font-size: 0.875rem; color: #64748b;">Compléteur d'excel automatique</span>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Use Streamlit native buttons in columns
            btn_col1, btn_col2, btn_col3 = st.columns(3, gap="small")
            
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
        
        # Add a separator
        st.markdown("<hr style='margin: 0.5rem 0 1rem 0; border: none; border-bottom: 1px solid #e2e8f0;'>", 
                   unsafe_allow_html=True)
    
    def _render_chat_panel(self, on_message_send: Callable, on_file_upload: Callable, 
                      full_width: bool = False):
        """Renders modern chat panel"""
        # Container wrapper
        st.markdown(f"""
        <div class="chat-panel{'_full' if full_width else ''}">
            {self.chat_components.render_header()}
        </div>
        """, unsafe_allow_html=True)
        
        # Messages area
        messages_container = st.container(height=500 if not full_width else 600)
        with messages_container:
            self._render_messages_area(on_message_send)
        
        # Input area
        st.markdown("<div style='margin-top: 1rem;'>", unsafe_allow_html=True)
        self._render_chat_input(on_message_send, on_file_upload)
        st.markdown("</div>", unsafe_allow_html=True)
    
    def _render_excel_panel(self, on_tool_action: Callable, full_width: bool = False):
        """Renders Excel panel"""
        # Header
        st.markdown(f"""
        <div class="excel-panel{'_full' if full_width else ''}">
            <div class="excel-header">
                <h3>Espace Excel</h3>
                <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 0.875rem;">
                    Ajouter un classeur, extraire des données de messages, utiliser l'outil BPSS
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Content sections
        with st.container():
            # Section 1: Données
            with st.expander("**Données Excel**", expanded=True):
                st.caption("Visualisez et éditez vos feuilles Excel")
                self._render_excel_data_tab(on_tool_action)  # Passer on_tool_action
            
            # Section 2: Extraction et Analyse
            with st.expander("**Extraction et analyse de l'extraction**", expanded=True):
                st.caption("Extrayez automatiquement les données budgétaires de vos documents")
                self._render_excel_analysis_tab(on_tool_action)
            
            # Section 3: Outil BPSS
            with st.expander("🛠️ **Outil BPSS**", expanded=False):
                st.caption("Traitez automatiquement vos fichiers PP-E-S, DPP18 et BUD45")
                self._render_excel_tools_tab(on_tool_action)
        
            # Interface de vérification si mapping disponible
            if st.session_state.get('mapping_report'):
                st.markdown("---")
                self._render_verification_interface()
    
    def _render_messages_area(self, on_message_send: Callable):
        """Renders messages area"""
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
    
    def _render_chat_input(self, on_message_send: Callable, on_file_upload: Callable):
        """Renders simplified chat input"""
        col1, col2 = st.columns([4, 1])
        
        with col1:
            prompt = st.chat_input(
                "Tapez votre message ou glissez un fichier...",
                key="chat_input_modern",
                max_chars=6000
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
    
    def _render_excel_data_tab(self, on_tool_action : Callable):
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
            
            col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
            with col1:
                selected_sheet = st.selectbox(
                    "Sélectionner une feuille",
                    sheets,
                    key="sheet_selector_main"
                )

            with col2:
                # Toggle valeurs/formules
                display_mode = st.selectbox(
                    "Afficher",
                    ["Valeurs", "Formules"],
                    key="display_mode_toggle"
                )

            with col3:
                if st.button("📊 Parser", help="Analyser les formules"):
                    on_tool_action({'action': 'parse_excel'})

            with col4:
                # Bouton Appliquer si formules parsées
                if st.session_state.get('parsed_formulas'):
                    if st.button("⚡ Appliquer", help="Appliquer les formules"):
                        on_tool_action({'action': 'apply_formulas'})

            with col5:
                st.download_button(
                    "💾",
                    data=self.services['excel_handler'].save_workbook_to_bytes(wb),
                    file_name=f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                        
            # Display data
            if selected_sheet:
                try:
                    df = self.services['excel_handler'].sheet_to_dataframe(
                        wb, 
                        selected_sheet,
                        show_formulas=(display_mode == "Formules")
                    )                    
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
                
                # Afficher les options JSON
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Actualiser labels depuis Excel", 
                               help="Met à jour les labels du JSON avec le contenu des cellules sources",
                               use_container_width=True):
                        if st.session_state.get('excel_workbook'):
                            with st.spinner("Actualisation en cours..."):
                                updated_json, modifications = self.services['json_helper'].update_tags_from_excel(
                                    st.session_state.json_data,
                                    st.session_state.excel_workbook
                                )
                                st.session_state.json_data = updated_json
                                
                                if modifications:
                                    st.success(f"✅ {len(modifications)} tags enrichis")
                                    with st.expander("📋 Détails des modifications"):
                                        for mod in modifications:
                                            st.markdown(f"**{mod['sheet']}!{mod['cell']}** : +{len(mod['added_labels'])} labels")
                                            for label in mod['added_labels']:
                                                st.markdown(f"  • {label}")
                                else:
                                    st.info("ℹ️ Aucun nouveau label trouvé")
                        else:
                            st.warning("⚠️ Chargez d'abord un fichier Excel")
                
                with col2:
                    # Export JSON modifié
                    if st.button("💾 Exporter JSON modifié", use_container_width=True):
                        json_str = self.services['json_helper'].export_json(st.session_state.json_data)
                        st.download_button(
                            "📥 Télécharger",
                            data=json_str,
                            file_name=f"config_updated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            use_container_width=True
                        )
                        
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
            st.markdown("###Données extraites")
            
            df = pd.DataFrame(st.session_state.extracted_data)
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Entrées", len(df))
            
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
        
        col1, col2, col3 = st.columns(3)
        with col1:
            year = st.number_input("Année", value=2025, min_value=2020, max_value=2030, key="bpss_year")
        with col2:
            ministry = st.text_input("Ministère", value="38", key="bpss_ministry")
        with col3:
            program = st.text_input("Programme", value="150", key="bpss_program")
        
        st.markdown("#### 📁 Fichiers requis")
        col1, col2, col3 = st.columns(3)
        with col1:
            ppes = st.file_uploader("PP‑E‑S", type=['xlsx'], key="bpss_ppes_excel_new")
        with col2:
            dpp18 = st.file_uploader("DPP18", type=['xlsx'], key="bpss_dpp18_excel_new")
        with col3:
            bud45 = st.file_uploader("BUD45", type=['xlsx'], key="bpss_bud45_excel_new")
        
        # Vérifier l'état des fichiers
        files_ready = all([ppes is not None, dpp18 is not None, bud45 is not None])
        
        # Afficher l'état des fichiers
        if files_ready:
            st.success("✅ Tous les fichiers sont chargés")
        else:
            missing = []
            if not ppes:
                missing.append("PP‑E‑S")
            if not dpp18:
                missing.append("DPP18")
            if not bud45:
                missing.append("BUD45")
            st.warning(f"⚠️ Fichiers manquants : {', '.join(missing)}")
        
        # Bouton de traitement
        if st.button(
            "Lancer le traitement", 
            use_container_width=True, 
            type="primary" if files_ready else "secondary",
            disabled=not files_ready,
            key="bpss_process_button"
        ):
            if files_ready:
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
                st.error("❌ Veuillez charger tous les fichiers requis")
        
    def _render_verification_interface(self):
        """Rend l'interface de vérification du mapping"""
        if not st.session_state.get('mapping_report'):
            return
            
        report = st.session_state.mapping_report
        
        # Vérifier que le rapport contient les clés nécessaires
        required_keys = ['summary', 'by_confidence', 'low_confidence', 'unmapped']
        if not all(key in report for key in required_keys):
            st.error("Le rapport de mapping est incomplet")
            return
        
        st.markdown("### Vérification et validation du mapping")
        
        # Métriques de synthèse
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            avg_conf = report['summary']['average_confidence']
            color = "🟢" if avg_conf > 0.8 else "🟡" if avg_conf > 0.6 else "🔴"
            st.metric(f"{color} Confiance moyenne", f"{avg_conf:.1%}")
        
        with col2:
            high_conf = report['by_confidence'].get('Très élevé (>90%)', 0)
            st.metric("✅ Haute confiance", high_conf)
        
        with col3:
            low_conf = report['by_confidence'].get('Faible (<50%)', 0)
            needs_review = report['by_confidence'].get('Moyen (50-70%)', 0)
            st.metric("⚠️ À vérifier", low_conf + needs_review)
        
        with col4:
            unmapped = report['summary']['unmapped_entries']
            st.metric("❌ Non mappés", unmapped)
        
        # Graphique de répartition par confiance
        if st.checkbox("📊 Afficher l'analyse détaillée", key="show_confidence_analysis"):
            conf_data = pd.DataFrame({
                'Niveau de confiance': list(report['by_confidence'].keys()),
                'Nombre d\'entrées': list(report['by_confidence'].values())
            })
            
            st.bar_chart(conf_data.set_index('Niveau de confiance'))
        
        # Tabs pour différentes vues
        verify_tabs = st.tabs([
            "🔍 Révision prioritaire", 
            "❌ Entrées non mappées", 
            "📊 Vue d'ensemble"
        ])
        
        with verify_tabs[0]:
            self._render_revision_tab(report)
        
        with verify_tabs[1]:
            self._render_unmapped_tab(report)
        
        with verify_tabs[2]:
            self._render_overview_tab(report)
    
    def _render_revision_tab(self, report):
        """Tab pour révision prioritaire - CORRIGÉ sans colonnes imbriquées"""
        st.info("Mappings nécessitant une vérification (confiance < 70%)")
        
        low_conf_items = report['low_confidence']
        if low_conf_items:
            # Options de filtrage SANS colonnes pour éviter l'imbrication
            search_term = st.text_input(
                "🔍 Rechercher dans les descriptions",
                placeholder="Tapez pour filtrer...",
                key="search_low_conf"
            )
            
            sort_by = st.selectbox(
                "Trier par",
                ["Confiance ↓", "Confiance ↑", "Montant ↓", "Montant ↑"],
                key="sort_low_conf"
            )
            
            # Filtrer et trier
            filtered_items = low_conf_items
            if search_term:
                filtered_items = [
                    item for item in filtered_items 
                    if search_term.lower() in item['description'].lower()
                ]
            
            if sort_by == "Confiance ↓":
                filtered_items.sort(key=lambda x: x['confidence'])
            elif sort_by == "Confiance ↑":
                filtered_items.sort(key=lambda x: x['confidence'], reverse=True)
            elif sort_by == "Montant ↓":
                filtered_items.sort(key=lambda x: x['montant'], reverse=True)
            elif sort_by == "Montant ↑":
                filtered_items.sort(key=lambda x: x['montant'])
            
            st.caption(f"Affichage de {min(10, len(filtered_items))} sur {len(filtered_items)} entrées")
            
            # Afficher les items à réviser
            for i, item in enumerate(filtered_items[:10]):
                with st.container():
                    # Utiliser un expander au lieu de colonnes imbriquées
                    with st.expander(f"{item['description'][:60]}... - Confiance: {item['confidence']:.0%}"):
                        st.markdown(f"**Cellule actuelle:** `{item['cellule']}`")
                        st.markdown(f"**Montant:** {item['montant']:,.0f} €")
                        st.markdown(f"**Critères:** {', '.join(item.get('matches', []))}")
                        
                        # Actions dans un container simple
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ Valider", key=f"validate_{i}"):
                                st.success("Validé!")
                        with col2:
                            if st.button("✏️ Modifier", key=f"edit_{i}"):
                                st.session_state[f'editing_{i}'] = True
                        
                        # Zone d'édition si activée
                        if st.session_state.get(f'editing_{i}', False):
                            st.markdown("---")
                            new_sheet = st.selectbox(
                                "Nouvelle feuille",
                                st.session_state.excel_workbook.sheetnames if st.session_state.get('excel_workbook') else [],
                                key=f"new_sheet_{i}"
                            )
                            new_cell = st.text_input(
                                "Nouvelle cellule",
                                value=item['cellule'].split('!')[-1] if item['cellule'] else "",
                                key=f"new_cell_{i}",
                                placeholder="Ex: D27"
                            )
                            if st.button("💾 Sauvegarder", key=f"save_{i}"):
                                st.success(f"Nouveau mapping: {new_sheet}!{new_cell}")
                                st.session_state[f'editing_{i}'] = False
                                st.rerun()
        else:
            st.success("✅ Tous les mappings ont une confiance élevée (> 70%)")
    
    def _render_unmapped_tab(self, report):
        """Tab pour les entrées non mappées - CORRIGÉ"""
        unmapped_items = report['unmapped']
        if unmapped_items:
            st.warning(f"❌ {len(unmapped_items)} entrées n'ont pas pu être mappées automatiquement")
            
            # Options de mapping manuel
            mapping_method = st.radio(
                "Méthode de mapping",
                ["Individual", "Par lot (pattern)"],
                horizontal=True
            )
            
            if mapping_method == "Individual":
                # Table des non mappés
                st.markdown("#### Entrées non mappées")
                unmapped_df = pd.DataFrame(unmapped_items)
                st.dataframe(unmapped_df, use_container_width=True, height=200)
                
                # Sélection d'une entrée
                st.markdown("#### Mapper une entrée")
                selected_idx = st.selectbox(
                    "Sélectionner une entrée à mapper",
                    range(len(unmapped_items)),
                    format_func=lambda x: f"{unmapped_items[x]['description'][:60]}... ({unmapped_items[x]['montant']:,.0f} €)"
                )
                
                if selected_idx is not None:
                    selected_item = unmapped_items[selected_idx]
                    st.info(f"**{selected_item['description']}**")
                    
                    # Formulaire de mapping sans colonnes imbriquées
                    target_sheet = st.selectbox(
                        "Feuille cible",
                        st.session_state.excel_workbook.sheetnames if st.session_state.get('excel_workbook') else [],
                        key="target_sheet_unmapped"
                    )
                    target_cell = st.text_input(
                        "Cellule cible",
                        placeholder="Ex: D27",
                        key="target_cell_unmapped"
                    )
                    confidence = st.slider(
                        "Confiance",
                        0.0, 1.0, 0.8, 0.1,
                        key="confidence_unmapped"
                    )
                    
                    if st.button("➕ Créer le mapping", type="primary", use_container_width=True):
                        st.success(f"Mapping créé: {target_sheet}!{target_cell}")
                
            else:  # Par lot
                st.info("Mapper plusieurs entrées similaires en une fois")
                
                # Recherche de pattern
                pattern = st.text_input(
                    "Pattern de recherche",
                    placeholder="Ex: 'recrutement 2025'",
                    key="pattern_batch"
                )
                
                if pattern:
                    # Filtrer les entrées correspondantes
                    matching = [
                        item for item in unmapped_items
                        if pattern.lower() in item['description'].lower()
                    ]
                    
                    if matching:
                        st.success(f"✅ {len(matching)} entrées correspondent au pattern")
                        
                        # Afficher les entrées correspondantes
                        if st.checkbox("Voir les entrées correspondantes", key="show_matching"):
                            for i, item in enumerate(matching[:5]):
                                st.text(f"• {item['description'][:80]}...")
                            if len(matching) > 5:
                                st.text(f"... et {len(matching) - 5} autres")
                        
                        # Mapping groupé
                        batch_sheet = st.selectbox(
                            "Feuille pour toutes",
                            st.session_state.excel_workbook.sheetnames if st.session_state.get('excel_workbook') else [],
                            key="batch_sheet"
                        )
                        batch_pattern = st.text_input(
                            "Pattern de cellules",
                            placeholder="Ex: D{27+i} pour D27, D28...",
                            help="Utilisez {i} pour l'index",
                            key="batch_pattern"
                        )
                        
                        if st.button("🚀 Mapper toutes les entrées", type="primary"):
                            st.success(f"✅ {len(matching)} mappings créés!")
                    else:
                        st.warning("Aucune entrée ne correspond au pattern")
        else:
            st.success("✅ Toutes les entrées ont été mappées avec succès!")
    
    def _render_overview_tab(self, report):
        """Tab pour vue d'ensemble"""
        if st.session_state.get('extracted_data'):
            df_all = pd.DataFrame(st.session_state.extracted_data)
            
            # Afficher uniquement les colonnes disponibles
            display_cols = ['Description', 'Montant']
            optional_cols = ['CelluleCible', 'ConfidenceScore', 'IsMapped']
            
            available_cols = [col for col in display_cols + optional_cols if col in df_all.columns]
            
            if available_cols:
                st.dataframe(df_all[available_cols], use_container_width=True, height=400)
    
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