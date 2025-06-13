import streamlit as st
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import uuid

from ui.components.excel_component import excel_viewer


class OperationType(Enum):
    UPDATE_CELLS = "update_cells"
    ADD_SHEET = "add_sheet"
    DELETE_SHEET = "delete_sheet"
    FOCUS_CELL = "focus_cell"
    FOCUS_SHEET = "focus_sheet"


@dataclass
class CellUpdate:
    sheet: str
    cell: str
    value: Any
    value_type: str = "v"  # "v" for value, "f" for formula


@dataclass
class SheetOperation:
    operation_id: str
    operation_type: OperationType
    payload: Dict[str, Any]


class ExcelComponentManager:
    """
    A clean, encapsulated manager for the Excel Streamlit component.
    Handles initialization, user changes, and programmatic updates.
    """

    def __init__(self, key: str, height: int = 600):
        self.key = key
        self.height = height
        self.component_key = f"excel_component_{key}"

        # Internal state keys
        self._initialized_key = f"_excel_initialized_{key}"
        self._pending_ops_key = f"_excel_pending_ops_{key}"
        self._workbook_data_key = f"_excel_workbook_{key}"

        # Initialize pending operations queue if not exists
        if self._pending_ops_key not in st.session_state:
            st.session_state[self._pending_ops_key] = []

    def initialize(self, workbook_data: Dict[str, Any]) -> 'ExcelComponentManager':
        """Initialize the component with workbook data (called only once)."""
        if not self.is_initialized():
            st.session_state[self._workbook_data_key] = workbook_data
            st.session_state[self._initialized_key] = True
        return self

    def is_initialized(self) -> bool:
        """Check if the component has been initialized."""
        return st.session_state.get(self._initialized_key, False)

    def update_cells(self, updates: List[CellUpdate]) -> 'ExcelComponentManager':
        """Queue cell updates to be sent to the component."""
        operation = SheetOperation(
            operation_id=str(uuid.uuid4()),
            operation_type=OperationType.UPDATE_CELLS,
            payload={
                "updates": [
                    {
                        "sheet": update.sheet,
                        "cell": update.cell,
                        "value": update.value,
                        "value_type": update.value_type
                    }
                    for update in updates
                ]
            }
        )
        self._add_pending_operation(operation)
        return self

    def add_sheet(self, sheet_name: str, sheet_data: Dict[str, Any]) -> 'ExcelComponentManager':
        """Add a new sheet to the workbook."""
        operation = SheetOperation(
            operation_id=str(uuid.uuid4()),
            operation_type=OperationType.ADD_SHEET,
            payload={
                "sheet_name": sheet_name,
                "sheet_data": sheet_data
            }
        )
        self._add_pending_operation(operation)
        return self

    def focus_cell(self, sheet: str, cell: str) -> 'ExcelComponentManager':
        """Focus on a specific cell."""
        operation = SheetOperation(
            operation_id=str(uuid.uuid4()),
            operation_type=OperationType.FOCUS_CELL,
            payload={
                "sheet": sheet,
                "cell": cell
            }
        )
        self._add_pending_operation(operation)
        return self

    def focus_sheet(self, sheet: str) -> 'ExcelComponentManager':
        """Focus on a specific sheet."""
        operation = SheetOperation(
            operation_id=str(uuid.uuid4()),
            operation_type=OperationType.FOCUS_SHEET,
            payload={
                "sheet": sheet
            }
        )
        self._add_pending_operation(operation)
        return self

    def render(self, on_change: Optional[Callable[[Dict[str, Any]], None]] = None) -> Any:
        """
        Render the component and handle user interactions.

        Args:
            on_change: Callback function called when user makes changes to the sheet

        Returns:
            The component response (user changes)
        """
        # Prepare initial data (only if not initialized)
        initial_data = None
        if self.is_initialized():
            initial_data = st.session_state.get(self._workbook_data_key)

        # Prepare update command (if any pending operations)
        update_command = None
        pending_ops = st.session_state.get(self._pending_ops_key, [])
        if pending_ops:
            # Send the next operation
            next_op = pending_ops[0]
            update_command = {
                "operation_id": next_op.operation_id,
                "action": next_op.operation_type.value,
                "payload": next_op.payload
            }

        component_response = excel_viewer(
            initial_data=initial_data,
            update_command=update_command,
            height=self.height,
            key=self.component_key,
            default=None
        )

        # Handle operation acknowledgment
        if update_command and component_response is None:
            # Component processed the operation, remove from queue
            st.session_state[self._pending_ops_key] = pending_ops[1:]

        # Handle user changes
        if component_response and isinstance(component_response, dict):
            if 'operation_ack' in component_response:
                # This is an operation acknowledgment
                self._handle_operation_ack(component_response['operation_ack'])
            else:
                # This is a user change
                if on_change:
                    on_change(component_response)

        return component_response

    def _add_pending_operation(self, operation: SheetOperation):
        """Add an operation to the pending queue."""
        if self._pending_ops_key not in st.session_state:
            st.session_state[self._pending_ops_key] = []
        st.session_state[self._pending_ops_key].append(operation)

    def _handle_operation_ack(self, operation_id: str):
        """Handle acknowledgment of a completed operation."""
        pending_ops = st.session_state.get(self._pending_ops_key, [])
        st.session_state[self._pending_ops_key] = [
            op for op in pending_ops if op.operation_id != operation_id
        ]

    def clear_pending_operations(self):
        """Clear all pending operations."""
        st.session_state[self._pending_ops_key] = []

    def has_pending_operations(self) -> bool:
        """Check if there are pending operations."""
        return len(st.session_state.get(self._pending_ops_key, [])) > 0


class ExcelSheetBuilder:
    """Helper class to build sheet data more easily."""

    @staticmethod
    def create_sheet(name: str, data: List[List[Any]], headers: Optional[List[str]] = None) -> Dict[str, Any]:
        """Create a sheet from tabular data."""
        sheet_data = {
            "name": name,
            "cellData": {}
        }

        # Add headers if provided
        start_row = 0
        if headers:
            header_row = {}
            for col, header in enumerate(headers):
                header_row[str(col)] = {"v": header, "t": 1}  # String type
            sheet_data["cellData"]["0"] = header_row
            start_row = 1

        # Add data rows
        for row_idx, row_data in enumerate(data):
            row_dict = {}
            for col_idx, cell_value in enumerate(row_data):
                if cell_value is not None:
                    cell_type = 2 if isinstance(cell_value, (int, float)) else 1
                    row_dict[str(col_idx)] = {"v": cell_value, "t": cell_type}

            if row_dict:  # Only add non-empty rows
                sheet_data["cellData"][str(start_row + row_idx)] = row_dict

        return sheet_data


class ExcelSession:
    """Context manager for Excel component sessions."""

    def __init__(self, key: str, height: int = 600):
        self.manager = ExcelComponentManager(key, height)
        self.changes = []

    def __enter__(self) -> ExcelComponentManager:
        return self.manager

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def collect_changes(self, change_data: Dict[str, Any]):
        """Collect user changes for batch processing."""
        self.changes.append(change_data)

    def get_changes(self) -> List[Dict[str, Any]]:
        """Get all collected changes."""
        return self.changes.copy()

    def clear_changes(self):
        """Clear collected changes."""
        self.changes.clear()