import logging
from datetime import datetime
from typing import Dict, List

from backend.core.communication.ConnectionManager import ConnectionManager
from backend.core.excel_handler.excel_handler import UpdatedExcelHandler
from backend.core.excel_handler.excel_update_builder import ExcelUpdateBuilder

logger = logging.getLogger("ExcelSyncManager")


class ExcelSyncManager:
    """
    Orchestrates data synchronization for a SINGLE client session.
    Manages pending operations for user validation for that session.
    """

    def __init__(self, client_id: str, handler: UpdatedExcelHandler, conn_manager: ConnectionManager):
        self.client_id = client_id
        self.handler = handler
        self.conn_manager = conn_manager
        self.pending_operations: Dict[str, Dict] = {}
        logger.info(f"ExcelSyncManager initialized for Client ID: {self.client_id}")

    def new_update_builder(self) -> ExcelUpdateBuilder:
        """Creates a new, clean builder for defining a transaction."""
        return ExcelUpdateBuilder(self)

    async def commit_updates(self, operations: List[Dict], validate: bool):
        """Commits the operations, handling validation and targeted communication."""
        if not operations:
            return

        ui_ops = [{
            "id": op['id'],
            "type": op['frontend_type'].name,
            "description": op['description'],
            "payload": op['ui_payload']
        } for op in operations]

        if validate:
            self.pending_operations.clear()
            for op in operations:
                self.pending_operations[op['id']] = op

            logger.info(f"Sending {len(ui_ops)} operations for validation to Client ID: {self.client_id}")
            await self.conn_manager.send_to(self.client_id, 'propose_updates', {"operations": ui_ops})
        else:
            # Apply updates to the handler without validation
            handler_ops = [{
                "type": op['backend_type'],
                "description": op['description'],
                "payload": op['handler_payload']
            } for op in operations]
            task = self.handler.apply_updates(handler_ops)

            logger.info(f"Sending {len(ui_ops)} direct update operations to Client ID: {self.client_id}")
            await self.conn_manager.send_to(self.client_id, 'apply_direct_updates', {"operations": ui_ops})
            await self.conn_manager.send_to(self.client_id, "chat_message", {
                "role": "assistant", "content": "✅ Mise à jour directe appliquée.",
                "timestamp": datetime.now().isoformat()
            })

            # Finish the task in the background
            await task

    async def _broadcast_full_update(self, message: str):
        """
        Sends a full workbook update to THIS client.
        Used after validation when the client's state might be out of sync.
        """
        from core.ExcelToUniverConverterOpt import \
            ExcelToUniverConverterOpt  # Local import to avoid circular dependency
        if not self.handler.has_workbook(): return

        converter = ExcelToUniverConverterOpt(self.handler.workbook)
        updated_data = converter.convert()
        await self.conn_manager.send_to(self.client_id, 'workbook_update', updated_data)
        await self.conn_manager.send_to(self.client_id, "chat_message", {
            "role": "assistant", "content": f"✅ {message}", "timestamp": datetime.now().isoformat()
        })

    # --- Handlers for Incoming WebSocket Messages ---

    async def handle_cell_update(self, payload: Dict):
        """Handles a direct cell edit from the UI."""
        logger.info(f"Received cell update from Client ID: {self.client_id}, Payload: {payload}")
        self.handler.apply_component_update(payload)

    async def handle_validate_op(self, payload):
        """
        Handles user validated and rejected requests of the following format:

            {
                "accepted": ["9c2e0ed6-f744-4eea-84fe-1c63e9645e92"],
                "refused": ["ddbeaa31-89d4-41a8-b53b-04147a087455"]
            }
        """
        accepted_ops = []
        for op_id in payload.get('accepted', []):
            op = self.pending_operations.pop(op_id, None)
            if op:
                handler_op = {
                    "type": op['backend_type'],
                    "description": op['description'],
                    "payload": op['handler_payload']
                }
                accepted_ops.append(handler_op)

        await self.handler.apply_updates(accepted_ops)

        self.pending_operations.clear()
        message = f"✅ {len(accepted_ops)} modifications validées et appliquées."
        await self.conn_manager.send_to(self.client_id, "chat_message", {
            "role": "assistant",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })