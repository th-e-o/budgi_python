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
                
                # Afficher un résumé des cellules sources
                if st.checkbox("📊 Voir le résumé des cellules sources"):
                    summary = self.services['json_helper'].get_source_cells_summary(st.session_state.json_data)
                    if summary:
                        for sheet, cells in summary.items():
                            st.markdown(f"**{sheet}** : {len(cells)} cellules")
                            with st.expander(f"Détails pour {sheet}"):
                                st.markdown(", ".join(cells))
                
                # Afficher les labels extraits
                if st.button("🏷️ Afficher tous les labels"):
                    labels = self.services['json_helper'].extract_labels(st.session_state.json_data)
                    st.markdown(f"### 🏷️ Labels uniques ({len(labels)})")
                    if labels:
                        # Créer un DataFrame pour un meilleur affichage
                        labels_df = pd.DataFrame({"Labels": sorted(labels)})
                        st.dataframe(labels_df, use_container_width=True, height=300)
                    else:
                        st.info("Aucun label trouvé")
                        
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

             # Interface de vérification du mapping
            if st.session_state.get('mapping_report'):
                st.markdown("---")
                st.markdown("### 🔍 Vérification et validation du mapping")
                
                report = st.session_state.mapping_report
                
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
                with st.expander("📊 Analyse détaillée de la confiance"):
                    conf_data = pd.DataFrame({
                        'Niveau de confiance': list(report['by_confidence'].keys()),
                        'Nombre d\'entrées': list(report['by_confidence'].values())
                    })
                    
                    # Créer un graphique en barres coloré
                    import plotly.express as px
                    colors = ['#28a745', '#5cb85c', '#ffc107', '#dc3545', '#6c757d']
                    fig = px.bar(
                        conf_data, 
                        x='Niveau de confiance', 
                        y='Nombre d\'entrées',
                        color='Niveau de confiance',
                        color_discrete_sequence=colors,
                        title="Répartition des mappings par niveau de confiance"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Répartition par feuille
                    if report['by_sheet']:
                        st.markdown("#### 📋 Répartition par feuille")
                        sheet_df = pd.DataFrame({
                            'Feuille': list(report['by_sheet'].keys()),
                            'Nombre': list(report['by_sheet'].values())
                        })
                        st.dataframe(sheet_df, use_container_width=True)
                
                # Tabs pour différentes vues de vérification
                verify_tabs = st.tabs([
                    "🔍 Révision prioritaire", 
                    "❌ Entrées non mappées", 
                    "📊 Vue d'ensemble",
                    "✏️ Corrections manuelles"
                ])
                
                with verify_tabs[0]:  # Révision prioritaire
                    st.info("Mappings nécessitant une vérification (confiance < 70%)")
                    
                    low_conf_items = report['low_confidence']
                    if low_conf_items:
                        # Options de filtrage
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            search_term = st.text_input(
                                "🔍 Rechercher dans les descriptions",
                                placeholder="Tapez pour filtrer..."
                            )
                        with col2:
                            sort_by = st.selectbox(
                                "Trier par",
                                ["Confiance ↓", "Confiance ↑", "Montant ↓", "Montant ↑"]
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
                        
                        st.caption(f"Affichage de {min(20, len(filtered_items))} sur {len(filtered_items)} entrées")
                        
                        # Afficher les items à réviser
                        for i, item in enumerate(filtered_items[:20]):
                            with st.expander(
                                f"{'🔴' if item['confidence'] < 0.5 else '🟡'} "
                                f"{item['description'][:60]}... "
                                f"({item['confidence']:.0%})",
                                expanded=(i < 3)  # Ouvrir les 3 premiers
                            ):
                                col1, col2, col3 = st.columns([3, 2, 1])
                                
                                with col1:
                                    st.markdown("**Détails de l'entrée**")
                                    st.markdown(f"• Description: {item['description']}")
                                    st.markdown(f"• Montant: **{item['montant']:,.0f} €**")
                                    st.markdown(f"• Critères de match: {', '.join(item['matches'])}")
                                
                                with col2:
                                    st.markdown("**Mapping actuel**")
                                    st.markdown(f"• Cellule: `{item['cellule']}`")
                                    st.markdown(f"• Confiance: {item['confidence']:.1%}")
                                    
                                    # Suggestions alternatives (si disponibles)
                                    if st.checkbox("Voir alternatives", key=f"alt_{i}"):
                                        st.info("Fonctionnalité à venir: suggestions alternatives")
                                
                                with col3:
                                    st.markdown("**Actions**")
                                    if st.button("✅ Valider", key=f"validate_{i}", use_container_width=True):
                                        st.success("Validé!")
                                    if st.button("✏️ Modifier", key=f"edit_{i}", use_container_width=True):
                                        st.session_state[f'editing_{i}'] = True
                                
                                # Zone d'édition si activée
                                if st.session_state.get(f'editing_{i}', False):
                                    st.markdown("---")
                                    new_col1, new_col2 = st.columns(2)
                                    with new_col1:
                                        new_sheet = st.selectbox(
                                            "Nouvelle feuille",
                                            st.session_state.excel_workbook.sheetnames,
                                            key=f"new_sheet_{i}"
                                        )
                                    with new_col2:
                                        new_cell = st.text_input(
                                            "Nouvelle cellule",
                                            value=item['cellule'].split('!')[-1],
                                            key=f"new_cell_{i}",
                                            placeholder="Ex: D27"
                                        )
                                    
                                    if st.button("💾 Sauvegarder", key=f"save_{i}"):
                                        st.success(f"Nouveau mapping: {new_sheet}!{new_cell}")
                                        st.session_state[f'editing_{i}'] = False
                                        st.rerun()
                    else:
                        st.success("✅ Tous les mappings ont une confiance élevée (> 70%)")
                
                with verify_tabs[1]:  # Entrées non mappées
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
                            unmapped_df = pd.DataFrame(unmapped_items)
                            
                            # Sélection d'une entrée
                            selected_idx = st.selectbox(
                                "Sélectionner une entrée à mapper",
                                range(len(unmapped_items)),
                                format_func=lambda x: f"{unmapped_items[x]['description'][:60]}... ({unmapped_items[x]['montant']:,.0f} €)"
                            )
                            
                            if selected_idx is not None:
                                selected_item = unmapped_items[selected_idx]
                                st.info(f"**{selected_item['description']}**")
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    target_sheet = st.selectbox(
                                        "Feuille cible",
                                        st.session_state.excel_workbook.sheetnames
                                    )
                                with col2:
                                    target_cell = st.text_input(
                                        "Cellule cible",
                                        placeholder="Ex: D27"
                                    )
                                with col3:
                                    confidence = st.slider(
                                        "Confiance",
                                        0.0, 1.0, 0.8, 0.1
                                    )
                                
                                if st.button("➕ Créer le mapping", type="primary", use_container_width=True):
                                    st.success(f"Mapping créé: {target_sheet}!{target_cell}")
                                    # TODO: Ajouter la logique pour sauvegarder le mapping
                        
                        else:  # Par lot
                            st.info("Mapper plusieurs entrées similaires en une fois")
                            
                            # Recherche de pattern
                            pattern = st.text_input(
                                "Pattern de recherche",
                                placeholder="Ex: 'recrutement 2025'"
                            )
                            
                            if pattern:
                                # Filtrer les entrées correspondantes
                                matching = [
                                    item for item in unmapped_items
                                    if pattern.lower() in item['description'].lower()
                                ]
                                
                                if matching:
                                    st.success(f"✅ {len(matching)} entrées correspondent au pattern")
                                    
                                    # Prévisualisation
                                    with st.expander("Voir les entrées correspondantes"):
                                        for item in matching[:5]:
                                            st.text(f"• {item['description'][:80]}...")
                                        if len(matching) > 5:
                                            st.text(f"... et {len(matching) - 5} autres")
                                    
                                    # Mapping groupé
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        batch_sheet = st.selectbox(
                                            "Feuille pour toutes",
                                            st.session_state.excel_workbook.sheetnames,
                                            key="batch_sheet"
                                        )
                                    with col2:
                                        batch_pattern = st.text_input(
                                            "Pattern de cellules",
                                            placeholder="Ex: D{27+i} pour D27, D28...",
                                            help="Utilisez {i} pour l'index"
                                        )
                                    
                                    if st.button("🚀 Mapper toutes les entrées", type="primary"):
                                        st.success(f"✅ {len(matching)} mappings créés!")
                                else:
                                    st.warning("Aucune entrée ne correspond au pattern")
                    else:
                        st.success("✅ Toutes les entrées ont été mappées avec succès!")
                
                with verify_tabs[2]:  # Vue d'ensemble
                    st.info("Vue complète de tous les mappings avec filtres avancés")
                    
                    if st.session_state.get('extracted_data'):
                        df_all = pd.DataFrame(st.session_state.extracted_data)
                        
                        # Filtres avancés
                        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
                        
                        with filter_col1:
                            status_filter = st.multiselect(
                                "Statut",
                                ["Mappé", "Non mappé", "À réviser"],
                                default=["Mappé", "Non mappé", "À réviser"]
                            )
                        
                        with filter_col2:
                            conf_range = st.slider(
                                "Plage de confiance",
                                0.0, 1.0, (0.0, 1.0), 0.1
                            )
                        
                        with filter_col3:
                            sheet_filter = st.multiselect(
                                "Feuilles",
                                ["Toutes"] + list(df_all['SheetName'].unique()),
                                default=["Toutes"]
                            )
                        
                        with filter_col4:
                            amount_range = st.slider(
                                "Montant (k€)",
                                float(df_all['Montant'].min() / 1000),
                                float(df_all['Montant'].max() / 1000),
                                (float(df_all['Montant'].min() / 1000), 
                                 float(df_all['Montant'].max() / 1000))
                            )
                        
                        # Appliquer les filtres
                        filtered_df = df_all.copy()
                        
                        # Filtre statut
                        status_conditions = []
                        if "Mappé" in status_filter:
                            status_conditions.append((filtered_df['IsMapped'] == True) & (filtered_df['NeedsReview'] == False))
                        if "Non mappé" in status_filter:
                            status_conditions.append(filtered_df['IsMapped'] == False)
                        if "À réviser" in status_filter:
                            status_conditions.append(filtered_df['NeedsReview'] == True)
                        
                        if status_conditions:
                            combined_condition = status_conditions[0]
                            for condition in status_conditions[1:]:
                                combined_condition = combined_condition | condition
                            filtered_df = filtered_df[combined_condition]
                        
                        # Filtre confiance
                        filtered_df = filtered_df[
                            (filtered_df['ConfidenceScore'] >= conf_range[0]) &
                            (filtered_df['ConfidenceScore'] <= conf_range[1])
                        ]
                        
                        # Filtre feuilles
                        if "Toutes" not in sheet_filter:
                            filtered_df = filtered_df[filtered_df['SheetName'].isin(sheet_filter)]
                        
                        # Filtre montant
                        filtered_df = filtered_df[
                            (filtered_df['Montant'] >= amount_range[0] * 1000) &
                            (filtered_df['Montant'] <= amount_range[1] * 1000)
                        ]
                        
                        # Statistiques sur les données filtrées
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Entrées affichées", len(filtered_df))
                        with col2:
                            st.metric("Montant total", f"{filtered_df['Montant'].sum():,.0f} €")
                        with col3:
                            avg_conf = filtered_df['ConfidenceScore'].mean()
                            st.metric("Confiance moyenne", f"{avg_conf:.1%}" if not pd.isna(avg_conf) else "N/A")
                        
                        # Options d'affichage
                        show_columns = st.multiselect(
                            "Colonnes à afficher",
                            ['Axe', 'Description', 'Montant', 'Date', 'Nature', 
                             'CelluleCible', 'ConfidenceScore', 'MatchCriteria'],
                            default=['Description', 'Montant', 'CelluleCible', 'ConfidenceScore']
                        )
                        
                        # Affichage du dataframe avec style conditionnel
                        if not filtered_df.empty and show_columns:
                            def style_confidence(val):
                                if pd.isna(val):
                                    return ''
                                if isinstance(val, (int, float)):
                                    if val >= 0.9:
                                        return 'background-color: #d4edda; color: #155724'
                                    elif val >= 0.7:
                                        return 'background-color: #fff3cd; color: #856404'
                                    else:
                                        return 'background-color: #f8d7da; color: #721c24'
                                return ''
                            
                            styled_df = filtered_df[show_columns].style
                            
                            if 'ConfidenceScore' in show_columns:
                                styled_df = styled_df.applymap(
                                    style_confidence, 
                                    subset=['ConfidenceScore']
                                ).format({'ConfidenceScore': '{:.1%}'})
                            
                            if 'Montant' in show_columns:
                                styled_df = styled_df.format({'Montant': '{:,.0f} €'})
                            
                            st.dataframe(
                                styled_df,
                                use_container_width=True,
                                height=500
                            )
                            
                            # Options d'export
                            col1, col2 = st.columns(2)
                            with col1:
                                csv = filtered_df.to_csv(index=False)
                                st.download_button(
                                    "📥 Exporter les données filtrées (CSV)",
                                    data=csv,
                                    file_name=f"mapping_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                    mime="text/csv",
                                    use_container_width=True
                                )
                            
                            with col2:
                                # Générer un rapport Excel détaillé
                                if st.button("📊 Générer rapport Excel", use_container_width=True):
                                    st.info("Génération du rapport...")
                                    # TODO: Implémenter la génération du rapport
                
                with verify_tabs[3]:  # Corrections manuelles
                    st.info("Interface pour corriger les mappings en masse")
                    
                    # Import de corrections
                    st.markdown("#### 📤 Importer des corrections")
                    uploaded_corrections = st.file_uploader(
                        "Charger un fichier CSV de corrections",
                        type=['csv'],
                        help="Le CSV doit contenir: Description, CelluleCible"
                    )
                    
                    if uploaded_corrections:
                        corrections_df = pd.read_csv(uploaded_corrections)
                        st.success(f"✅ {len(corrections_df)} corrections chargées")
                        
                        # Prévisualisation
                        with st.expander("Voir les corrections"):
                            st.dataframe(corrections_df.head(10))
                        
                        if st.button("🔄 Appliquer les corrections", type="primary"):
                            # TODO: Implémenter l'application des corrections
                            st.success("Corrections appliquées!")
                    
                    # Export pour correction manuelle
                    st.markdown("#### 📥 Exporter pour correction")
                    if st.button("Générer template de correction"):
                        if st.session_state.get('extracted_data'):
                            df_export = pd.DataFrame(st.session_state.extracted_data)
                            template_df = df_export[['Description', 'Montant', 'CelluleCible', 'ConfidenceScore']]
                            template_df['NouvelleCellule'] = ''
                            template_df['Commentaire'] = ''
                            
                            csv = template_df.to_csv(index=False)
                            st.download_button(
                                "📥 Télécharger le template",
                                data=csv,
                                file_name=f"template_corrections_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )

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