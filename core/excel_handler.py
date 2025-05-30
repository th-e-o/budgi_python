# core/excel_handler.py
import openpyxl
import pandas as pd
from io import BytesIO
from typing import Optional, Union, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ExcelHandler:
    """Gère les opérations sur les fichiers Excel"""
    
    def __init__(self):
        self.current_workbook = None
        self.current_path = None
    
    def load_workbook(self, file_path: str) -> openpyxl.Workbook:
        """Charge un workbook depuis un fichier"""
        try:
            wb = openpyxl.load_workbook(file_path, data_only=False, keep_vba=True)
            self.current_workbook = wb
            self.current_path = file_path
            logger.info(f"Workbook chargé: {file_path}")
            return wb
        except Exception as e:
            logger.error(f"Erreur chargement workbook: {str(e)}")
            raise
    
    def load_workbook_from_bytes(self, file_bytes: bytes) -> openpyxl.Workbook:
        """Charge un workbook depuis des bytes"""
        try:
            wb = openpyxl.load_workbook(BytesIO(file_bytes), data_only=False, keep_vba=True)
            self.current_workbook = wb
            logger.info("Workbook chargé depuis bytes")
            return wb
        except Exception as e:
            logger.error(f"Erreur chargement workbook depuis bytes: {str(e)}")
            raise
    
    def save_workbook_to_bytes(self, workbook: openpyxl.Workbook) -> bytes:
        """Sauvegarde un workbook en bytes"""
        output = BytesIO()
        workbook.save(output)
        output.seek(0)
        return output.getvalue()
    
    def sheet_to_dataframe(self, workbook: openpyxl.Workbook, sheet_name: str) -> pd.DataFrame:
        """Convertit une feuille en DataFrame"""
        if sheet_name not in workbook.sheetnames:
            raise ValueError(f"Feuille '{sheet_name}' non trouvée")
        
        sheet = workbook[sheet_name]
        data = []
        
        for row in sheet.iter_rows(values_only=True):
            data.append(list(row))
        
        if data:
            df = pd.DataFrame(data)
            # Nettoyer les valeurs None
            df = df.fillna('')
            return df
        else:
            return pd.DataFrame()
    
    def dataframe_to_sheet(self, df: pd.DataFrame, workbook: openpyxl.Workbook, 
                          sheet_name: str, start_row: int = 1, start_col: int = 1):
        """Écrit un DataFrame dans une feuille"""
        if sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
        else:
            sheet = workbook.create_sheet(sheet_name)
        
        # Écrire les données
        for r_idx, row in enumerate(df.values):
            for c_idx, value in enumerate(row):
                sheet.cell(row=start_row + r_idx, column=start_col + c_idx, value=value)
        
        logger.info(f"DataFrame écrit dans la feuille '{sheet_name}'")
    
    def get_sheet_info(self, workbook: openpyxl.Workbook) -> Dict[str, Any]:
        """Récupère les informations sur les feuilles du workbook"""
        info = {
            'sheets': [],
            'total_sheets': len(workbook.sheetnames)
        }
        
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            sheet_info = {
                'name': sheet_name,
                'max_row': sheet.max_row,
                'max_column': sheet.max_column,
                'has_formulas': False
            }
            
            # Vérifier s'il y a des formules
            for row in sheet.iter_rows():
                for cell in row:
                    if cell.value and isinstance(cell.value, str) and cell.value.startswith('='):
                        sheet_info['has_formulas'] = True
                        break
                if sheet_info['has_formulas']:
                    break
            
            info['sheets'].append(sheet_info)
        
        return info
    
    def update_cell(self, workbook: openpyxl.Workbook, sheet_name: str, 
                   row: int, col: int, value: Any):
        """Met à jour une cellule spécifique"""
        if sheet_name not in workbook.sheetnames:
            raise ValueError(f"Feuille '{sheet_name}' non trouvée")
        
        sheet = workbook[sheet_name]
        sheet.cell(row=row, column=col, value=value)
        logger.info(f"Cellule mise à jour: {sheet_name}!{openpyxl.utils.get_column_letter(col)}{row}")
    
    def apply_formulas_from_script(self, workbook: openpyxl.Workbook, 
                                  script_content: str) -> openpyxl.Workbook:
        """Applique les formules générées par le parseur"""
        # Cette méthode serait implémentée pour exécuter le script Python généré
        # et appliquer les résultats au workbook
        logger.info("Application des formules depuis le script")
        # TODO: Implémenter l'exécution du script
        return workbook