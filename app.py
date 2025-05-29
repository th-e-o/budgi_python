import streamlit as st
import asyncio
from pathlib import Path
import pandas as pd
from datetime import datetime
import logging

# Import des modules
from core.llm_client import MistralClient
from core.file_handler import FileHandler
from core.chat_handler import ChatHandler
from core.excel_handler import ExcelHandler
from modules.budget_extractor import BudgetExtractor
from modules.bpss_tool import BPSSTool
from modules.json_helper import JSONHelper
from config import config

# Configuration de la page
st.set_page_config(
    page_title="BudgiBot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.5rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #1ABC9C;
        color: white;
        align-self: flex-end;
        max-width: 80%;
    }
    .bot-message {
        background-color: #4169E1;
        color: white;
        align-self: flex-start;
        max-width: 80%;
    }
    .stButton button {
        background-color: #4169E1;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation des services
@st.cache_resource
def init_services():
    return {
        'llm_client': MistralClient(),
        'file_handler': FileHandler(),
        'chat_handler': ChatHandler(),
        'excel_handler': ExcelHandler(),
        'budget_extractor': BudgetExtractor(),
        'bpss_tool': BPSSTool(),
        'json_helper': JSONHelper()
    }

services = init_services()

# État de session
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'current_file' not in st.session_state:
    st.session_state.current_file = None

if 'excel_workbook' not in st.session_state:
    st.session_state.excel_workbook = None

if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = None

# Interface principale
def main():
    st.title("🤖 BudgiBot - Assistant Budgétaire")
    
    # Layout en colonnes
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Zone de chat
        st.header("💬 Chat")
        
        # Historique du chat
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.chat_history:
                if msg['role'] == 'user':
                    st.markdown(
                        f'<div class="chat-message user-message">{msg["content"]}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div class="chat-message bot-message">{msg["content"]}</div>',
                        unsafe_allow_html=True
                    )
        
        # Zone de saisie
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_area(
                "Votre message",
                key="user_input",
                height=100,
                placeholder="Écrivez votre message ici..."
            )
            
            col_send, col_file = st.columns([1, 1])
            with col_send:
                send_button = st.form_submit_button("📤 Envoyer", use_container_width=True)
            with col_file:
                uploaded_file = st.file_uploader(
                    "📎 Joindre un fichier",
                    type=['pdf', 'docx', 'txt', 'msg', 'xlsx'],
                    key="file_upload"
                )
        
        # Traitement du message
        if send_button and user_input:
            asyncio.run(handle_user_message(user_input))
        
        # Traitement du fichier
        if uploaded_file:
            asyncio.run(handle_file_upload(uploaded_file))
        
        # Bouton de téléchargement de l'historique
        if st.session_state.chat_history:
            st.download_button(
                label="💾 Télécharger l'historique",
                data=services['chat_handler'].export_history(st.session_state.chat_history),
                file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
    
    with col2:
        # Outils
        st.header("🛠️ Outils Budgétaires")
        
        # Outil BPSS
        with st.expander("📊 Outil BPSS Excel", expanded=False):
            render_bpss_tool()
        
        # Module Mesures Catégorielles
        with st.expander("📈 Mesures Catégorielles", expanded=True):
            render_excel_module()
        
        # JSON Helper
        with st.expander("📄 JSON Helper", expanded=False):
            render_json_helper()

async def handle_user_message(message: str):
    """Gère l'envoi d'un message utilisateur"""
    # Ajouter à l'historique
    st.session_state.chat_history.append({
        'role': 'user',
        'content': message
    })
    
    # Obtenir la réponse du bot
    with st.spinner("BudgiBot réfléchit..."):
        response = await services['llm_client'].chat(st.session_state.chat_history)
    
    if response:
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response
        })
        
        # Vérifier si on doit proposer l'outil BPSS
        if any(keyword in message.lower() for keyword in ['bpss', 'outil', 'excel', 'fichier final']):
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': "Souhaitez-vous lancer l'outil BPSS ?",
                'type': 'bpss_prompt'
            })
    
    st.rerun()

async def handle_file_upload(uploaded_file):
    """Gère l'upload d'un fichier"""
    # Sauvegarder temporairement
    temp_path = Path(f"/tmp/{uploaded_file.name}")
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Lire le contenu
    content = services['file_handler'].read_file(str(temp_path), uploaded_file.name)
    
    # Stocker dans la session
    st.session_state.current_file = {
        'name': uploaded_file.name,
        'content': content,
        'path': str(temp_path)
    }
    
    # Ajouter à l'historique
    st.session_state.chat_history.append({
        'role': 'user',
        'content': f"Fichier envoyé : {uploaded_file.name}"
    })
    
    # Obtenir un résumé du bot
    with st.spinner("Analyse du fichier..."):
        messages = st.session_state.chat_history + [
            {
                'role': 'user',
                'content': content
            },
            {
                'role': 'system',
                'content': "L'utilisateur a envoyé un fichier. Propose une synthèse en deux lignes et demande ce qu'il attend de cet envoi."
            }
        ]
        
        response = await services['llm_client'].chat(messages)
    
    if response:
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': response
        })
    
    # Si c'est un fichier Excel, le charger
    if uploaded_file.name.endswith('.xlsx'):
        st.session_state.excel_workbook = services['excel_handler'].load_workbook(temp_path)
    
    # Nettoyer
    temp_path.unlink()
    
    st.rerun()

def render_bpss_tool():
    """Rendu de l'outil BPSS"""
    with st.form("bpss_form"):
        st.number_input("Année", value=2025, min_value=2000, max_value=2100, key="bpss_year")
        st.text_input("Code Ministère", value="38", key="bpss_ministry")
        st.text_input("Code Programme", value="150", key="bpss_program")
        
        st.file_uploader("PP‑E‑S (.xlsx)", type=['xlsx'], key="bpss_ppes")
        st.file_uploader("DPP 18 (.xlsx)", type=['xlsx'], key="bpss_dpp18")
        st.file_uploader("BUD 45 (.xlsx)", type=['xlsx'], key="bpss_bud45")
        
        if st.form_submit_button("✅ Générer", use_container_width=True):
            # Implémenter la logique BPSS
            st.info("Traitement BPSS en cours...")

def render_excel_module():
    """Rendu du module Excel"""
    uploaded_excel = st.file_uploader(
        "📂 Charger un fichier Excel (.xlsx)",
        type=['xlsx'],
        key="excel_upload"
    )
    
    if uploaded_excel:
        # Charger le fichier
        wb = services['excel_handler'].load_workbook_from_bytes(uploaded_excel.getbuffer())
        st.session_state.excel_workbook = wb
        
        # Sélecteur de feuille
        sheets = wb.sheetnames
        selected_sheet = st.selectbox("🗂️ Choisir une feuille", sheets)
        
        # Afficher les données
        if selected_sheet:
            df = services['excel_handler'].sheet_to_dataframe(wb, selected_sheet)
            st.dataframe(df, use_container_width=True)
            
            # Boutons d'action
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🖋️ Appliquer les formules", use_container_width=True):
                    st.info("Application des formules en cours...")
            with col2:
                if st.button("📊 Extraire budget", use_container_width=True):
                    if st.session_state.current_file:
                        asyncio.run(extract_budget_data())
            with col3:
                # Bouton de téléchargement
                if st.button("💾 Exporter", use_container_width=True):
                    output = services['excel_handler'].save_workbook_to_bytes(wb)
                    st.download_button(
                        label="Télécharger Excel",
                        data=output,
                        file_name=f"sortie_budgibot_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

def render_json_helper():
    """Rendu du JSON Helper"""
    uploaded_json = st.file_uploader(
        "📂 Importer un fichier JSON",
        type=['json'],
        key="json_upload"
    )
    
    if uploaded_json:
        import json
        json_data = json.load(uploaded_json)
        st.json(json_data)
        
        if st.button("🔍 Analyser les labels"):
            if 'tags' in json_data:
                labels = services['json_helper'].extract_labels(json_data)
                st.write("Labels extraits:", labels)

async def extract_budget_data():
    """Extrait les données budgétaires du fichier actuel"""
    if not st.session_state.current_file:
        st.error("Aucun fichier chargé")
        return
    
    with st.spinner("Extraction des données budgétaires..."):
        data = await services['budget_extractor'].extract(
            st.session_state.current_file['content'],
            services['llm_client']
        )
    
    if data:
        st.session_state.extracted_data = pd.DataFrame(data)
        st.success(f"{len(data)} entrées budgétaires extraites!")
        
        # Afficher les données
        st.dataframe(st.session_state.extracted_data)
    else:
        st.warning("Aucune donnée budgétaire trouvée")

if __name__ == "__main__":
    main()