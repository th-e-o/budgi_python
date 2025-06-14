from enum import Enum, auto


class BackendOperationType(Enum):
    """
    Defines the full set of operations the ExcelHandler can execute internally.
    These are the "engine" commands.
    """
    CREATE_SHEET = auto() # Creates a new sheet in the workbook
    DELETE_SHEET = auto() # Deletes a sheet from the workbook if it exists
    UPDATE_CELL_VALUE = auto() # Updates the value of a cell
    IMPORT_DATAFRAME = auto()  # Dumps a DataFrame into a sheet, preserving styles of untouched cells
    REPLACE_SHEET_FROM_ANOTHER_WORKBOOK = auto() # High-fidelity copy of a sheet from another workbook object


class FrontendOperationType(Enum):
    """
    Defines the operations as they are presented to the frontend.
    This simplifies the user experience.
    """
    CREATE_SHEET = auto() # Creates a new sheet in the workbook
    DELETE_SHEET = auto() # Deletes a sheet from the workbook if it exists
    UPDATE_CELL = auto() # Updates the value of a cell
    REPLACE_SHEET = auto() # Replaces the entire content of a sheet with another sheet's content