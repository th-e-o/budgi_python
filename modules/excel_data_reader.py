import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ExcelDataReader: 
    "Lit et structure les données Excel selon la configuration JSON"

    def __init__(self, excel_handler, json_helper):
        self.excel_handler = excel_handler
        self.json_helper = json_helper
    
    async def read_and_structure_data(self, workbook, json_config) -> Dict[str, Any]:
        """Lit les données Excel et crée une structure compréhensible"""


        }