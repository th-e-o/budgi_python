import logging
import json
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException, Form, Cookie, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Annotated
from fastapi.staticfiles import StaticFiles
import datetime

from backend.core.communication.ConnectionManager import ConnectionManager
from backend.core.communication.excel_synchronization_manager import ExcelSyncManager
from backend.core.excel_handler.excel_handler import UpdatedExcelHandler
from core.ExcelToUniverConverterOpt import ExcelToUniverConverterOpt
from backend.modules.bpss_tool import BPSSTool

from core.chat_service import ChatService

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend" / "dist"
ASSETS_DIR = FRONTEND_DIR / "assets"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # WARNING: Only use this in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

conn_manager = ConnectionManager()
bpss_tool = BPSSTool()

SESSION_HANDLERS: Dict[str, UpdatedExcelHandler] = {}
SESSION_SYNC_MANAGERS: Dict[str, ExcelSyncManager] = {}
SESSION_CHAT_SERVICES: Dict[str, ChatService] = {}

async def get_session_manager(session_id: Annotated[str | None, Cookie()] = None) -> ExcelSyncManager:
    """A FastAPI dependency that retrieves the user's session manager via cookie."""
    if session_id is None or session_id not in SESSION_SYNC_MANAGERS:
        raise HTTPException(status_code=401, detail="Invalid or expired session. Please refresh.")
    return SESSION_SYNC_MANAGERS[session_id]

def get_session_data(session_id: str) -> Dict[str, Any]:
    """Récupère ou initialise les données de session"""
    if session_id not in SESSION_DATA:
        SESSION_DATA[session_id] = {
            'last_file_content': None,
            'last_file_name': None,
            'extracted_budget_data': None,
            'tags': None
        }
    return SESSION_DATA[session_id]

# --- Welcome Message from Streamlit Legacy ---
WELCOME_MESSAGE = """Bonjour,\n
Je peux vous aider à :\n
• **Analyser vos fichiers Excel** - Chargez un fichier .xlsx pour commencer\n
• **Extraire des données budgétaires** - À partir de PDF, Word, emails ou textes\n
• **Utiliser l'outil BPSS** - Pour traiter vos fichiers PP-E-S, DPP18 et BUD45 \n
• **Mapper des données budgétaires** - Associer des entrées aux cellules Excel\n
Vous pouvez envoyer des fichiers (PDF, Word, TXT, MSG) ou poser des questions !
"""


@app.post("/upload")
async def upload_excel(file: UploadFile = File(...), excel_sync_manager: ExcelSyncManager = Depends(get_session_manager)):
    logger.info(f"Received file for upload: {file.filename}")
    try:
        contents = await file.read()

        excel_sync_manager.handler.load_workbook_from_bytes(contents)

        converter = ExcelToUniverConverterOpt(excel_sync_manager.handler.workbook)
        univer_data = converter.convert()
        logger.info("Workbook converted to Univer format for initial load.")

        await conn_manager.send_to(excel_sync_manager.client_id, "chat_message", {
            "role": "assistant",
            "content": f"✅ Fichier '{file.filename}' chargé dans votre session.",
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
        return univer_data

    except Exception as e:
        logger.error(f"Error in upload for session {excel_sync_manager.client_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/perform_small_update")
async def perform_small_update(
        sync_manager: ExcelSyncManager = Depends(get_session_manager)
):
    logger.info(f"Received small update request for session {sync_manager.client_id}")

    if not sync_manager.handler.has_workbook():
        raise HTTPException(status_code=400, detail="No main workbook loaded. Please upload an Excel file first.")

    try:
        # Create a new update builder for the small update
        update_builder = sync_manager.new_update_builder()
        update_builder.update_cell_value("Accueil", 2, 1, "25")
        update_builder.update_cell_value("Accueil", 3, 1, "26")
        update_builder.update_cell_value("Accueil", 4, 2, 123)
        update_builder.update_cell_value("Accueil", 4, 1, 342)
        update_builder.update_cell_value("Accueil", 4, 3, 43432)
        update_builder.update_cell_value("Accueil", 4, 4, 43)
        await update_builder.commit(require_validation=True)

    except Exception as e:
        logger.error(f"Error applying small update: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to apply small update: {str(e)}")

@app.post("/bpss/process")
async def process_bpss_files(
        sync_manager: ExcelSyncManager = Depends(get_session_manager),
        ppes: UploadFile = File(...),
        dpp18: UploadFile = File(...),
        bud45: UploadFile = File(...),
        year: int = Form(...),
        ministry: str = Form(...),
        program: str = Form(...)
):
    logger.info("Received request to process BPSS files.")

    if not sync_manager.handler.has_workbook():
        raise HTTPException(status_code=400, detail="No main workbook loaded. Please upload an Excel file first.")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_paths = {}
            for key, uploaded_file in [('ppes', ppes), ('dpp18', dpp18), ('bud45', bud45)]:
                temp_path = os.path.join(temp_dir, uploaded_file.filename)
                with open(temp_path, 'wb') as f:
                    f.write(await uploaded_file.read())
                temp_paths[key] = temp_path
                logger.info(f"Saved temp file: {temp_path}")

            target_workbook = sync_manager.handler.workbook
            updates = sync_manager.new_update_builder()

            bpss_tool.process_files(
                ppes_path=temp_paths['ppes'],
                dpp18_path=temp_paths['dpp18'],
                bud45_path=temp_paths['bud45'],
                year=year,
                ministry_code=ministry,
                program_code=program,
                target_workbook=target_workbook,
                builder=updates
            )

            await updates.commit(require_validation=False, use_compiler=True)
            logger.info("BPSS processing complete. Broadcasting workbook_update.")

            # Send a success message to the chat
            await conn_manager.send_to(sync_manager.client_id, "chat_message", {
                "role": "assistant",
                "content": f"✅ Traitement BPSS terminé ! Le classeur a été mis à jour.",
                "timestamp": datetime.datetime.utcnow().isoformat()
            })

    except Exception as e:
        logger.error(f"Error during BPSS processing: {e}", exc_info=True)
        await conn_manager.send_to(sync_manager.client_id, "chat_message", {
            "role": "assistant",
            "content": f"❌ Erreur lors du traitement BPSS : {str(e)}",
            "error": True, "timestamp": datetime.datetime.utcnow().isoformat()
        })
        raise HTTPException(status_code=500, detail=f"BPSS processing failed: {str(e)}")

@app.post("/chat/upload_and_message")
async def chat_with_file(
    file: UploadFile = File(...),
    message: str = Form(""),
    history: str = Form("[]"),  # Historique JSON stringifié
    sync_manager: ExcelSyncManager = Depends(get_session_manager)
):
    """Upload fichier + message, traite via LLM, répond via WebSocket (sans contexte Excel automatique)"""
    
    try:
        # 1. Validation du fichier
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ['.pdf', '.docx', '.txt', '.msg']:
            raise HTTPException(status_code=400, detail=f"Type de fichier non supporté: {file_ext}")
        
        # 2. Traiter le fichier
        file_content = await sync_manager.process_uploaded_file(file)
        
        # 3. Parser l'historique
        try:
            chat_history = json.loads(history) if history else []
        except json.JSONDecodeError:
            chat_history = []
        
        # 4. Construire le contexte simple (sans Excel)
        context = {
            'user_message': message,
            'file_content': file_content,
            'file_name': file.filename,
            'chat_history': chat_history
        }
        
        # 5. Traitement LLM
        llm_response = await sync_manager.process_with_llm(context)
        logger.info(f"LLM response generated: {len(llm_response)} characters")
        
        # 6. Envoyer les réponses via WebSocket
        await sync_manager.send_user_message_to_chat(file.filename, message)
        await sync_manager.send_llm_response(llm_response)
        
        # 7. Retour simple d'acquittement
        return {
            "status": "processing", 
            "message": f"Fichier {file.filename} reçu, réponse en cours via chat"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur chat_with_file: {str(e)}", exc_info=True)
        # Envoyer l'erreur via WebSocket aussi
        await sync_manager.send_error_to_chat(f"Erreur lors du traitement: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_user_message(session_id: str, client_id: str, payload: Dict):
    """Traite un message utilisateur avec le LLM"""
    try:
        message_content = payload.get('content', '')
        frontend_history = payload.get('history', [])
        
        if not message_content.strip():
            return
        
        # Récupérer le service de chat de la session
        chat_service = SESSION_CHAT_SERVICES.get(session_id)
        
        if not chat_service:
            raise Exception("Service de chat non initialisé")
        
        # Traiter le message avec le LLM
        llm_response = await chat_service.process_user_message(
            message_content, frontend_history
        )
        
        # Envoyer la réponse au client
        await conn_manager.send_to(client_id, "chat_message", {
            "role": "assistant",
            "content": llm_response,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement du message utilisateur: {str(e)}", exc_info=True)
        await conn_manager.send_to(client_id, "chat_message", {
            "role": "assistant",
            "content": f"❌ Désolé, je n'ai pas pu traiter votre message : {str(e)}",
            "error": True,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })


# --- WebSocket Endpoint ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    session_id, client_id = await conn_manager.connect(websocket)

    session_handler = UpdatedExcelHandler()
    session_sync_manager = ExcelSyncManager(client_id, session_handler, conn_manager)
    session_chat_service = ChatService() 

    SESSION_HANDLERS[session_id] = session_handler
    SESSION_SYNC_MANAGERS[session_id] = session_sync_manager
    SESSION_CHAT_SERVICES[session_id] = session_chat_service

    try:
        # Send to the client its new session_id
        await conn_manager.send_to(client_id, "session_created", {"session_id": session_id})

        await conn_manager.send_to(client_id, "chat_message", {
            "role": "assistant",
            "content": WELCOME_MESSAGE,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })

        while True:
            data = await websocket.receive_text()
            try:
                logger.info(f"Received data: {data}")
                message = json.loads(data)
                msg_type = message.get("type")
                payload = message.get("payload", {})

                if msg_type == 'cell_update':
                    await session_sync_manager.handle_cell_update(payload)

                elif msg_type == 'validate_change':
                    await session_sync_manager.handle_validate_op(payload)

                elif msg_type == 'user_message':
                    await handle_user_message(session_id, client_id, payload)
            
            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON via WebSocket: {data}")
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {e}", exc_info=True)
                break
    except WebSocketDisconnect:
        conn_manager.disconnect(client_id)
        if session_id in SESSION_SYNC_MANAGERS:
            del SESSION_SYNC_MANAGERS[session_id]
        if session_id in SESSION_HANDLERS:
            del SESSION_HANDLERS[session_id]
        logger.info("Client disconnected.")
    finally:
        conn_manager.disconnect(client_id)
        if session_id in SESSION_SYNC_MANAGERS:
            del SESSION_SYNC_MANAGERS[session_id]
        if session_id in SESSION_HANDLERS:
            del SESSION_HANDLERS[session_id]


app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")