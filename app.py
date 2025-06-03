# app.py - Updated for modern UI
import streamlit as st
import asyncio
from pathlib import Path
from datetime import datetime
import logging
import openpyxl
import tempfile
import contextlib
import os
import pandas as pd
from modules.excel_parser.parser_v3 import ExcelFormulaParser, ParserConfig
from modules.budget_mapper import BudgetMapper

# Configuration de la page - Wide layout for better Excel display
st.set_page_config(
    page_title="BudgiBot - Assistant Budgétaire Intelligent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",  # Start with collapsed sidebar for cleaner look
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "BudgiBot - Assistant Budgétaire Intelligent v2.0"
    }
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

# Import des composants UI avec les nouveaux styles
from ui import get_main_styles, get_javascript, MainLayout
from ui.styles_additions import get_additional_styles

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Injection des styles et scripts - Combined modern styles
st.markdown(get_main_styles(), unsafe_allow_html=True)
st.markdown(get_additional_styles(), unsafe_allow_html=True)
st.markdown(get_javascript(), unsafe_allow_html=True)

# Context manager pour fichiers temporaires
@contextlib.contextmanager
def temporary_file(content, suffix=''):
    """Context manager pour fichiers temporaires"""
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, 'wb') as f:
            if isinstance(content, bytes):
                f.write(content)
            else:
                f.write(content.encode() if hasattr(content, 'encode') else bytes(content))
        yield path
    finally:
        try:
            os.unlink(path)
        except:
            pass

# Initialisation des services
@st.cache_resource
def init_services():
    services = {
        'llm_client': MistralClient(),
        'file_handler': FileHandler(),
        'chat_handler': ChatHandler(),
        'excel_handler': ExcelHandler(),
        'budget_extractor': BudgetExtractor(),
        'bpss_tool': BPSSTool(),
        'json_helper': JSONHelper(),
        'budget_mapper': BudgetMapper(MistralClient())  # Add budget mapper
    }
    
    # Register cleanup for Excel handler
    import atexit
    atexit.register(lambda: services['excel_handler'].cleanup_temp_files())
    
    return services

services = init_services()

def init_session_state():
    """Initialise l'état de session avec les nouvelles variables"""
    defaults = {
        'chat_history': [],
        'current_file': None,
        'excel_workbook': None,
        'extracted_data': None,
        'is_typing': False,
        'bpss_response': None,
        'show_bpss_tool': False,
        'pending_action': None,
        'json_data': None,
        'parsed_formulas': None,
        'excel_script': None,
        'message_input_key': 0,
        'scroll_to_bottom': False,
        'processed_files': set(),
        'temp_files': [],
        'layout_mode': 'split',  # New: layout mode
        'excel_tab': 'data',     # New: active Excel tab
        'theme': 'light',        # New: theme preference
        'show_welcome': True     # New: show welcome message
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# Nettoyage des fichiers temporaires
def cleanup_temp_files():
    """Nettoie les fichiers temporaires"""
    for temp_file in st.session_state.get('temp_files', []):
        try:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        except:
            pass
    st.session_state.temp_files = []

# Gestionnaires d'événements améliorés
async def handle_message_send(message: str):
    """Gère l'envoi d'un message avec animation"""
    # Hide welcome message
    st.session_state.show_welcome = False
    
    # Ajouter à l'historique
    st.session_state.chat_history.append({
        'role': 'user',
        'content': message,
        'timestamp': datetime.now().strftime("%H:%M")
    })
    
    # Incrémenter la clé pour forcer un nouveau widget vide
    st.session_state.message_input_key += 1
    
    # Activer l'indicateur de frappe
    st.session_state.is_typing = True
    
    # Forcer le scroll vers le bas
    st.session_state.scroll_to_bottom = True
    
    st.rerun()

async def process_message():
    """Traite le message de manière asynchrone avec gestion d'erreur améliorée"""
    try:
        # Obtenir la réponse
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
            last_message = st.session_state.chat_history[-2]['content']
            keywords = ['bpss', 'outil', 'excel', 'fichier final', 'mesures catégorielles']
            if any(keyword in last_message.lower() for keyword in keywords):
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': "Je détecte que vous avez besoin de l'outil BPSS. Souhaitez-vous que je le lance pour vous ?",
                    'type': 'bpss_prompt',
                    'timestamp': datetime.now().strftime("%H:%M")
                })
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du message: {str(e)}")
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': "Désolé, une erreur s'est produite. Pouvez-vous reformuler votre question ?",
            'timestamp': datetime.now().strftime("%H:%M"),
            'error': True
        })
    
    st.session_state.is_typing = False
    st.rerun()

async def handle_file_upload(uploaded_file):
    """Gère l'upload d'un fichier avec feedback visuel amélioré"""
    # Hide welcome message
    st.session_state.show_welcome = False
    
    # Créer une clé unique pour le fichier
    file_key = f"{uploaded_file.name}_{uploaded_file.size}"
    
    if file_key in st.session_state.processed_files:
        return  # Fichier déjà traité
    
    st.session_state.processed_files.add(file_key)
    
    # Notifier l'upload avec style
    st.session_state.chat_history.append({
        'role': 'user',
        'content': f"📎 Fichier envoyé : {uploaded_file.name}",
        'timestamp': datetime.now().strftime("%H:%M"),
        'file_name': uploaded_file.name,
        'file_size': uploaded_file.size,
        'file_key': file_key
    })
    
    st.session_state.is_typing = True
    st.session_state.scroll_to_bottom = True
    st.rerun()

async def process_file(uploaded_file):
    """Traite le fichier avec extraction intelligente"""
    try:
        # Utiliser le context manager pour fichier temporaire
        file_content = uploaded_file.getbuffer()
        suffix = Path(uploaded_file.name).suffix
        
        with temporary_file(file_content, suffix=suffix) as temp_path:
            # Lire le contenu
            content = services['file_handler'].read_file(temp_path, uploaded_file.name)
            
            # Stocker le contenu
            st.session_state.current_file = {
                'name': uploaded_file.name,
                'content': content,
                'path': temp_path,
                'type': uploaded_file.name.split('.')[-1].lower(),
                'raw_bytes': file_content,
                'size': uploaded_file.size
            }
            
            # Ajouter dans l'historique (caché)
            st.session_state.chat_history.append({
                'role': 'system',
                'content': content,
                'meta': 'file_content',
                'file_name': uploaded_file.name,
                'timestamp': datetime.now().strftime("%H:%M")
            })
            
            # Traitement spécifique selon le type
            if uploaded_file.name.endswith('.xlsx'):
                st.session_state.excel_workbook = services['excel_handler'].load_workbook_from_bytes(
                    file_content
                )
                # Auto-switch to split view for Excel files
                st.session_state.layout_mode = 'split'
            
            elif uploaded_file.name.endswith('.json'):
                import json
                st.session_state.json_data = json.loads(content)
            
            # Obtenir un résumé intelligent
            summary_prompt = [
                {'role': 'user', 'content': f"Fichier: {uploaded_file.name}\n\nContenu (extrait):\n{content[:2000]}"},
                {'role': 'system', 'content': "Fais un résumé en 2-3 lignes et suggère des actions possibles."}
            ]
            
            response = await services['llm_client'].chat(summary_prompt)
            
            if response:
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': response,
                    'timestamp': datetime.now().strftime("%H:%M")
                })
        
    except Exception as e:
        logger.error(f"Erreur lors de l'upload du fichier: {str(e)}")
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': f"❌ Erreur lors du traitement du fichier: {str(e)}",
            'timestamp': datetime.now().strftime("%H:%M"),
            'error': True
        })
    finally:
        st.session_state.is_typing = False
        st.session_state.scroll_to_bottom = True
    
    st.rerun()

def handle_tool_action(action: dict):
    """Gère les actions des outils avec feedback amélioré"""
    action_type = action.get('action')
    
    # Show loading state
    with st.spinner(f"Traitement en cours: {action_type}..."):
        if action_type == 'clear_history':
            st.session_state.chat_history = []
            st.session_state.processed_files = set()
            st.session_state.show_welcome = True
            cleanup_temp_files()
            st.success("✨ Conversation réinitialisée")
            st.rerun()
        
        elif action_type == 'process_bpss':
            asyncio.run(process_bpss(action.get('data')))
        
        elif action_type == 'apply_formulas':
            apply_excel_formulas()
        
        elif action_type == 'extract_budget':
            asyncio.run(extract_budget_data())
        
        elif action_type == 'analyze_labels':
            data = action.get('data')
            labels = services['json_helper'].extract_labels(data)
            st.success(f"✅ Analyse terminée : {len(labels)} labels trouvés")
        
        elif action_type == 'parse_excel':
            parse_excel_formulas()
        
        elif action_type == 'export_excel':
            export_excel()
        
        elif action_type == 'map_budget_cells':
            asyncio.run(map_budget_to_cells())

async def process_bpss(data: dict):
    """Traite les fichiers BPSS avec feedback détaillé"""
    try:
        # Progress tracking
        progress_bar = st.progress(0, text="Initialisation BPSS...")
        
        temp_paths = {}
        files_info = data['files']
        
        # Save files temporarily
        progress_bar.progress(25, text="Sauvegarde des fichiers...")
        for idx, (key, file) in enumerate(files_info.items()):
            with temporary_file(file.getbuffer(), suffix='.xlsx') as temp_path:
                temp_paths[key] = temp_path
        
        # Process with BPSS tool
        progress_bar.progress(50, text="Traitement des données BPSS...")
        result_wb = services['bpss_tool'].process_files(
            ppes_path=temp_paths.get('ppes'),
            dpp18_path=temp_paths.get('dpp18'),
            bud45_path=temp_paths.get('bud45'),
            year=data['year'],
            ministry_code=data['ministry'],
            program_code=data['program'],
            target_workbook=st.session_state.excel_workbook or openpyxl.Workbook()
        )
        
        progress_bar.progress(90, text="Finalisation...")
        st.session_state.excel_workbook = result_wb
        
        progress_bar.progress(100, text="Terminé!")
        st.success("✅ Traitement BPSS terminé avec succès!")
        
        # Add to chat history
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': f"✅ J'ai terminé le traitement BPSS pour l'année {data['year']}, "
                      f"ministère {data['ministry']}, programme {data['program']}. "
                      f"Les données ont été intégrées dans votre fichier Excel.",
            'timestamp': datetime.now().strftime("%H:%M")
        })
        
    except Exception as e:
        st.error(f"❌ Erreur BPSS: {str(e)}")
        logger.error(f"Erreur BPSS détaillée: {str(e)}")

async def extract_budget_data():
    """Extrait les données budgétaires avec UI améliorée"""
    content = None
    file_name = None
    
    # Find content to extract
    if st.session_state.get('current_file') and st.session_state.current_file.get('content'):
        content = st.session_state.current_file['content']
        file_name = st.session_state.current_file.get('name', 'fichier')
    else:
        # Look in history
        for msg in reversed(st.session_state.chat_history):
            if msg.get('meta') == 'file_content':
                content = msg['content']
                file_name = msg.get('file_name', 'fichier')
                break
    
    if not content:
        st.error("❌ Aucun fichier chargé pour l'extraction")
        return
    
    # Progress tracking
    progress_bar = st.progress(0, text="Analyse du contenu...")
    
    try:
        # Limit content size
        max_content_length = 10000
        content_to_process = content
        if len(content) > max_content_length:
            content_to_process = content[:max_content_length] + "\n\n[... contenu tronqué ...]"
        
        progress_bar.progress(50, text="Extraction des données budgétaires...")
        
        data = await services['budget_extractor'].extract(
            content_to_process,
            services['llm_client']
        )
        
        progress_bar.progress(100, text="Extraction terminée!")
        
        if data:
            st.session_state.extracted_data = data
            st.success(f"✅ {len(data)} entrées budgétaires extraites!")
            
            # Add to chat
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': f"✅ J'ai extrait {len(data)} entrées budgétaires du fichier '{file_name}'. "
                          f"Vous pouvez maintenant les visualiser et les éditer dans l'onglet 'Extraction & Analyse'.",
                'timestamp': datetime.now().strftime("%H:%M")
            })
            
            # Switch to analysis tab - but keep it in the split view
            st.session_state.excel_tab = 'analysis'
            # Keep split view to see both Excel and extraction
            st.session_state.layout_mode = 'split'
        else:
            st.warning("⚠️ Aucune donnée budgétaire trouvée")
            
    except Exception as e:
        logger.error(f"Erreur extraction: {str(e)}")
        st.error(f"❌ Erreur: {str(e)}")

async def map_budget_to_cells():
    """Mappe les données budgétaires avec visualisation"""
    if not st.session_state.extracted_data or not st.session_state.json_data:
        st.error("❌ Données manquantes pour le mapping")
        return
    
    progress_bar = st.progress(0, text="Préparation du mapping...")
    
    try:
        mapper = services['budget_mapper']
        tags = services['json_helper'].get_tags_for_mapping(st.session_state.json_data)
        
        progress_bar.progress(33, text="Analyse des correspondances...")
        
        # Convert to DataFrame if needed
        if isinstance(st.session_state.extracted_data, list):
            entries_df = pd.DataFrame(st.session_state.extracted_data)
        else:
            entries_df = st.session_state.extracted_data
        
        # Map entries to cells
        progress_bar.progress(66, text="Mapping intelligent en cours...")
        
        mapping = await mapper.map_entries_to_cells(
            st.session_state.extracted_data,
            tags
        )
        
        if mapping:
            progress_bar.progress(100, text="Mapping terminé!")
            st.success(f"✅ {len(mapping)} correspondances trouvées")
            
            # Apply to workbook
            if st.session_state.excel_workbook:
                success, errors = mapper.apply_mapping_to_excel(
                    st.session_state.excel_workbook,
                    mapping,
                    entries_df
                )
                
                if success > 0:
                    st.success(f"✅ {success} cellules mises à jour")
                if errors:
                    with st.expander("⚠️ Erreurs rencontrées"):
                        for error in errors:
                            st.warning(error)
        else:
            st.warning("⚠️ Aucun mapping trouvé")
            
    except Exception as e:
        logger.error(f"Erreur mapping: {str(e)}")
        st.error(f"❌ Erreur: {str(e)}")

def parse_excel_formulas():
    """Parse les formules Excel avec visualisation détaillée"""
    if not st.session_state.excel_workbook or not st.session_state.current_file:
        st.error("❌ Aucun fichier Excel chargé")
        return
    
    progress_bar = st.progress(0, text="Analyse des formules Excel...")
    
    try:
        # Save file temporarily
        with temporary_file(st.session_state.current_file.get('raw_bytes', b''), suffix='.xlsx') as temp_path:
            progress_bar.progress(50, text="Parsing des formules...")
            
            parser = ExcelFormulaParser()
            result = parser.parse_excel_file(temp_path, emit_script=True)
            
            st.session_state.parsed_formulas = result
            st.session_state.excel_script = result.get('script_file')
            
            progress_bar.progress(100, text="Analyse terminée!")
            
            stats = result['statistics']
            st.success(f"✅ {stats['success']}/{stats['total']} formules converties ({stats['success_rate']}%)")
            
            # Switch to formulas tab
            st.session_state.excel_tab = 'formulas'
            
    except Exception as e:
        logger.error(f"Erreur parsing: {str(e)}")
        st.error(f"❌ Erreur: {str(e)}")

def export_excel():
    """Exporte le fichier Excel avec nom intelligent"""
    if not st.session_state.excel_workbook:
        st.error("❌ Aucun fichier Excel à exporter")
        return
    
    output = services['excel_handler'].save_workbook_to_bytes(st.session_state.excel_workbook)
    
    # Generate intelligent filename
    base_name = "budgibot_export"
    if st.session_state.current_file:
        base_name = Path(st.session_state.current_file['name']).stem + "_processed"
    
    filename = f"{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    st.download_button(
        label="📥 Télécharger Excel",
        data=output,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

def main():
    """Fonction principale avec UI moderne"""
    # Initialiser l'état
    init_session_state()
    
    # Nettoyer au démarrage
    if 'startup_cleanup' not in st.session_state:
        cleanup_temp_files()
        st.session_state.startup_cleanup = True
    
    # Gérer les messages en attente
    if st.session_state.is_typing and len(st.session_state.chat_history) > 0:
        last_msg = st.session_state.chat_history[-1]
        if last_msg['role'] == 'user' and not last_msg['content'].startswith("📎"):
            # Message texte à traiter
            asyncio.run(process_message())
        elif last_msg['role'] == 'user' and last_msg['content'].startswith("📎"):
            # Fichier à traiter
            file_key = last_msg.get('file_key')
            if file_key:
                # Chercher le fichier
                for key in ['file_upload_drop', 'file_upload_chat_modern']:
                    file_to_process = st.session_state.get(key)
                    if file_to_process:
                        current_file_key = f"{file_to_process.name}_{file_to_process.size}"
                        if current_file_key == file_key:
                            asyncio.run(process_file(file_to_process))
                            break
    
    # Gérer les actions en attente
    if st.session_state.get('pending_action'):
        action = st.session_state.pending_action
        st.session_state.pending_action = None
        
        if action['type'] == 'extract_budget':
            asyncio.run(extract_budget_data())
    
    # Créer le layout moderne
    layout = MainLayout(services)
    
    # Rendre l'interface
    layout.render(
        on_message_send=lambda msg: asyncio.run(handle_message_send(msg)),
        on_file_upload=lambda file: asyncio.run(handle_file_upload(file)),
        on_tool_action=handle_tool_action
    )

if __name__ == "__main__":
    main()