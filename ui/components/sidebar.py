# ui/components/sidebar.py - Version corrigée sans expanders imbriqués
import streamlit as st
from typing import Callable, Dict, Any
from datetime import datetime
import openpyxl

class SidebarComponents:
    """Composants pour la sidebar avec les outils"""
    
    @staticmethod
    def render_tool_section(title: str, icon: str, key: str, 
                          render_content: Callable, expanded: bool = False):
        """Rend une section d'outil dans la sidebar"""
        with st.expander(f"{icon} {title}", expanded=expanded):
            render_content()
    
    @staticmethod
    def render_bpss_tool(services: Dict[str, Any]):
        """Rendu de l'outil BPSS"""
        with st.form("bpss_form"):
            col1, col2 = st.columns(2)
            with col1:
                year = st.number_input("Année", value=2025, min_value=2000, max_value=2100)
                ministry = st.text_input("Code Ministère", value="38")
            with col2:
                program = st.text_input("Code Programme", value="150")
            
            st.markdown("### 📁 Fichiers requis")
            ppes = st.file_uploader("PP‑E‑S (.xlsx)", type=['xlsx'], key="bpss_ppes")
            dpp18 = st.file_uploader("DPP 18 (.xlsx)", type=['xlsx'], key="bpss_dpp18")
            bud45 = st.file_uploader("BUD 45 (.xlsx)", type=['xlsx'], key="bpss_bud45")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                submit = st.form_submit_button("🚀 Générer", use_container_width=True, type="primary")
            with col2:
                st.form_submit_button("❓", use_container_width=True, help="Aide sur l'outil BPSS")
            
            if submit and all([ppes, dpp18, bud45]):
                return {
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
                }
        return None
    
    @staticmethod
    def render_excel_module(services: Dict[str, Any]):
        """Rendu du module Excel (Mesures Catégorielles)"""
        uploaded = st.file_uploader(
            "📂 Charger un fichier Excel",
            type=['xlsx'],
            key="excel_main",
            help="Formats supportés : .xlsx"
        )
        
        if uploaded:
            # Charger le fichier si pas déjà fait
            if not st.session_state.get('excel_workbook'):
                try:
                    wb = services['excel_handler'].load_workbook_from_bytes(uploaded.getbuffer())
                    st.session_state.excel_workbook = wb
                    st.session_state.current_file = {
                        'name': uploaded.name,
                        'content': uploaded.getbuffer(),
                        'path': None,
                        'raw_bytes': uploaded.getbuffer()
                    }
                except Exception as e:
                    st.error(f"Erreur chargement Excel: {str(e)}")
                    return None
        
        if st.session_state.get('excel_workbook'):
            wb = st.session_state.excel_workbook
            sheets = wb.sheetnames
            
            selected = st.selectbox(
                "📑 Sélectionner une feuille",
                sheets,
                key="sheet_selector"
            )
            
            if selected:
                # Actions disponibles
                st.markdown("### ⚡ Actions rapides")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🔍 Parser formules", use_container_width=True, key="parse_formulas"):
                        return {'action': 'parse_excel', 'sheet': selected}
                    
                    if st.button("🔧 Appliquer formules", use_container_width=True, key="apply_formulas"):
                        return {'action': 'apply_formulas', 'sheet': selected}
                    
                    if st.button("📊 Extraire budget", use_container_width=True, key="extract_budget"):
                        return {'action': 'extract_budget', 'sheet': selected}
                
                with col2:
                    if st.button("📈 Analyser", use_container_width=True, key="analyze_sheet"):
                        return {'action': 'analyze_sheet', 'sheet': selected}
                    
                    if st.button("💾 Exporter", use_container_width=True, key="export_excel"):
                        return {'action': 'export_excel', 'sheet': selected}
                
                # Aperçu des données - PAS dans un expander pour éviter l'imbrication
                st.markdown("### 👁️ Aperçu des données")
                
                # Toggle pour afficher/masquer l'aperçu
                show_preview = st.checkbox("Afficher l'aperçu", key="show_excel_preview", value=False)
                
                if show_preview:
                    try:
                        df = services['excel_handler'].sheet_to_dataframe(wb, selected)
                        st.dataframe(
                            df.head(10),
                            use_container_width=True,
                            height=200
                        )
                        st.caption(f"Affichage des 10 premières lignes sur {len(df)}")
                    except Exception as e:
                        st.error(f"Erreur affichage: {str(e)}")
        
        return None
    
    @staticmethod
    def render_json_helper(services: Dict[str, Any]):
        """Rendu du JSON Helper"""
        uploaded = st.file_uploader(
            "📄 Charger un fichier JSON",
            type=['json'],
            key="json_upload",
            help="Fichier de configuration JSON"
        )
        
        if uploaded:
            import json
            try:
                data = json.load(uploaded)
                st.session_state.json_data = data
                
                # Statistiques
                st.markdown("### 📊 Informations")
                if 'tags' in data:
                    st.metric("Nombre de tags", len(data.get('tags', [])))
                    
                    # Extraire et afficher les labels
                    labels = services['json_helper'].extract_labels(data)
                    if labels:
                        # Utiliser un toggle au lieu d'un expander
                        st.markdown("### 🏷️ Labels extraits")
                        show_labels = st.checkbox("Afficher les labels", key="show_json_labels", value=False)
                        if show_labels:
                            # Afficher en colonnes pour gagner de la place
                            n_cols = 3
                            cols = st.columns(n_cols)
                            for i, label in enumerate(labels):
                                with cols[i % n_cols]:
                                    st.caption(f"• {label}")
                    
                    # Actions
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🔍 Analyser labels", use_container_width=True):
                            return {'action': 'analyze_labels', 'data': data}
                    
                    with col2:
                        if st.button("🔄 Mettre à jour tags", use_container_width=True):
                            if st.session_state.get('excel_workbook'):
                                return {'action': 'update_json_tags', 'data': data}
                            else:
                                st.warning("Chargez d'abord un fichier Excel")
                
                # Aperçu JSON - utiliser un toggle
                st.markdown("### 📋 Aperçu JSON")
                show_json = st.checkbox("Afficher le JSON", key="show_json_preview", value=False)
                if show_json:
                    # Limiter la hauteur pour ne pas prendre trop de place
                    st.json(data, expanded=False)
                    
            except json.JSONDecodeError as e:
                st.error(f"❌ Erreur de lecture JSON : {str(e)}")
        
        return None
    
    @staticmethod
    def render_history_section(chat_handler):
        """Rendu de la section historique"""
        st.markdown("### 📚 Historique")
        
        messages_count = len(st.session_state.get('chat_history', []))
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Messages", messages_count)
        
        with col2:
            if messages_count > 0:
                if st.button("🗑️ Effacer", use_container_width=True):
                    return {'action': 'clear_history'}
        
        if messages_count > 0:
            if st.button("💾 Télécharger l'historique", use_container_width=True):
                chat_export = chat_handler.export_history(st.session_state.chat_history)
                st.download_button(
                    label="📥 Télécharger (.txt)",
                    data=chat_export,
                    file_name=f"budgibot_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        
        return None