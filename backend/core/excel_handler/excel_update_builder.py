from __future__ import annotations
from typing import Any, Optional

from openpyxl.worksheet.worksheet import Worksheet


class ExcelUpdateBuilder:
    """
    A builder class for constructing updates to an Excel workbook.
    This class allows building a sequence of operations to modify an Excel workbook.
    """
    def __init__(self):
        self.updates = []

    def create_sheet_if_not_exists(self, sheet_name: str) -> ExcelUpdateBuilder:
        """
        Create a new sheet if it does not already exist.
        :param sheet_name: Name of the sheet to create.
        """
        self.updates.append({
            "type": "create_sheet",
            "sheet_name": sheet_name
        })
        return self

    def delete_sheet(self, sheet_name: str) -> ExcelUpdateBuilder:
        """
        Delete a sheet by its name.
        :param sheet_name: Name of the sheet to delete.
        """
        self.updates.append({
            "type": "delete_sheet",
            "sheet_name": sheet_name
        })
        return self

    def update_cell_value(self, sheet_name: str, row: int, column: int, value: Optional[str]) -> ExcelUpdateBuilder:
        """
        Update the value of a specific cell.
        :param sheet_name: Name of the sheet where the cell is located.
        :param row: Row index of the cell (0-indexed).
        :param column: Column index of the cell (0-indexed).
        :param value: New value to set in the cell.
        """
        self.updates.append({
            "type": "update_cell",
            "sheet_name": sheet_name,
            "row": row,
            "column": column,
            "value": value
        })
        return self

    def create_sheet(self, sheet_name: str) -> ExcelUpdateBuilder:
        """
        Create a new sheet with the specified name.
        :param sheet_name: Name of the new sheet.
        """
        self.updates.append({
            "type": "create_sheet",
            "sheet_name": sheet_name
        })
        return self
