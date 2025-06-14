import logging
from collections import defaultdict
from io import BytesIO
from typing import List, Dict, Set, Optional
import copy

import openpyxl
from openpyxl.workbook import Workbook

from backend.core.excel_handler.excel_handler import UpdatedExcelHandler
from backend.core.excel_handler.operation_types import BackendOperationType, FrontendOperationType
from core.ExcelToUniverConverterOpt import ExcelToUniverConverterOpt

logger = logging.getLogger(__name__)


class ExcelUpdateCompiler:
    """
    Analyzes a list of Excel operations and compiles numerous cell updates
    for a single sheet into a more efficient, single 'REPLACE_SHEET' operation.
    """

    def __init__(self, handler: UpdatedExcelHandler, cell_update_threshold: int = 20):
        """
        Initializes the compiler.

        Args:
            handler: The Excel handler that holds the current state of the workbook.
            cell_update_threshold: The number of cell updates on a single sheet
                                   to trigger compilation for that sheet.
        """
        self.handler = handler
        self.threshold = cell_update_threshold
        self.base_workbook = self.handler.workbook
        self.temp_workbook: Optional[Workbook] = None

    def compile(self, operations: List[Dict]) -> List[Dict]:
        """
        Takes a list of operations and returns a new, potentially smaller list
        where heavy modifications have been compiled.

        Args:
            operations: The original list of operation dictionaries.

        Returns:
            A new list of optimized operations.
        """
        if not self.base_workbook:
            logger.warning("Compiler cannot run without a base workbook. Skipping.")
            return operations

        # Analyze which sheets have too many cell updates
        sheets_to_compile = self._find_sheets_to_compile(operations)
        if not sheets_to_compile:
            return operations  # No optimization needed

        logger.info(f"Compiler will optimize updates for sheets: {list(sheets_to_compile)}")

        # Prepare a temporary in-memory workbook for modifications
        temp_workbook = self.handler.save_workbook_to_bytes(self.handler.workbook)
        self.temp_workbook = openpyxl.load_workbook(BytesIO(temp_workbook), data_only=True, keep_vba=False)
        temp_sheet_map = self._prepare_temp_sheets(sheets_to_compile)

        # Process operations: apply changes to temp sheets or pass them through
        final_ops: List[Dict] = []
        for op in operations:
            op_sheet = op['handler_payload'].get('sheet_name')
            if op_sheet and op_sheet in sheets_to_compile:
                if op['backend_type'] == BackendOperationType.UPDATE_CELL_VALUE:
                    # This operation is being compiled, apply it to the temp sheet
                    self._apply_update_to_temp(op, temp_sheet_map)
                else:
                    # A non-cell-update operation on a compiled sheet (e.g., delete)
                    # is an edge case. For safety, pass it through and log a warning.
                    logger.warning(
                        f"Passing through non-cell op '{op['backend_type'].name}' for compiled sheet '{op_sheet}'.")
                    final_ops.append(op)
            else:
                final_ops.append(op)

        # 4. Generate the new 'REPLACE_SHEET' operations from the temp workbook
        compiled_ops = self._generate_compiled_ops(sheets_to_compile, temp_sheet_map)
        final_ops.extend(compiled_ops)

        # 5. Clean up the temporary workbook in memory
        self._cleanup_temp_sheets(temp_sheet_map)
        self.temp_workbook = None

        logger.info(f"Compilation complete. Original ops: {len(operations)}, Compiled ops: {len(final_ops)}")
        return final_ops

    def _find_sheets_to_compile(self, operations: List[Dict]) -> Set[str]:
        """Counts cell updates per sheet and identifies which exceed the threshold."""
        update_counts = defaultdict(int)
        for op in operations:
            if op['backend_type'] == BackendOperationType.UPDATE_CELL_VALUE:
                sheet_name = op['handler_payload'].get('sheet_name')
                if sheet_name:
                    update_counts[sheet_name] += 1

        return {sheet for sheet, count in update_counts.items() if count > self.threshold}

    def _prepare_temp_sheets(self, sheets_to_compile: Set[str]) -> Dict[str, str]:
        """Creates temporary copies of sheets that will be compiled."""
        temp_sheet_map = {}
        for sheet_name in sheets_to_compile:
            temp_name = f"__compiling_{sheet_name}"
            temp_sheet_map[sheet_name] = temp_name

            if sheet_name in self.temp_workbook.sheetnames:
                source_sheet = self.temp_workbook[sheet_name]
                temp_sheet = self.temp_workbook.copy_worksheet(source_sheet)
                temp_sheet.title = temp_name
            else:
                # If the sheet doesn't exist (it might be created in this transaction),
                # start with a blank temporary sheet.
                self.temp_workbook.create_sheet(temp_name)
        return temp_sheet_map

    def _apply_update_to_temp(self, op: Dict, temp_sheet_map: Dict[str, str]):
        """Applies a single UPDATE_CELL operation to the correct temporary sheet."""
        payload = op['handler_payload']
        original_sheet_name = payload['sheet_name']
        temp_sheet_name = temp_sheet_map.get(original_sheet_name)

        if not temp_sheet_name: return

        temp_sheet = self.temp_workbook[temp_sheet_name]
        # Payload uses 0-based index, openpyxl uses 1-based
        row, col = payload['row'] + 1, payload['column'] + 1
        temp_sheet.cell(row=row, column=col, value=payload['value'])

    def _generate_compiled_ops(self, sheets_to_compile: Set[str], temp_sheet_map: Dict[str, str]) -> List[Dict]:
        """Creates the final REPLACE_SHEET operations from the modified temp sheets."""
        # Save the entire temp workbook to bytes once for efficiency
        with BytesIO() as bio:
            self.temp_workbook.save(bio)
            source_workbook_bytes = bio.getvalue()

        converter = ExcelToUniverConverterOpt(self.temp_workbook)
        compiled_ops = []

        for original_sheet_name in sheets_to_compile:
            temp_sheet_name = temp_sheet_map[original_sheet_name]
            temp_sheet = self.temp_workbook[temp_sheet_name]

            # Generate the UI payload (Univer format)
            ui_sheet_data = converter.convert_sheet(temp_sheet)
            ui_sheet_data['name'] = original_sheet_name  # Ensure the UI replaces the correct sheet

            # Build the new compiled operation
            op = {
                "id": f"compiled-op-{original_sheet_name}",  # A stable ID for the compiled op
                "frontend_type": FrontendOperationType.REPLACE_SHEET,
                "backend_type": BackendOperationType.REPLACE_SHEET_FROM_ANOTHER_WORKBOOK,
                "description": f"Mettre à jour en bloc la feuille '{original_sheet_name}'",
                "handler_payload": {
                    "source_workbook_bytes": source_workbook_bytes,
                    "sheet_name": temp_sheet_name,
                    "new_sheet_name": original_sheet_name
                },
                "ui_payload": ui_sheet_data
            }
            compiled_ops.append(op)

        return compiled_ops

    def _cleanup_temp_sheets(self, temp_sheet_map: Dict[str, str]):
        """Removes all temporary sheets from the in-memory workbook."""
        for temp_name in temp_sheet_map.values():
            if temp_name in self.temp_workbook.sheetnames:
                del self.temp_workbook[temp_name]