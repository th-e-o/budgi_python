# main.py
import logging
import json
import os
import tempfile

from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
import datetime

from backend.core.excel_handler.excel_handler import UpdatedExcelHandler
from core.ExcelToUniverConverterOpt import ExcelToUniverConverterOpt
from modules.bpss_tool import BPSSTool

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # WARNING: Only use this in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

excel_handler = UpdatedExcelHandler()
bpss_tool = BPSSTool()

# --- WebSocket Message Models ---
class WebSocketMessage(BaseModel):
    type: str
    payload: Dict[str, Any]


# --- Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection: {websocket.client.host}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket connection closed: {websocket.client.host}")

    async def send_to(self, websocket: WebSocket, message_type: str, payload: Dict):
        """Sends a structured message to a specific websocket."""
        ws_message = WebSocketMessage(type=message_type, payload=payload)
        await websocket.send_text(ws_message.model_dump_json())

    async def broadcast(self, message_type: str, payload: Dict):
        """Broadcasts a structured message to all connected clients."""
        ws_message = WebSocketMessage(type=message_type, payload=payload)
        message_json = ws_message.model_dump_json()
        for connection in self.active_connections:
            await connection.send_text(message_json)


manager = ConnectionManager()

# --- Welcome Message from Streamlit Legacy ---
WELCOME_MESSAGE = """Bonjour,\n
je peux vous aider à :\n
• **Analyser vos fichiers Excel** - Chargez un fichier .xlsx pour commencer\n
• **Extraire des données budgétaires** - À partir de PDF, Word, emails ou textes\n
• **Utiliser l'outil BPSS** - Pour traiter vos fichiers PP-E-S, DPP18 et BUD45
"""


# --- Upload Endpoint (MODIFIED) ---
@app.post("/upload")
async def upload_excel(file: UploadFile = File(...)):
    logger.info(f"Received file for upload: {file.filename}")
    try:
        contents = await file.read()

        excel_handler.load_workbook_from_bytes(contents)

        if not excel_handler.workbook:
            raise HTTPException(status_code=500, detail="Failed to load workbook in handler.")

        sheet_count = len(excel_handler.workbook.sheetnames)
        logger.info(f"Workbook '{file.filename}' loaded with {sheet_count} sheets.")

        converter = ExcelToUniverConverterOpt(excel_handler.workbook)
        univer_data = converter.convert()
        logger.info("Workbook converted to Univer format for initial load.")

        await manager.broadcast("chat_message", {
            "role": "assistant",
            "content": f"✅ Fichier '{file.filename}' chargé. Il contient {sheet_count} feuilles.",
            "timestamp": datetime.datetime.utcnow().isoformat()
        })
        return univer_data

    except Exception as e:
        logger.error(f"Error processing upload: {e}", exc_info=True)
        await manager.broadcast("chat_message", {
            "role": "assistant",
            "content": f"❌ Erreur lors du traitement du fichier '{file.filename}': {str(e)}",
            "error": True, "timestamp": datetime.datetime.utcnow().isoformat()
        })
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@app.post("/bpss/process")
async def process_bpss_files(
        ppes: UploadFile = File(...),
        dpp18: UploadFile = File(...),
        bud45: UploadFile = File(...),
        year: int = Form(...),
        ministry: str = Form(...),
        program: str = Form(...)
):
    logger.info("Received request to process BPSS files.")

    if not excel_handler.has_workbook():
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

            # Get the current workbook from the handler to be modified
            target_workbook = excel_handler.workbook

            # Process the files
            result_wb = bpss_tool.process_files(
                ppes_path=temp_paths['ppes'],
                dpp18_path=temp_paths['dpp18'],
                bud45_path=temp_paths['bud45'],
                year=year,
                ministry_code=ministry,
                program_code=program,
                target_workbook=target_workbook
            )

            # Replace the workbook in the handler with the newly modified one
            excel_handler._user_workbook = result_wb

            # Convert the *new* workbook state to Univer JSON
            converter = ExcelToUniverConverterOpt(excel_handler.workbook)
            updated_univer_data = converter.convert()

            logger.info("BPSS processing complete. Broadcasting workbook_update.")

            # Broadcast the full updated workbook data to all clients
            await manager.broadcast('workbook_update', updated_univer_data)

            # Send a success message to the chat
            await manager.broadcast("chat_message", {
                "role": "assistant",
                "content": f"✅ Traitement BPSS terminé ! Le classeur a été mis à jour.",
                "timestamp": datetime.datetime.utcnow().isoformat()
            })

            return {"message": "BPSS processing successful. Update sent via WebSocket."}

    except Exception as e:
        logger.error(f"Error during BPSS processing: {e}", exc_info=True)
        await manager.broadcast("chat_message", {
            "role": "assistant",
            "content": f"❌ Erreur lors du traitement BPSS : {str(e)}",
            "error": True, "timestamp": datetime.datetime.utcnow().isoformat()
        })
        raise HTTPException(status_code=500, detail=f"BPSS processing failed: {str(e)}")


# --- WebSocket Endpoint (MODIFIED) ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    await manager.send_to(websocket, "chat_message", {
        "role": "assistant",
        "content": WELCOME_MESSAGE,
        "timestamp": datetime.datetime.utcnow().isoformat()
    })
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                msg_type = message.get("type")

                if msg_type == 'cell_update':
                    if excel_handler.has_workbook():
                        excel_handler.apply_component_update(message['payload'])
                    else:
                        logger.warning("Received cell_update but no workbook is loaded.")
                elif msg_type == 'user_message':
                     # Placeholder for future LLM interaction
                    await manager.send_to(websocket, "chat_message", {
                        "role": "assistant",
                        "content": f"Received your message: '{message['payload']['content']}'. LLM logic is not yet connected.",
                        "timestamp": datetime.datetime.utcnow().isoformat()
                    })

            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON via WebSocket: {data}")
            except Exception as e:
                 logger.error(f"Error processing WebSocket message: {e}", exc_info=True)


    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected.")


app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="static")