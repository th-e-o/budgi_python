# app.py
import streamlit as st
import asyncio
from pathlib import Path
from datetime import datetime
import logging

# Configuration de la page
st.set_page_config(
    page_title="BudgiBot - Assistant Budgétaire",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import des modules
from core.llm_client import MistralClient
from core.file_handler import FileHandler
from core.chat_handler import ChatHandler
from core.excel_handler import ExcelHandler
from modules.budget_extractor import BudgetExtractor
from modules.bpss_tool import BPSSTool
from modules.json_helper import JSONHelper
from config import config

# Import des composants UI
from ui import get_main_styles, get_javascript, MainLayout

# Injection des styles et scripts
st.markdown(get_main_styles(), unsafe_allow_html=True)
st.markdown(get_javascript(), unsafe_allow_html=True)

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

def init_session_state():
    """Initialise l'état de session"""
    defaults = {
        'chat_history': [],
        'current_file': None,
        'excel_workbook': None,
        'extracted_data': None,
        'is_typing': False,
        'bpss_response': None,
        'show_bpss_tool': False,  # Pour ouvrir l'outil BPSS
        'pending_action': None    # Pour les actions en attente
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# Gestionnaires d'événements
async def handle_message_send(message: str):
    """Gère l'envoi d'un message"""
    # Ajouter à l'historique
    st.session_state.chat_history.append({
        'role': 'user',
        'content': message,
        'timestamp': datetime.now().strftime("%H:%M")
    })
    
    # Activer l'indicateur de frappe
    st.session_state.is_typing = True
    st.rerun()
    
    # Obtenir la réponse
    try:
        response = await services['llm_client'].chat(
            services['chat_handler'].filter_messages_for_api(st.session_state.chat_history)
        )
        
        if response:
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now().strftime("%H:%M")
            })
            
            # Vérifier si on doit proposer l'outil BPSS
            if any(keyword in message.lower() for keyword in ['bpss', 'outil', 'excel', 'fichier final']):
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': "Souhaitez-vous lancer l'outil BPSS ?",
                    'type': 'bpss_prompt',
                    'timestamp': datetime.now().strftime("%H:%M")
                })
    except Exception as e:
        logging.error(f"Erreur lors de l'envoi du message: {str(e)}")
        st.error("Une erreur s'est produite lors de l'envoi du message.")
    
    st.session_state.is_typing = False
    st.rerun()

async def handle_file_upload(uploaded_file):
    """Gère l'upload d'un fichier"""
    # Notifier l'upload
    st.session_state.chat_history.append({
        'role': 'user',
        'content': f"📎 Fichier envoyé : {uploaded_file.name}",
        'timestamp': datetime.now().strftime("%H:%M")
    })
    
    st.session_state.is_typing = True
    st.rerun()
    
    try:
        # Traiter le fichier
        temp_path = Path(f"/tmp/{uploaded_file.name}")
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        content = services['file_handler'].read_file(str(temp_path), uploaded_file.name)
        
        st.session_state.current_file = {
            'name': uploaded_file.name,
            'content': content,
            'path': str(temp_path)
        }
        
        # Si c'est un Excel, le charger
        if uploaded_file.name.endswith('.xlsx'):
            st.session_state.excel_workbook = services['excel_handler'].load_workbook_from_bytes(
                uploaded_file.getbuffer()
            )
        
        # Obtenir un résumé
        summary_prompt = [
            {'role': 'user', 'content': content[:2000]},
            {'role': 'system', 'content': "Résume ce fichier en 2-3 lignes et demande ce que l'utilisateur souhaite en faire."}
        ]
        
        response = await services['llm_client'].chat(summary_prompt)
        
        if response:
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now().strftime("%H:%M")
            })
        
        # Nettoyer
        temp_path.unlink(missing_ok=True)
        
    except Exception as e:
        logging.error(f"Erreur lors de l'upload du fichier: {str(e)}")
        st.error(f"Erreur lors du traitement du fichier: {str(e)}")
    
    st.session_state.is_typing = False
    st.rerun()

def handle_tool_action(action: dict):
    """Gère les actions des outils"""
    action_type = action.get('action')
    
    if action_type == 'clear_history':
        st.session_state.chat_history = []
        st.success("Historique effacé")
        st.rerun()
    
    elif action_type == 'process_bpss':
        with st.spinner("Traitement BPSS en cours..."):
            # Implémenter la logique BPSS
            st.success("Traitement BPSS terminé!")
    
    elif action_type == 'apply_formulas':
        with st.spinner("Application des formules..."):
            # Implémenter l'application des formules
            st.info("Formules appliquées")
    
    elif action_type == 'extract_budget':
        asyncio.run(extract_budget_data())
    
    elif action_type == 'analyze_labels':
        data = action.get('data')
        labels = services['json_helper'].extract_labels(data)
        st.success(f"Analyse terminée : {len(labels)} labels trouvés")
    
    # Autres actions...

async def extract_budget_data():
    """Extrait les données budgétaires"""
    if not st.session_state.current_file:
        st.error("Aucun fichier chargé")
        return
    
    with st.spinner("Extraction en cours..."):
        try:
            data = await services['budget_extractor'].extract(
                st.session_state.current_file['content'],
                services['llm_client']
            )
            
            if data:
                st.session_state.extracted_data = data
                st.success(f"{len(data)} entrées extraites!")
            else:
                st.warning("Aucune donnée trouvée")
                
        except Exception as e:
            st.error(f"Erreur extraction: {str(e)}")

def main():
    # Initialiser l'état
    init_session_state()
    
    # Gérer les actions en attente
    if st.session_state.pending_action:
        action = st.session_state.pending_action
        st.session_state.pending_action = None
        
        if action['type'] == 'extract_budget':
            # Obtenir le message utilisateur correspondant
            if st.session_state.current_file:
                asyncio.run(extract_budget_data())
            else:
                st.warning("Aucun fichier chargé pour l'extraction")
    
    # Créer le layout
    layout = MainLayout(services)
    
    # Rendre l'interface
    layout.render(
        on_message_send=lambda msg: asyncio.run(handle_message_send(msg)),
        on_file_upload=lambda file: asyncio.run(handle_file_upload(file)),
        on_tool_action=handle_tool_action
    )
if __name__ == "__main__":
    main()