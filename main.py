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

async def get_session_manager(session_id: Annotated[str | None, Cookie()] = None) -> ExcelSyncManager:
    """A FastAPI dependency that retrieves the user's session manager via cookie."""
    if session_id is None or session_id not in SESSION_SYNC_MANAGERS:
        raise HTTPException(status_code=401, detail="Invalid or expired session. Please refresh.")
    return SESSION_SYNC_MANAGERS[session_id]

# --- Welcome Message from Streamlit Legacy ---
WELCOME_MESSAGE = """Bonjour,\n
je peux vous aider à :\n
• **Analyser vos fichiers Excel** - Chargez un fichier .xlsx pour commencer\n
• **Extraire des données budgétaires** - À partir de PDF, Word, emails ou textes\n
• **Utiliser l'outil BPSS** - Pour traiter vos fichiers PP-E-S, DPP18 et BUD45
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

            await updates.commit(require_validation=False, use_compiler=False)
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


# --- WebSocket Endpoint ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    session_id, client_id = await conn_manager.connect(websocket)

    session_handler = UpdatedExcelHandler()
    session_sync_manager = ExcelSyncManager(client_id, session_handler, conn_manager)
    SESSION_HANDLERS[session_id] = session_handler
    SESSION_SYNC_MANAGERS[session_id] = session_sync_manager

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
                    await session_sync_manager.handle_validate_op(payload.get('id'))

                elif msg_type == 'reject_change':
                    await session_sync_manager.handle_reject_op(payload.get('id'))

                elif msg_type == 'validate_all_changes':
                    await session_sync_manager.handle_validate_all()

                elif msg_type == 'reject_all_changes':
                    await session_sync_manager.handle_reject_all()

                elif msg_type == 'user_message':
                     # Placeholder for future LLM interaction
                    await conn_manager.send_to(client_id, "chat_message", {
                        "role": "assistant",
                        "content": f"Received your message: '{message['payload']['content']}'. LLM logic is not yet connected.",
                        "timestamp": datetime.datetime.utcnow().isoformat()
                    })
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


# app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")
# app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")