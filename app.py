# app.py - Version corrigée avec tous les bugs fixés
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

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Injection des styles et scripts
st.markdown(get_main_styles(), unsafe_allow_html=True)
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
        'show_bpss_tool': False,
        'pending_action': None,
        'json_data': None,
        'parsed_formulas': None,
        'excel_script': None,
        'message_input_key': 0,
        'scroll_to_bottom': False,
        'processed_files': set(),  # Pour éviter les doublons
        'temp_files': []  # Pour nettoyer les fichiers temporaires
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

# Gestionnaires d'événements
async def handle_message_send(message: str):
    """Gère l'envoi d'un message"""
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
    """Traite le message de manière asynchrone"""
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
            if any(keyword in last_message.lower() for keyword in ['bpss', 'outil', 'excel', 'fichier final']):
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': "Souhaitez-vous lancer l'outil BPSS ?",
                    'type': 'bpss_prompt',
                    'timestamp': datetime.now().strftime("%H:%M")
                })
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi du message: {str(e)}")
        st.error("Une erreur s'est produite lors de l'envoi du message.")
    
    st.session_state.is_typing = False
    st.rerun()

async def handle_file_upload(uploaded_file):
    """Gère l'upload d'un fichier - VERSION CORRIGÉE"""
    # Créer une clé unique pour le fichier
    file_key = f"{uploaded_file.name}_{uploaded_file.size}"
    
    if file_key in st.session_state.processed_files:
        return  # Fichier déjà traité
    
    st.session_state.processed_files.add(file_key)
    
    # Notifier l'upload
    st.session_state.chat_history.append({
        'role': 'user',
        'content': f"📎 Fichier envoyé : {uploaded_file.name}",
        'timestamp': datetime.now().strftime("%H:%M"),
        'file_name': uploaded_file.name,
        'file_key': file_key
    })
    
    st.session_state.is_typing = True
    st.session_state.scroll_to_bottom = True
    st.rerun()

async def process_file(uploaded_file):
    """Traite le fichier de manière asynchrone - VERSION CORRIGÉE"""
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
                'raw_bytes': file_content
            }
            
            # Ajouter dans l'historique
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
            
            elif uploaded_file.name.endswith('.json'):
                import json
                st.session_state.json_data = json.loads(content)
            
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
        
    except Exception as e:
        logger.error(f"Erreur lors de l'upload du fichier: {str(e)}")
        st.error(f"Erreur lors du traitement du fichier: {str(e)}")
    finally:
        st.session_state.is_typing = False
        st.session_state.scroll_to_bottom = True
    
    st.rerun()

def handle_tool_action(action: dict):
    """Gère les actions des outils"""
    action_type = action.get('action')
    
    if action_type == 'clear_history':
        st.session_state.chat_history = []
        st.session_state.processed_files = set()
        cleanup_temp_files()
        st.success("Historique effacé")
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
        st.success(f"Analyse terminée : {len(labels)} labels trouvés")
    
    elif action_type == 'parse_excel':
        parse_excel_formulas()
    
    elif action_type == 'export_excel':
        export_excel()

async def process_bpss(data: dict):
    """Traite les fichiers BPSS"""
    with st.spinner("Traitement BPSS en cours..."):
        temp_files = []
        try:
            # Sauvegarder temporairement les fichiers
            temp_paths = {}
            for key, file in data['files'].items():
                with temporary_file(file.getbuffer(), suffix='.xlsx') as temp_path:
                    temp_paths[key] = temp_path
                    
                    # Traiter avec l'outil BPSS
                    result_wb = services['bpss_tool'].process_files(
                        ppes_path=temp_paths.get('ppes'),
                        dpp18_path=temp_paths.get('dpp18'),
                        bud45_path=temp_paths.get('bud45'),
                        year=data['year'],
                        ministry_code=data['ministry'],
                        program_code=data['program'],
                        target_workbook=st.session_state.excel_workbook or openpyxl.Workbook()
                    )
            
            st.session_state.excel_workbook = result_wb
            st.success("✅ Traitement BPSS terminé!")
                
        except Exception as e:
            st.error(f"Erreur BPSS: {str(e)}")

async def extract_budget_data():
    """Extrait les données budgétaires - VERSION CORRIGÉE"""
    content = None
    file_name = None
    
    # Méthode 1: current_file
    if st.session_state.get('current_file') and st.session_state.current_file.get('content'):
        content = st.session_state.current_file['content']
        file_name = st.session_state.current_file.get('name', 'fichier')
        logger.info(f"Contenu trouvé dans current_file: {len(content)} caractères")
    
    # Méthode 2: Chercher dans l'historique
    if not content:
        for msg in reversed(st.session_state.chat_history):
            if msg.get('meta') == 'file_content':
                content = msg['content']
                file_name = msg.get('file_name', 'fichier')
                logger.info(f"Contenu trouvé dans l'historique: {len(content)} caractères")
                break
    
    # Méthode 3: Dernier message utilisateur
    if not content:
        for msg in reversed(st.session_state.chat_history):
            if msg.get('role') == 'user' and not msg['content'].startswith('📎'):
                content = msg['content']
                file_name = "message"
                logger.info(f"Utilisation du dernier message: {len(content)} caractères")
                break
    
    if not content:
        st.error("Aucun fichier ou texte chargé pour l'extraction. Veuillez d'abord envoyer un fichier ou un message contenant des données budgétaires.")
        return
    
    with st.spinner("Extraction en cours..."):
        try:
            # Limiter la taille
            max_content_length = 10000
            content_to_process = content
            if len(content) > max_content_length:
                logger.warning(f"Contenu tronqué de {len(content)} à {max_content_length} caractères")
                content_to_process = content[:max_content_length] + "\n\n[... contenu tronqué ...]"
            
            data = await services['budget_extractor'].extract(
                content_to_process,
                services['llm_client']
            )
            
            if data:
                st.session_state.extracted_data = data
                st.success(f"✅ {len(data)} entrées budgétaires extraites de '{file_name}'!")
                
                # Afficher les données
                show_budget_data_modal(data)
            else:
                st.warning("Aucune donnée budgétaire trouvée dans le contenu.")
                
        except Exception as e:
            logger.error(f"Erreur extraction: {str(e)}")
            st.error(f"Erreur lors de l'extraction: {str(e)}")

def show_budget_data_modal(data):
    """Affiche les données budgétaires extraites"""
    with st.expander("📊 Données budgétaires extraites", expanded=True):
        df = pd.DataFrame(data)
        
        # Édition des données
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            key="budget_data_editor"
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💾 Sauvegarder", type="primary"):
                st.session_state.extracted_data = edited_df.to_dict('records')
                st.success("Données sauvegardées")
        
        with col2:
            if st.button("🎯 Mapper les cellules"):
                if st.session_state.json_data:
                    asyncio.run(map_budget_to_cells())
                else:
                    st.warning("Chargez d'abord un fichier JSON de configuration")
        
        with col3:
            if st.button("📥 Exporter CSV"):
                csv = edited_df.to_csv(index=False)
                st.download_button(
                    label="Télécharger CSV",
                    data=csv,
                    file_name=f"budget_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

async def map_budget_to_cells():
    """Mappe les données budgétaires aux cellules Excel - IMPLÉMENTATION COMPLÈTE"""
    if not st.session_state.extracted_data or not st.session_state.json_data:
        st.error("Données manquantes pour le mapping")
        return
    
    with st.spinner("Mapping en cours..."):
        try:
            mapper = BudgetMapper(services['llm_client'])
            tags = services['json_helper'].get_tags_for_mapping(st.session_state.json_data)
            
            # Convertir en DataFrame si nécessaire
            if isinstance(st.session_state.extracted_data, list):
                entries_df = pd.DataFrame(st.session_state.extracted_data)
            else:
                entries_df = st.session_state.extracted_data
            
            # Mapper
            mapping = await mapper.map_entries_to_cells(
                st.session_state.extracted_data,
                tags
            )
            
            if mapping:
                st.info(f"📍 {len(mapping)} mappings trouvés")
                
                # Afficher le mapping
                with st.expander("🗺️ Aperçu du mapping", expanded=True):
                    mapping_df = pd.DataFrame(mapping)
                    st.dataframe(mapping_df, use_container_width=True)
                
                # Appliquer au workbook si disponible
                if st.session_state.excel_workbook:
                    success, errors = mapper.apply_mapping_to_excel(
                        st.session_state.excel_workbook,
                        mapping,
                        entries_df
                    )
                    
                    if success > 0:
                        st.success(f"✅ {success} cellules mises à jour dans Excel")
                    if errors:
                        with st.expander("❌ Erreurs", expanded=False):
                            for error in errors:
                                st.error(error)
                else:
                    st.warning("Aucun fichier Excel chargé pour appliquer le mapping")
                    
        except Exception as e:
            logger.error(f"Erreur mapping: {str(e)}")
            st.error(f"Erreur lors du mapping: {str(e)}")

def parse_excel_formulas():
    """Parse les formules Excel"""
    if not st.session_state.excel_workbook or not st.session_state.current_file:
        st.error("Aucun fichier Excel chargé")
        return
    
    with st.spinner("Analyse des formules en cours..."):
        try:
            # Sauver temporairement le fichier
            with temporary_file(st.session_state.current_file.get('raw_bytes', b''), suffix='.xlsx') as temp_path:
                parser = ExcelFormulaParser()
                result = parser.parse_excel_file(temp_path, emit_script=True)
                
                st.session_state.parsed_formulas = result
                st.session_state.excel_script = result.get('script_file')
                
                stats = result['statistics']
                st.success(f"✅ Parsing terminé: {stats['success']}/{stats['total']} formules converties ({stats['success_rate']}%)")
                
                # Afficher les formules
                if result['formulas']:
                    with st.expander("📝 Formules converties", expanded=False):
                        for formula in result['formulas'][:10]:  # Limiter à 10
                            if formula.r_code and not formula.r_code.startswith('#'):
                                st.code(f"{formula.sheet}!{formula.address}: {formula.formula}\n→ {formula.r_code}", language='python')
            
        except Exception as e:
            logger.error(f"Erreur parsing: {str(e)}")
            st.error(f"Erreur parsing: {str(e)}")

def apply_excel_formulas():
    """Applique les formules Excel parsées"""
    if not st.session_state.parsed_formulas:
        st.warning("Parsez d'abord les formules Excel")
        return
    
    with st.spinner("Application des formules..."):
        try:
            # TODO: Implémenter l'application des formules
            st.info("Application des formules en cours de développement...")
        except Exception as e:
            st.error(f"Erreur application: {str(e)}")

def export_excel():
    """Exporte le fichier Excel modifié"""
    if not st.session_state.excel_workbook:
        st.error("Aucun fichier Excel à exporter")
        return
    
    output = services['excel_handler'].save_workbook_to_bytes(st.session_state.excel_workbook)
    
    st.download_button(
        label="📥 Télécharger Excel modifié",
        data=output,
        file_name=f"budgibot_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def inject_scroll_script():
    """Injecte le script pour scroll automatique"""
    if st.session_state.get('scroll_to_bottom', False):
        st.markdown("""
        <script>
        // Scroll amélioré
        function scrollToBottom() {
            const containers = document.querySelectorAll('[data-testid="stVerticalBlock"] > div');
            containers.forEach(container => {
                if (container.style.height === '500px' || 
                    window.getComputedStyle(container).height === '500px') {
                    container.scrollTop = container.scrollHeight;
                }
            });
        }
        scrollToBottom();
        setTimeout(scrollToBottom, 100);
        setTimeout(scrollToBottom, 300);
        </script>
        """, unsafe_allow_html=True)
        
        st.session_state.scroll_to_bottom = False

def main():
    """Fonction principale - VERSION CORRIGÉE"""
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
                for key in ['file_upload', 'file_upload_chat']:
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
    
    # Créer le layout
    layout = MainLayout(services)
    
    # Rendre l'interface
    layout.render(
        on_message_send=lambda msg: asyncio.run(handle_message_send(msg)),
        on_file_upload=lambda file: asyncio.run(handle_file_upload(file)),
        on_tool_action=handle_tool_action
    )
    
    # Injecter le script de scroll
    inject_scroll_script()

if __name__ == "__main__":
    main()