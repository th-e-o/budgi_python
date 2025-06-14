import logging
import uuid
from typing import Dict, Any

from pydantic import BaseModel
from fastapi import WebSocket


class WebSocketMessage(BaseModel):
    """Represents a structured message sent over WebSocket connections."""
    type: str
    payload: Dict[str, Any]


class ConnectionManager:
    """
    Manages WebSocket connections, enabling targeted and broadcast communication.
    Connections are identified by a unique client ID.
    """

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.logger = logging.getLogger("ConnectionManager")

    async def connect(self, websocket: WebSocket) -> tuple[str, str]:
        """
        Accepts a new WS connection, assigns it a unique session and client ID.
        Returns (session_id, client_id).
        """
        await websocket.accept()
        session_id = str(uuid.uuid4())
        # TODO: In a more complex case, refactor this to allow multiple clients per session.
        client_id = session_id # For this simple case, they can be the same.
                               # In more complex scenarios, a user might have multiple
                               # client connections (tabs) to one session.
        self.active_connections[client_id] = websocket
        self.logger.info(f"New WebSocket connection. Session ID: {session_id}, Client ID: {client_id}")
        return session_id, client_id

    def disconnect(self, client_id: str):
        """Removes a WebSocket connection by its client ID."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            self.logger.info(f"WebSocket connection closed for Client ID: {client_id}")

    async def send_to(self, client_id: str, message_type: str, payload: Dict):
        """Sends a structured message to a specific client by their ID."""
        websocket = self.active_connections.get(client_id)
        if websocket:
            ws_message = WebSocketMessage(type=message_type, payload=payload)
            await websocket.send_text(ws_message.model_dump_json())
        else:
            self.logger.warning(f"Attempted to send message to non-existent Client ID: {client_id}")

    async def broadcast(self, message_type: str, payload: Dict):
        """Broadcasts a structured message to all connected clients."""
        if not self.active_connections:
            return

        ws_message = WebSocketMessage(type=message_type, payload=payload)
        message_json = ws_message.model_dump_json()
        for websocket in self.active_connections.values():
            await websocket.send_text(message_json)