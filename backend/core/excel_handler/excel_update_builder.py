from __future__ import annotations

import uuid
from io import BytesIO
from typing import Optional, Dict, Any

import pandas as pd
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.workbook import Workbook
import openpyxl

from backend.core.excel_handler.operation_types import BackendOperationType, FrontendOperationType
from core.ExcelToUniverConverterOpt import ExcelToUniverConverterOpt


class ExcelUpdateBuilder:
    """A fluent API for defining a transaction of Excel operations."""

    def __init__(self, synchronization_manager):
        self.operations = []
        self.synchronization_manager = synchronization_manager

    def get_operations(self):
        return self.operations

    def _add_operation(self, frontend_op: FrontendOperationType, backend_op: BackendOperationType, description: str,
                       handler_payload: Dict, ui_payload: Optional[Dict] = None):
        """Internal helper to add a fully-formed operation."""
        op = {
            "id": str(uuid.uuid4()),
            "frontend_type": frontend_op,
            "backend_type": backend_op,
            "description": description,
            "handler_payload": handler_payload,
            "ui_payload": ui_payload or handler_payload
        }
        self.operations.append(op)

    def create_sheet(self, sheet_name: str) -> ExcelUpdateBuilder:
        self._add_operation(
            frontend_op=FrontendOperationType.CREATE_SHEET,
            backend_op=BackendOperationType.CREATE_SHEET,
            description=f"Créer la feuille '{sheet_name}'",
            handler_payload={"sheet_name": sheet_name}
        )
        return self

    def delete_sheet(self, sheet_name: str) -> ExcelUpdateBuilder:
        self._add_operation(
            frontend_op=FrontendOperationType.DELETE_SHEET,
            backend_op=BackendOperationType.DELETE_SHEET,
            description=f"Supprimer la feuille '{sheet_name}'",
            handler_payload={"sheet_name": sheet_name}
        )
        return self

    def update_cell_value(self, sheet_name: str, row: int, col: int, value: Any) -> ExcelUpdateBuilder:
        """Updates only the value of a cell, preserving its style."""
        self._add_operation(
            frontend_op=FrontendOperationType.UPDATE_CELL,
            backend_op=BackendOperationType.UPDATE_CELL_VALUE,
            description=f"Modifier la cellule ({row + 1}, {col + 1}) dans '{sheet_name}'",
            handler_payload={"sheet_name": sheet_name, "row": row, "column": col, "value": value},
            ui_payload={"sheet": sheet_name, "row": row, "col": col, "value": {"v": value}}
        )
        return self

    def import_from_dataframe(self, df: pd.DataFrame, sheet_name: str) -> ExcelUpdateBuilder:
        """
        Replaces a sheet's content with a DataFrame.
        This operation is low-fidelity on the UI side, but high-fidelity on the backend.
        It won't preserve styles of existing cells on the frontend side.
        """
        # To get UI payload, we must convert the df to a temporary worksheet
        temp_wb = openpyxl.Workbook()
        temp_ws = temp_wb.active
        temp_ws.title = sheet_name
        for r in dataframe_to_rows(df, index=False, header=True):
            temp_ws.append(r)

        converter = ExcelToUniverConverterOpt(temp_wb)
        ui_sheet_data = converter.convert_sheet(temp_ws)

        self.delete_sheet(sheet_name)
        self._add_operation(
            frontend_op=FrontendOperationType.REPLACE_SHEET,
            backend_op=BackendOperationType.IMPORT_DATAFRAME,
            description=f"Remplacer la feuille '{sheet_name}' avec de nouvelles données",
            handler_payload={"sheet_name": sheet_name, "df": df.to_dict(orient='split'), "start_row": 1,
                             "start_col": 1},
            ui_payload=ui_sheet_data
        )
        return self

    def import_sheet_from_workbook(self, source_workbook: Workbook, sheet_name: str,
                                   new_sheet_name: Optional[str] = None) -> ExcelUpdateBuilder:
        """High-fidelity import of a sheet from another workbook."""
        target_sheet_name = new_sheet_name or sheet_name
        source_sheet = source_workbook[sheet_name]

        converter = ExcelToUniverConverterOpt(source_workbook)
        ui_sheet_data = converter.convert_sheet(source_sheet)
        ui_sheet_data['name'] = target_sheet_name

        with BytesIO() as bio:
            source_workbook.save(bio)
            source_workbook_bytes = bio.getvalue()

        self.delete_sheet(target_sheet_name)
        self._add_operation(
            frontend_op=FrontendOperationType.REPLACE_SHEET,
            backend_op=BackendOperationType.REPLACE_SHEET_FROM_ANOTHER_WORKBOOK,
            description=f"Importer la feuille '{sheet_name}' vers '{target_sheet_name}'",
            handler_payload={"source_workbook_bytes": source_workbook_bytes, "sheet_name": sheet_name,
                             "new_sheet_name": target_sheet_name},
            ui_payload=ui_sheet_data
        )
        return self

    async def commit(self, require_validation: bool = False):
        """Commits the defined operations to the synchronization manager."""
        if not self.operations:
            return

        await self.synchronization_manager.commit_updates(self, validate=require_validation)