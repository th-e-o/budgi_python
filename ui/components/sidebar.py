# ui/components/sidebar.py
import streamlit as st
from typing import Callable, Dict, Any

class SidebarComponents:
    """Composants pour la sidebar avec les outils"""
    
    @staticmethod
    def render_tool_section(title: str, icon: str, key: str, 
                          render_content: Callable, expanded: bool = False):
        """Rend une section d'outil dans la sidebar"""
        with st.expander(f"{icon} {title}", expanded=expanded):
            st.markdown('<div class="tool-card">', unsafe_allow_html=True)
            render_content()
            st.markdown('</div>', unsafe_allow_html=True)
    
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
        """Rendu du module Excel"""
        uploaded = st.file_uploader(
            "📂 Charger un fichier Excel",
            type=['xlsx'],
            key="excel_main",
            help="Formats supportés : .xlsx"
        )
        
        if uploaded and st.session_state.get('excel_workbook'):
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
                    if st.button("🔧 Appliquer formules", use_container_width=True, key="apply_formulas"):
                        return {'action': 'apply_formulas', 'sheet': selected}
                    
                    if st.button("📊 Extraire budget", use_container_width=True, key="extract_budget"):
                        return {'action': 'extract_budget', 'sheet': selected}
                
                with col2:
                    if st.button("📈 Analyser", use_container_width=True, key="analyze_sheet"):
                        return {'action': 'analyze_sheet', 'sheet': selected}
                    
                    if st.button("💾 Exporter", use_container_width=True, key="export_excel"):
                        return {'action': 'export_excel', 'sheet': selected}
                
                # Aperçu des données
                with st.expander("👁️ Aperçu des données", expanded=False):
                    df = services['excel_handler'].sheet_to_dataframe(wb, selected)
                    st.dataframe(
                        df.head(10),
                        use_container_width=True,
                        height=200
                    )
        
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
                
                # Statistiques
                st.markdown("### 📊 Informations")
                if 'tags' in data:
                    st.metric("Nombre de tags", len(data.get('tags', [])))
                    
                    # Actions
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🔍 Analyser labels", use_container_width=True):
                            return {'action': 'analyze_labels', 'data': data}
                    
                    with col2:
                        if st.button("🔄 Mettre à jour", use_container_width=True):
                            return {'action': 'update_json', 'data': data}
                
                # Aperçu
                with st.expander("📋 Aperçu JSON", expanded=False):
                    st.json(data)
                    
            except json.JSONDecodeError as e:
                st.error(f"❌ Erreur de lecture JSON : {str(e)}")
        
        return None
    
    @staticmethod
    def render_history_section(chat_handler):
        """Rendu de la section historique"""
        st.markdown("### 📚 Historique de conversation")
        
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