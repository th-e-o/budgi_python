# app.py - Simplified version with welcome message
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
from modules.excel_parser.parser_v3 import ExcelFormulaParser, ParserConfig, FormulaCell
from modules.budget_mapper import BudgetMapper
from modules.pdf_to_word_converter import PDFToWordConverter
from typing import List

# Configuration de la page
st.set_page_config(
    page_title="BudgiBot - Assistant Budgétaire",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed",  # Pas de sidebar
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
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

# Import des composants UI
from ui import get_main_styles, get_javascript, MainLayout

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Injection des styles CSS et JavaScript
st.markdown(get_main_styles(), unsafe_allow_html=True)
st.markdown(get_javascript(), unsafe_allow_html=True)
# CSS additionnel pour forcer la suppression des marges Streamlit
st.markdown("""
<style>
    /* Force removal of Streamlit default spacing */
    .main > div {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* Remove header space */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* Block container */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        max-width: 100% !important;
    }
    
    /* First element fix */
    .element-container:first-child {
        margin-top: 0 !important;
    }
    
    /* Hide Streamlit menu */
    button[kind="header"] {
        display: none !important;
    }
    
    /* App container */
    .stApp {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Remove excessive gaps */
    div[data-testid="stVerticalBlock"] > div:not([style*="height"]) {
        gap: 0.5rem !important;
    }
    
    /* Container height fix */
    div[data-testid="stVerticalBlock"] > div[style*="height"] {
        overflow-y: auto !important;
    }
</style>
""", unsafe_allow_html=True)

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
    """Initialise tous les services nécessaires"""
    services = {
        'llm_client': MistralClient(),
        'file_handler': FileHandler(),
        'chat_handler': ChatHandler(),
        'excel_handler': ExcelHandler(),
        'budget_extractor': BudgetExtractor(),
        'bpss_tool': BPSSTool(),
        'json_helper': JSONHelper(),
        'budget_mapper': BudgetMapper(MistralClient()), 
        'pdf_converter': PDFToWordConverter(),
    }
    
    # Nettoyage automatique des fichiers temporaires
    import atexit
    atexit.register(lambda: services['excel_handler'].cleanup_temp_files())
    
    return services

# Message de bienvenue
WELCOME_MESSAGE = """Bonjour, 
je peux vous aider à :
• **Analyser vos fichiers Excel** - Chargez un fichier .xlsx pour commencer
• **Extraire des données budgétaires** - À partir de PDF, Word, emails ou textes
• **Utiliser l'outil BPSS** - Pour traiter vos fichiers PP-E-S, DPP18 et BUD45
• **Convertir vos fichiers pdf en word** - À partir d'un fichier glissé-déposé
"""

def init_session_state():
    """Initialise l'état de session"""
    defaults = {
        'chat_history': [],
        'current_file': None,
        'excel_workbook': None,
        'extracted_data': None,
        'is_typing': False,
        'pending_action': None,
        'json_data': None,
        'parsed_formulas': None,
        'message_input_key': 0,
        'processed_files': set(),
        'temp_files': [],
        'layout_mode': 'chat',
        'mapping_report': None,  
        'excel_tab': 'data',  # Ajouter pour gérer l'onglet actif
        'pending_mapping': None,       # Mapping en attente de validation
        'mapping_validated': False,    # Flag indiquant si le mapping a été appliqué
        'is_pdf_loaded': False,
        'converted_docx': None,
        'pdf_convert_preserve_layout': True,
    }
    
    # Initialiser les valeurs par défaut
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value
    
    # Ajouter le message de bienvenue si première fois
    if not st.session_state.chat_history:
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': WELCOME_MESSAGE,
            'timestamp': datetime.now().strftime("%H:%M"),
            'type': 'welcome'
        })

def cleanup_temp_files():
    """Nettoie les fichiers temporaires"""
    for temp_file in st.session_state.get('temp_files', []):
        try:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
                logger.info(f"Fichier temporaire supprimé: {temp_file}")
        except Exception as e:
            logger.warning(f"Impossible de supprimer {temp_file}: {str(e)}")
    st.session_state.temp_files = []

# Gestionnaires d'événements
async def handle_message_send(message: str):
    """Gère l'envoi d'un message"""
    # Ajouter le message utilisateur
    st.session_state.chat_history.append({
        'role': 'user',
        'content': message,
        'timestamp': datetime.now().strftime("%H:%M")
    })
    
    # Activer l'indicateur de frappe
    st.session_state.is_typing = True
    st.rerun()

async def process_message():
    """Traite le message avec le LLM"""
    try:
        # Préparer les messages pour l'API
        api_messages = services['chat_handler'].filter_messages_for_api(
            st.session_state.chat_history
        )
        
        # Obtenir la réponse
        response = await services['llm_client'].chat(api_messages)
        
        if response:
            # Ajouter la réponse
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now().strftime("%H:%M")
            })
            
                
    except Exception as e:
        logger.error(f"Erreur traitement message: {str(e)}")
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': "❌ Désolé, une erreur s'est produite. Pouvez-vous reformuler ?",
            'timestamp': datetime.now().strftime("%H:%M"),
            'error': True
        })
    
    st.session_state.is_typing = False
    st.rerun()

async def handle_file_upload(uploaded_file):
    """Gère l'upload d'un fichier"""
    # Réinitialiser les états PDF si on charge un nouveau fichier
    st.session_state.is_pdf_loaded = False
    st.session_state.converted_docx = None
    # Éviter les doublons
    file_key = f"{uploaded_file.name}_{uploaded_file.size}"
    if file_key in st.session_state.processed_files:
        return
    
    st.session_state.processed_files.add(file_key)
    
    # Ajouter le message d'upload
    st.session_state.chat_history.append({
        'role': 'user',
        'content': f"📎 Fichier envoyé : {uploaded_file.name}",
        'timestamp': datetime.now().strftime("%H:%M"),
        'file_name': uploaded_file.name,
        'file_size': uploaded_file.size,
        'file_key': file_key
    })
    
    st.session_state.is_typing = True
    st.rerun()

async def process_file(uploaded_file):
    """Traite le fichier uploadé"""
    try:
        file_content = uploaded_file.getbuffer()
        suffix = Path(uploaded_file.name).suffix
        
        with temporary_file(file_content, suffix=suffix) as temp_path:
            # Lire le contenu
            content = services['file_handler'].read_file(temp_path, uploaded_file.name)
            
            # Stocker les informations
            st.session_state.current_file = {
                'name': uploaded_file.name,
                'content': content,
                'type': suffix[1:].lower(),
                'raw_bytes': file_content,
                'size': uploaded_file.size
            }
            
            # Stocker le contenu (caché)
            st.session_state.chat_history.append({
                'role': 'system',
                'content': content,
                'meta': 'file_content',
                'file_name': uploaded_file.name,
                'timestamp': datetime.now().strftime("%H:%M")
            })
            
            # Traitement spécifique
            if uploaded_file.name.endswith('.xlsx'):
                st.session_state.excel_workbook = services['excel_handler'].load_workbook_from_bytes(
                    file_content
                )
                st.session_state.layout_mode = 'split'  # Vue partagée pour Excel
                
                response = f"✅ J'ai chargé votre fichier Excel '{uploaded_file.name}'. Il contient {len(st.session_state.excel_workbook.sheetnames)} feuilles. Vous pouvez maintenant :\n\n• Visualiser et éditer les données dans l'onglet Excel\n• Extraire les données budgétaires\n• Utiliser l'outil BPSS pour les mesures catégorielles"
                
            elif uploaded_file.name.endswith('.json'):
                import json
                st.session_state.json_data = json.loads(content)
                response = f"✅ Fichier JSON de configuration chargé. Il contient {len(st.session_state.json_data.get('tags', []))} tags pour le mapping automatique."

            elif uploaded_file.name.endswith('.pdf'):
                # Stocker qu'il s'agit d'un PDF pour la conversion
                st.session_state.is_pdf_loaded = True
                
                # Obtenir les infos du PDF
                pdf_info = services['pdf_converter'].get_pdf_info(temp_path)
                
                response = f"✅ J'ai chargé votre fichier PDF '{uploaded_file.name}'. "
                if pdf_info.get('pages'):
                    response += f"Il contient {pdf_info['pages']} pages. "
                
                response += "\n\nVoici un aperçu :\n\n{preview}\n\nQue souhaitez-vous faire avec ce fichier ?"
                
                # Si c'est un PDF, proposer la conversion
                if pdf_info.get('has_text', False):
                    response += "\n\n💡 **Astuce :** Vous pouvez convertir ce PDF en Word avec le bouton ci-dessous."

            else:
                # Résumé pour autres types
                preview = content[:200] + "..." if len(content) > 200 else content
                response = f"✅ J'ai bien reçu votre fichier '{uploaded_file.name}'. Voici un aperçu :\n\n{preview}\n\nQue souhaitez-vous faire avec ce fichier ?"
            
            # Ajouter la réponse
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response,
                'timestamp': datetime.now().strftime("%H:%M")
            })
        
    except Exception as e:
        logger.error(f"Erreur traitement fichier: {str(e)}")
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': f"❌ Erreur lors du traitement : {str(e)}",
            'timestamp': datetime.now().strftime("%H:%M"),
            'error': True
        })
    
    st.session_state.is_typing = False
    st.rerun()

async def convert_pdf_to_word():
    """Convertit le PDF chargé en document Word"""
    if not st.session_state.get('current_file'):
        st.error("❌ Aucun fichier PDF chargé")
        return
    
    file_info = st.session_state.current_file
    if not file_info['name'].endswith('.pdf'):
        st.error("❌ Le fichier actuel n'est pas un PDF")
        return
    
    with st.spinner("Conversion en cours... Cela peut prendre quelques instants pour les gros fichiers."):
        try:
            # Options de conversion
            preserve_layout = st.session_state.get('pdf_convert_preserve_layout', True)
            
            # Convertir
            docx_bytes = services['pdf_converter'].convert_pdf_bytes_to_docx(
                file_info['raw_bytes'],
                preserve_layout=preserve_layout
            )
            
            if docx_bytes:
                # Créer le nom du fichier de sortie
                original_name = Path(file_info['name']).stem
                output_name = f"{original_name}_converti.docx"
                
                # Stocker le résultat
                st.session_state.converted_docx = {
                    'bytes': docx_bytes,
                    'filename': output_name,
                    'original_pdf': file_info['name']
                }
                
                # Ajouter un message de succès
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': f"✅ J'ai converti votre PDF en document Word !\n\n"
                             f"**Fichier original :** {file_info['name']}\n"
                             f"**Fichier converti :** {output_name}\n\n"
                             f"Utilisez le bouton de téléchargement ci-dessous pour récupérer le fichier Word.",
                    'timestamp': datetime.now().strftime("%H:%M"),
                    'has_download': True
                })
                
                st.success("✅ Conversion réussie!")
                st.rerun()
                
            else:
                st.error("❌ Erreur lors de la conversion")
                
        except Exception as e:
            logger.error(f"Erreur conversion PDF: {str(e)}")
            st.error(f"❌ Erreur lors de la conversion: {str(e)}")

def handle_tool_action(action: dict):
    """Gère les actions des outils"""
    action_type = action.get('action')
    
    if action_type == 'clear_history':
        # Réinitialiser la conversation
        st.session_state.chat_history = [{
            'role': 'assistant',
            'content': WELCOME_MESSAGE,
            'timestamp': datetime.now().strftime("%H:%M"),
            'type': 'welcome'
        }]
        st.session_state.processed_files = set()
        st.session_state.current_file = None
        st.session_state.excel_workbook = None
        st.session_state.extracted_data = None
        cleanup_temp_files()
        st.success("✨ Conversation réinitialisée")
        
    elif action_type == 'extract_budget':
        asyncio.run(extract_budget_data())
        
    elif action_type == 'process_bpss':
        asyncio.run(process_bpss(action.get('data')))
        
    elif action_type == 'parse_excel':
        parse_excel_formulas()
        
    elif action_type == 'map_budget_cells':
        asyncio.run(map_budget_to_cells())
        
    elif action_type == 'apply_formulas':
        apply_excel_formulas()
    
    elif action_type == 'apply_validated_mapping':
        asyncio.run(apply_validated_mapping())
    
    elif action_type == 'convert_pdf':
        asyncio.run(convert_pdf_to_word())

async def extract_budget_data():
    """Extrait les données budgétaires"""
    if not st.session_state.current_file:
        st.error("❌ Aucun fichier chargé")
        return
    
    with st.spinner("Extraction en cours..."):
        try:
            content = st.session_state.current_file['content']
            file_name = st.session_state.current_file['name']
            
            # Limiter la taille
            if len(content) > 10000:
                content = content[:10000] + "\n\n[... contenu tronqué ...]"
            
            # Extraire
            data = await services['budget_extractor'].extract(
                content, 
                services['llm_client']
            )
            
            if data:
                st.session_state.extracted_data = data
                st.session_state.excel_tab = 'analysis'
                
                # Message de succès
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': f"✅ J'ai extrait **{len(data)} entrées budgétaires** du fichier '{file_name}'.\n\nRendez-vous dans l'onglet 'Extraction' pour visualiser et éditer les données.",
                    'timestamp': datetime.now().strftime("%H:%M")
                })
                st.success(f"✅ {len(data)} entrées extraites!")
            else:
                st.warning("⚠️ Aucune donnée budgétaire trouvée")
                
        except Exception as e:
            logger.error(f"Erreur extraction: {str(e)}")
            st.error(f"❌ Erreur: {str(e)}")

async def process_bpss(data: dict):
    """Traite les fichiers BPSS"""
    try:
        progress = st.progress(0, text="Traitement BPSS...")
        
        # Créer des fichiers temporaires SANS les supprimer automatiquement
        import tempfile
        import os
        
        temp_files = []
        temp_paths = {}
        
        try:
            # Sauvegarder les fichiers temporairement
            for key, file in data['files'].items():
                # Créer un fichier temporaire
                fd, temp_path = tempfile.mkstemp(suffix='.xlsx')
                temp_files.append(temp_path)  # Garder la trace pour nettoyage
                
                # Écrire le contenu
                with os.fdopen(fd, 'wb') as tmp:
                    tmp.write(file.getbuffer())
                
                temp_paths[key] = temp_path
                logger.info(f"Fichier temporaire créé: {key} -> {temp_path}")
            
            progress.progress(50, text="Application des données...")
            
            # Traiter avec les fichiers temporaires
            result_wb = services['bpss_tool'].process_files(
                ppes_path=temp_paths['ppes'],
                dpp18_path=temp_paths['dpp18'],
                bud45_path=temp_paths['bud45'],
                year=data['year'],
                ministry_code=data['ministry'],
                program_code=data['program'],
                target_workbook=st.session_state.excel_workbook or openpyxl.Workbook()
            )
            
            st.session_state.excel_workbook = result_wb
            progress.progress(100, text="Terminé!")
            
            # Message de succès
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': f"✅ Traitement BPSS terminé!\n\nJ'ai intégré les données pour:\n• Année: {data['year']}\n• Ministère: {data['ministry']}\n• Programme: {data['program']}\n\nLes feuilles ont été ajoutées à votre fichier Excel.",
                'timestamp': datetime.now().strftime("%H:%M")
            })
            
            st.success("✅ Traitement BPSS réussi!")

            # IMPORTANT : Forcer le rechargement
            st.session_state.excel_workbook = result_wb

            # Sauvegarder temporairement pour l'affichage des valeurs
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
                result_wb.save(tmp.name)
                services['excel_handler'].current_path = tmp.name
                temp_files.append(tmp.name)

            # Message de succès avec détails
            st.success(f"""
            ✅ Traitement BPSS terminé!
            - Année: {data['year']}
            - Ministère: {data['ministry']}
            - Programme: {data['program']}

            Feuilles ajoutées: Données PP-E-S, INF DPP 18, INF BUD 45
            """)

            # Basculer vers l'onglet Excel
            st.session_state.layout_mode = 'excel'

            # FORCER LE RAFRAÎCHISSEMENT
            st.rerun()
            
        finally:
            # Nettoyer les fichiers temporaires
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.unlink(temp_file)
                        logger.info(f"Fichier temporaire supprimé: {temp_file}")
                except Exception as e:
                    logger.warning(f"Impossible de supprimer {temp_file}: {str(e)}")
        
    except Exception as e:
        logger.error(f"Erreur BPSS: {str(e)}")
        st.error(f"❌ Erreur: {str(e)}")

def parse_excel_formulas():
    """Parse les formules Excel avec le parseur Python amélioré"""
    if not st.session_state.current_file:
        st.error("❌ Aucun fichier Excel chargé")
        return
    
    with st.spinner("Analyse des formules Excel..."):
        try:
            # Configuration du parseur
            parser_config = ParserConfig(
                chunk_size=800,
                workers=4,
                progress_enabled=True
            )
            
            # Créer une instance du parseur
            parser = ExcelFormulaParser(parser_config)
            
            # Sauvegarder temporairement le fichier
            with temporary_file(st.session_state.current_file['raw_bytes'], suffix='.xlsx') as path:
                # Parser le fichier
                result = parser.parse_excel_file(path, emit_script=True)
                
                st.session_state.parsed_formulas = result
                stats = result['statistics']
                
                # Afficher les résultats
                if stats['success'] > 0:
                    st.success(f"✅ {stats['success']}/{stats['total']} formules converties avec succès")
                    
                    # Ajouter un message dans le chat
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': f"✅ J'ai analysé **{stats['total']} formules Excel** dans votre fichier.\n\n"
                                 f"• **{stats['success']}** formules converties avec succès ({stats['success_rate']}%)\n"
                                 f"• **{stats['errors']}** formules avec erreurs\n\n"
                                 f"Un script Python a été généré pour appliquer ces formules.",
                        'timestamp': datetime.now().strftime("%H:%M")
                    })
                    
                    # Activer le bouton d'application si succès
                    if result.get('script_file'):
                        st.session_state.formula_script_ready = True
                else:
                    st.warning(f"⚠️ Aucune formule n'a pu être convertie sur {stats['total']} trouvées")
                
        except Exception as e:
            logger.error(f"Erreur parsing: {str(e)}")
            st.error(f"❌ Erreur: {str(e)}")

def apply_excel_formulas():
    """Applique les formules parsées au workbook avec debug amélioré"""
    if not st.session_state.get('parsed_formulas'):
        st.error("❌ Aucune formule parsée. Lancez d'abord le parsing.")
        return
    
    if not st.session_state.get('excel_workbook'):
        st.error("❌ Aucun fichier Excel chargé")
        return
    
    with st.spinner("Application des formules en cours..."):
        try:
            # Récupérer les formules parsées
            parsed_data = st.session_state.parsed_formulas
            formulas = parsed_data.get('formulas', [])
            
            if not formulas:
                st.warning("⚠️ Aucune formule à appliquer")
                return
            
            # Créer une instance du parseur
            parser_config = ParserConfig(
                chunk_size=800,
                workers=4,
                progress_enabled=True
            )
            parser = ExcelFormulaParser(parser_config)
            
            # Afficher les informations de debug si activé
            if st.session_state.get('debug_mode', False):
                st.info(f"🔍 Mode debug: Application de {len(formulas)} formules")
                
                # Afficher un échantillon du code généré
                sample_formulas = [f for f in formulas[:5] if f.python_code and not f.error]
                if sample_formulas:
                    with st.expander("Exemples de code Python généré"):
                        for f in sample_formulas:
                            st.code(f"{f.sheet}!{f.address}: {f.python_code}", language="python")
            
            # Appliquer les formules au workbook
            updated_wb = parser.apply_formulas_to_workbook(
                st.session_state.excel_workbook,
                formulas
            )
            
            # Mettre à jour le workbook en session
            st.session_state.excel_workbook = updated_wb
            
            # Sauvegarder temporairement pour l'affichage des valeurs
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
                updated_wb.save(tmp.name)
                services['excel_handler'].current_path = tmp.name
                st.session_state.temp_files.append(tmp.name)
            
            # Analyser les résultats
            success_count = sum(1 for f in formulas if f.value is not None and not f.error)
            error_count = sum(1 for f in formulas if f.error)
            
            # Afficher les résultats détaillés
            col1, col2 = st.columns(2)
            with col1:
                st.metric("✅ Succès", success_count)
            with col2:
                st.metric("❌ Erreurs", error_count)
            
            # Message de succès
            if success_count > 0:
                st.success(f"✅ {success_count} formules appliquées avec succès!")
                
                # Ajouter un message dans le chat
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': f"✅ J'ai appliqué **{success_count} formules** dans votre fichier Excel.\n\n"
                             f"• **{success_count}** calculs réussis\n"
                             f"• **{error_count}** erreurs\n\n"
                             f"Basculez en mode 'Valeurs' pour voir les résultats calculés.",
                    'timestamp': datetime.now().strftime("%H:%M")
                })
            
            # Gestion détaillée des erreurs
            if error_count > 0:
                st.warning(f"⚠️ {error_count} formules n'ont pas pu être calculées")
                
                # Grouper les erreurs par type
                error_types = {}
                if st.session_state.get('formula_errors'):
                    for err in st.session_state.formula_errors:
                        error_msg = err['error']
                        # Extraire le type d'erreur
                        if "can only concatenate str" in error_msg:
                            error_type = "Erreur de type (string/nombre)"
                        elif "unsupported operand type" in error_msg:
                            error_type = "Opération impossible (types incompatibles)"
                        elif "NoneType" in error_msg:
                            error_type = "Valeur manquante (None)"
                        else:
                            error_type = "Autre erreur"
                        
                        if error_type not in error_types:
                            error_types[error_type] = []
                        error_types[error_type].append(err)
                
                # Afficher les erreurs groupées
                st.markdown("### 📋 Détails des erreurs")
                for error_type, errors in error_types.items():
                    st.markdown(f"**{error_type}** ({len(errors)} erreurs)")
                    
                    # Afficher quelques exemples
                    for err in errors[:3]:
                        st.error(f"**{err['cell']}**: {err['formula']}")
                        st.caption(f"Erreur: {err['error'][:100]}...")
                        if st.session_state.get('debug_mode'):
                            st.code(f"Code généré: {err.get('python_code', 'N/A')}", language="python")
                    
                    if len(errors) > 3:
                        st.caption(f"... et {len(errors) - 3} autres erreurs de ce type")
                
                
                # Suggestions de correction
                st.info("""
                💡 **Suggestions pour corriger les erreurs** :
                
                1. **Erreurs de type** : Vérifiez que les cellules contiennent bien des nombres
                2. **Valeurs manquantes** : Remplacez les cellules vides par 0
                3. **Formules complexes** : Simplifiez les formules ou décomposez-les
                
                Vous pouvez éditer les données dans l'onglet "Données" puis relancer le calcul.
                """)
            
            # Forcer le rafraîchissement
            st.rerun()
            
        except Exception as e:
            logger.error(f"Erreur application formules: {str(e)}")
            st.error(f"❌ Erreur lors de l'application: {str(e)}")
            
            # En mode debug, afficher la trace complète
            if st.session_state.get('debug_mode'):
                import traceback
                st.code(traceback.format_exc(), language="python")

async def map_budget_to_cells():
    """
    Mappe les données aux cellules Excel - VERSION CORRIGÉE
    Génère le mapping et prépare pour validation sans appliquer directement
    """
    if not st.session_state.get('extracted_data') or not st.session_state.get('json_data'):
        st.error("❌ Données manquantes pour le mapping")
        return
    
    if not st.session_state.get('excel_workbook'):
        st.error("❌ Aucun fichier Excel chargé")
        return
    
    with st.spinner("Analyse et mapping en cours..."):
        try:
            mapper = services['budget_mapper']
            tags = services['json_helper'].get_tags_for_mapping(st.session_state.json_data)
            
            # Créer une barre de progression
            progress_bar = st.progress(0)
            progress_text = st.empty()
            
            def update_progress(percent, text):
                progress_bar.progress(int(percent))
                progress_text.text(text)
            
            # Mapper avec callback de progression
            mapping = await mapper.map_entries_to_cells(
                st.session_state.extracted_data,
                tags,
                progress_callback=update_progress
            )
            
            # Nettoyer la barre de progression
            progress_bar.empty()
            progress_text.empty()
            
            if mapping:
                # Valider le mapping avant de proposer l'application
                validated_mapping, validation_issues = mapper.validate_and_prepare_mapping(
                    mapping, 
                    st.session_state.excel_workbook
                )
                
                if validated_mapping:
                    # Enrichir les entrées avec le mapping
                    entries_df = pd.DataFrame(st.session_state.extracted_data)
                    enriched_df = mapper.enrich_entries_with_mapping(entries_df, validated_mapping)
                    
                    # Mettre à jour les données extraites enrichies
                    st.session_state.extracted_data = enriched_df.to_dict('records')
                    st.session_state.pending_mapping = validated_mapping  # stocker le mapping validé
                    st.session_state.mapping_validated = False  # flag de validation
                    
                    # Générer le rapport de mapping
                    report = mapper.generate_mapping_report(validated_mapping, entries_df)
                    st.session_state.mapping_report = report
                
                    st.success(f"""
                    ✅ Mapping préparé avec succès!
                    
                    **Résultats:**
                    - {len(validated_mapping)} entrées mappées
                    - {report['summary']['mapping_rate']:.1f}% de taux de mapping
                    - {report['summary']['average_confidence']:.1%} de confiance moyenne
                    """)
                    
                    # Afficher les problèmes de validation s'il y en a
                    if validation_issues:
                        for issue in validation_issues[:10]:
                            st.warning(issue)
                        if len(validation_issues) > 10:
                            st.info(f"... et {len(validation_issues) - 10} autres avertissements")
                    
                    # Instructions pour la suite
                    st.info("""
                    👉 **Prochaines étapes:**
                    1. Consultez l'interface de vérification dans l'onglet Excel
                    2. Révisez les mappings à faible confiance
                    3. Validez et appliquez le mapping quand vous êtes prêt
                    """)
                    
                    # Message dans le chat
                    st.session_state.chat_history.append({
                        'role': 'assistant',
                        'content': f"✅ Mapping préparé!\n\n• **{len(validated_mapping)}** entrées prêtes à mapper\n• **{report['summary']['mapping_rate']:.1f}%** de taux de mapping\n• **{report['summary']['average_confidence']:.1%}** de confiance moyenne\n\nConsultez l'interface de vérification dans l'onglet Excel pour valider et appliquer les mappings.",
                        'timestamp': datetime.now().strftime("%H:%M")
                    })
                    
                    # Basculer vers la vue Excel pour la vérification
                    st.session_state.layout_mode = 'excel'
                    st.rerun()
                else:
                    st.error("❌ Aucun mapping valide n'a pu être généré")
                    if validation_issues:
                        for issue in validation_issues:
                            st.error(issue)
            else:
                st.warning("⚠️ Aucun mapping n'a pu être établi")
                            
        except Exception as e:
            logger.error(f"Erreur mapping: {str(e)}")
            st.error(f"❌ Erreur lors du mapping: {str(e)}")

#Fonction pour appliquer le mapping validé
async def apply_validated_mapping():
    """
    Applique le mapping validé dans Excel - VERSION CORRIGÉE
    Écrit réellement les valeurs dans le workbook et sauvegarde
    """
    if not st.session_state.get('pending_mapping'):
        st.error("❌ Aucun mapping en attente d'application")
        return
    
    if not st.session_state.get('excel_workbook'):
        st.error("❌ Aucun fichier Excel chargé")
        return
    
    with st.spinner("Application du mapping dans Excel..."):
        try:
            mapper = services['budget_mapper']
            mapping = st.session_state.pending_mapping
            entries_df = pd.DataFrame(st.session_state.extracted_data)
            workbook = st.session_state.excel_workbook
            
            # Appliquer au workbook avec la nouvelle signature
            success_count, errors, modified_cells = mapper.apply_mapping_to_excel(
                workbook,
                mapping,
                entries_df
            )
            
            if success_count > 0:
                # IMPORTANT : Sauvegarder le workbook modifié dans un fichier temporaire
                # pour pouvoir afficher les valeurs mises à jour
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
                    workbook.save(tmp.name)
                    services['excel_handler'].current_path = tmp.name
                    st.session_state.temp_files.append(tmp.name)
                
                # Mettre à jour le workbook en session
                st.session_state.excel_workbook = workbook
                
                # Créer un résumé détaillé
                summary = mapper.create_mapping_summary(mapping, modified_cells)
                
                # Afficher le succès avec détails
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.success(f"""
                    ✅ Mapping appliqué avec succès!
                    
                    **{success_count} cellules** ont été mises à jour dans Excel.
                    Les montants ont été écrits dans les cellules cibles.
                    """)
                
                with col2:
                    st.metric("✍️ Cellules modifiées", success_count)
                
                with col3:
                    # Bouton de téléchargement immédiat
                    excel_bytes = services['excel_handler'].save_workbook_to_bytes(workbook)
                    st.download_button(
                        "📥 Télécharger",
                        data=excel_bytes,
                        file_name=f"excel_mapping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                # Afficher le résumé détaillé
                with st.expander("📊 Voir le résumé détaillé", expanded=True):
                    st.text(summary)
                    
                    # Afficher quelques exemples de cellules modifiées
                    if modified_cells:
                        st.markdown("### 📝 Exemples de modifications:")
                        for cell in modified_cells[:5]:
                            st.success(f"✓ **{cell['sheet']}!{cell['cell']}** = {cell['value']:,.2f} € ({cell['description']})")
                        if len(modified_cells) > 5:
                            st.info(f"... et {len(modified_cells) - 5} autres modifications")
                
                # Marquer comme appliqué
                st.session_state.mapping_validated = True
                st.session_state.pending_mapping = None
                
                # Message dans le chat
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': f"✅ Mapping appliqué avec succès!\n\n• **{success_count}** cellules mises à jour dans Excel\n• Les montants ont été écrits dans les cellules cibles\n\n💾 **Le fichier Excel est prêt** - utilisez le bouton de téléchargement pour récupérer le fichier mis à jour.",
                    'timestamp': datetime.now().strftime("%H:%M")
                })
                
                # Forcer le rafraîchissement pour afficher les nouvelles valeurs
                st.session_state.selected_sheet = st.session_state.selected_sheet  # Garder la même feuille
                st.rerun()
                
            else:
                st.error("❌ Aucune cellule n'a pu être mise à jour")
                
            # Afficher les erreurs s'il y en a
            if errors:
                with st.expander(f"⚠️ {len(errors)} problèmes rencontrés", expanded=False):
                    for error in errors[:10]:
                        if error.startswith("⚠️"):
                            st.warning(error)
                        else:
                            st.error(error)
                    if len(errors) > 10:
                        st.info(f"... et {len(errors) - 10} autres problèmes")
                        
        except Exception as e:
            logger.error(f"Erreur application mapping: {str(e)}")
            st.error(f"❌ Erreur lors de l'application: {str(e)}")
            
            # En mode debug, afficher plus de détails
            if st.session_state.get('debug_mode'):
                import traceback
                st.code(traceback.format_exc(), language="python")

# Initialisation des services
services = init_services()

def main():
    """Fonction principale"""
    # Initialiser l'état
    init_session_state()
    
    # Nettoyer au démarrage
    if 'startup_cleanup' not in st.session_state:
        cleanup_temp_files()
        st.session_state.startup_cleanup = True
    
    # Traiter les messages/fichiers en attente
    if st.session_state.is_typing and st.session_state.chat_history:
        last_msg = st.session_state.chat_history[-1]
        
        if last_msg['role'] == 'user':
            if last_msg['content'].startswith("📎"):
                # Fichier à traiter
                file_key = last_msg.get('file_key')
                if file_key:
                    # Chercher le fichier dans les widgets
                    for widget_key in st.session_state:
                        if widget_key.startswith('file_upload_'):
                            file = st.session_state.get(widget_key)
                            if file and f"{file.name}_{file.size}" == file_key:
                                asyncio.run(process_file(file))
                                break
            else:
                # Message texte
                asyncio.run(process_message())
    
    # Traiter les actions en attente
    if st.session_state.get('pending_action'):
        action = st.session_state.pending_action
        st.session_state.pending_action = None
        
        if action['type'] == 'extract_budget':
            asyncio.run(extract_budget_data())
        
        elif action['type'] == 'convert_pdf':  
            asyncio.run(convert_pdf_to_word())
    
    # Créer et rendre l'interface
    layout = MainLayout(services)
    layout.render(
        on_message_send=lambda msg: asyncio.run(handle_message_send(msg)),
        on_file_upload=lambda file: asyncio.run(handle_file_upload(file)),
        on_tool_action=handle_tool_action
    )

if __name__ == "__main__":
    main()