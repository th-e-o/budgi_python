# app.py - Version corrigée
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

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        'show_bpss_tool': False,
        'pending_action': None,
        'json_data': None,
        'parsed_formulas': None,
        'excel_script': None,
        'message_input_key': 0,  # Clé pour forcer le rafraîchissement
        'scroll_to_bottom': False
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

def inject_scroll_script():
    """Injecte le script pour scroll automatique"""
    # Créer un placeholder en bas de page qui force le scroll
    scroll_anchor = st.empty()
    
    if st.session_state.get('scroll_to_bottom', False):
        # Méthode 1: Utiliser JavaScript
        st.markdown("""
        <script>
        // Fonction de scroll améliorée
        function scrollChatToBottom() {
            // Chercher le container avec overflow
            const containers = document.querySelectorAll('[data-testid="stVerticalBlock"]');
            
            containers.forEach(container => {
                // Vérifier si c'est le bon container (celui avec hauteur fixe)
                const style = window.getComputedStyle(container);
                if (style.height === '500px' || container.style.height === '500px') {
                    container.scrollTop = container.scrollHeight;
                    console.log('Scrolled container:', container);
                }
            });
            
            // Alternative: chercher par classe
            const chatContainers = document.querySelectorAll('.stContainer > div');
            chatContainers.forEach(container => {
                if (container.scrollHeight > container.clientHeight) {
                    container.scrollTop = container.scrollHeight;
                }
            });
        }
        
        // Exécuter immédiatement et après un délai
        scrollChatToBottom();
        setTimeout(scrollChatToBottom, 200);
        setTimeout(scrollChatToBottom, 500);
        </script>
        """, unsafe_allow_html=True)
        
        # Méthode 2: Anchor invisible en bas
        with scroll_anchor:
            st.markdown('<div id="bottom-anchor" style="height: 1px;"></div>', unsafe_allow_html=True)
            st.markdown("""
            <script>
            document.getElementById('bottom-anchor')?.scrollIntoView({ behavior: 'smooth' });
            </script>
            """, unsafe_allow_html=True)
        
        st.session_state.scroll_to_bottom = False

def get_enhanced_styles():
    """Styles CSS améliorés pour le scroll"""
    return """
    <style>
        /* Forcer le scroll-behavior smooth sur les containers */
        [data-testid="stVerticalBlock"] {
            scroll-behavior: smooth !important;
        }
        
        /* Container des messages avec scroll amélioré */
        .chat-messages {
            scroll-behavior: smooth;
            overflow-y: auto;
            overflow-x: hidden;
        }
        
        /* Fix pour le container height */
        div[style*="height: 500px"] {
            overflow-y: auto !important;
            scroll-behavior: smooth !important;
        }
        
        /* Animation pour nouveaux messages */
        .message-wrapper {
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        /* S'assurer que le container prend toute la hauteur */
        .main .block-container {
            height: 100%;
            display: flex;
            flex-direction: column;
        }
    </style>
    """


async def handle_file_upload(uploaded_file):
    """Gère l'upload d'un fichier"""
    # Notifier l'upload
    st.session_state.chat_history.append({
        'role': 'user',
        'content': f"📎 Fichier envoyé : {uploaded_file.name}",
        'timestamp': datetime.now().strftime("%H:%M"),
        'file_name': uploaded_file.name  # Ajouter le nom du fichier
    })
    
    st.session_state.is_typing = True
    st.session_state.scroll_to_bottom = True
    st.rerun()

async def process_file(uploaded_file):
    """Traite le fichier de manière asynchrone"""
    try:
        # Créer un fichier temporaire
        temp_path = Path(f"/tmp/{uploaded_file.name}")
        temp_path.parent.mkdir(exist_ok=True)
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        content = services['file_handler'].read_file(str(temp_path), uploaded_file.name)
        
        # IMPORTANT: Stocker le contenu complet du fichier
        st.session_state.current_file = {
            'name': uploaded_file.name,
            'content': content,
            'path': str(temp_path),
            'type': uploaded_file.name.split('.')[-1].lower()
        }
        
        # Ajouter aussi dans l'historique pour l'extraction
        st.session_state.chat_history.append({
            'role': 'system',
            'content': content,
            'meta': 'file_content',
            'file_name': uploaded_file.name,
            'timestamp': datetime.now().strftime("%H:%M")
        })
        
        # Si c'est un Excel, le charger
        if uploaded_file.name.endswith('.xlsx'):
            st.session_state.excel_workbook = services['excel_handler'].load_workbook_from_bytes(
                uploaded_file.getbuffer()
            )
        
        # Si c'est un JSON, le charger
        if uploaded_file.name.endswith('.json'):
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
        
        # Nettoyer
        temp_path.unlink(missing_ok=True)
        
    except Exception as e:
        logger.error(f"Erreur lors de l'upload du fichier: {str(e)}")
        st.error(f"Erreur lors du traitement du fichier: {str(e)}")
    
    st.session_state.is_typing = False
    st.session_state.scroll_to_bottom = True
    st.rerun()

def handle_tool_action(action: dict):
    """Gère les actions des outils"""
    action_type = action.get('action')
    
    if action_type == 'clear_history':
        st.session_state.chat_history = []
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
        try:
            # Sauvegarder temporairement les fichiers
            temp_files = {}
            for key, file in data['files'].items():
                temp_path = Path(f"/tmp/{file.name}")
                with open(temp_path, "wb") as f:
                    f.write(file.getbuffer())
                temp_files[key] = str(temp_path)
            
            # Traiter avec l'outil BPSS
            result_wb = services['bpss_tool'].process_files(
                ppes_path=temp_files['ppes'],
                dpp18_path=temp_files['dpp18'],
                bud45_path=temp_files['bud45'],
                year=data['year'],
                ministry_code=data['ministry'],
                program_code=data['program'],
                target_workbook=st.session_state.excel_workbook or openpyxl.Workbook()
            )
            
            st.session_state.excel_workbook = result_wb
            st.success("✅ Traitement BPSS terminé!")
            
            # Nettoyer les fichiers temporaires
            for path in temp_files.values():
                Path(path).unlink(missing_ok=True)
                
        except Exception as e:
            st.error(f"Erreur BPSS: {str(e)}")

async def extract_budget_data():
    """Extrait les données budgétaires"""
    # D'abord vérifier current_file
    if st.session_state.current_file and st.session_state.current_file.get('content'):
        content = st.session_state.current_file['content']
    else:
        # Sinon, chercher dans l'historique
        content = None
        for msg in reversed(st.session_state.chat_history):
            if msg.get('meta') == 'file_content':
                content = msg['content']
                break
        
        if not content:
            st.error("Aucun fichier chargé pour l'extraction")
            return
    
    with st.spinner("Extraction en cours..."):
        try:
            data = await services['budget_extractor'].extract(
                content,
                services['llm_client']
            )
            
            if data:
                st.session_state.extracted_data = data
                st.success(f"✅ {len(data)} entrées extraites!")
                
                # Afficher les données dans un modal
                show_budget_data_modal(data)
            else:
                st.warning("Aucune donnée trouvée")
                
        except Exception as e:
            st.error(f"Erreur extraction: {str(e)}")

def show_budget_data_modal(data):
    """Affiche les données budgétaires extraites"""
    with st.expander("📊 Données budgétaires extraites", expanded=True):
        import pandas as pd
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
                    map_budget_to_cells()
                else:
                    st.warning("Chargez d'abord un fichier JSON de configuration")
        
        with col3:
            if st.button("📥 Exporter CSV"):
                csv = edited_df.to_csv(index=False)
                st.download_button(
                    label="Télécharger CSV",
                    data=csv,
                    file_name="budget_data.csv",
                    mime="text/csv"
                )

def map_budget_to_cells():
    """Mappe les données budgétaires aux cellules Excel"""
    if not st.session_state.extracted_data or not st.session_state.json_data:
        st.error("Données manquantes pour le mapping")
        return
    
    # Utiliser le JSON helper pour mapper
    tags = services['json_helper'].get_tags_for_mapping(st.session_state.json_data)
    
    # TODO: Implémenter la logique de mapping
    st.info("Mapping en cours de développement...")

def parse_excel_formulas():
    """Parse les formules Excel"""
    if not st.session_state.excel_workbook:
        st.error("Aucun fichier Excel chargé")
        return
    
    with st.spinner("Analyse des formules en cours..."):
        try:
            from modules.excel_parser.parser_v3 import ExcelFormulaParser
            
            parser = ExcelFormulaParser()
            result = parser.parse_excel_file(
                st.session_state.current_file['path'],
                emit_script=True
            )
            
            st.session_state.parsed_formulas = result
            st.session_state.excel_script = result.get('script_file')
            
            stats = result['statistics']
            st.success(f"✅ Parsing terminé: {stats['success']}/{stats['total']} formules converties ({stats['success_rate']}%)")
            
        except Exception as e:
            st.error(f"Erreur parsing: {str(e)}")

def apply_excel_formulas():
    """Applique les formules Excel parsées"""
    if not st.session_state.excel_script:
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

def main():
    # Initialiser l'état
    init_session_state()
    
    # Ajouter scroll_to_bottom à init_session_state
    if 'scroll_to_bottom' not in st.session_state:
        st.session_state.scroll_to_bottom = False
    
    # Gérer les messages en attente de traitement
    if st.session_state.is_typing and len(st.session_state.chat_history) > 0:
        last_msg = st.session_state.chat_history[-1]
        if last_msg['role'] == 'user':
            asyncio.run(process_message())
    
    # Gérer les fichiers en attente
    for msg in st.session_state.chat_history:
        if msg['role'] == 'user' and msg['content'].startswith("📎 Fichier envoyé :") and st.session_state.is_typing:
            # Récupérer le fichier depuis file_upload_chat
            file_to_process = st.session_state.get('file_upload_chat')
            if file_to_process:
                asyncio.run(process_file(file_to_process))
            break
    
    # Gérer les actions en attente
    if st.session_state.pending_action:
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