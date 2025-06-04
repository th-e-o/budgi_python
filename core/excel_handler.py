# core/excel_handler.py
import openpyxl
import pandas as pd
from io import BytesIO
from typing import Optional, Union, Dict, Any
import logging
import tempfile
import os

logger = logging.getLogger(__name__)

class ExcelHandler:
    """Gère les opérations sur les fichiers Excel"""
    
    def __init__(self):
        self.current_workbook = None
        self.current_path = None
        self.temp_files = []
    
    def load_workbook(self, file_path: str) -> openpyxl.Workbook:
        """Charge un workbook depuis un fichier"""
        try:
            # Keep images and VBA
            wb = openpyxl.load_workbook(
                file_path, 
                data_only=False, 
                keep_vba=True,
                keep_links=False  # Disable external links
            )
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
            # Save bytes to temporary file to keep file reference
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                tmp_file.write(file_bytes)
                temp_path = tmp_file.name
            
            self.temp_files.append(temp_path)
            
            # Load from temp file
            wb = openpyxl.load_workbook(
                temp_path,
                data_only=False,
                keep_vba=True,
                keep_links=False
            )
            self.current_workbook = wb
            self.current_path = temp_path
            logger.info("Workbook chargé depuis bytes via fichier temporaire")
            return wb
        except Exception as e:
            logger.error(f"Erreur chargement workbook depuis bytes: {str(e)}")
            raise
    
    def save_workbook_to_bytes(self, workbook: openpyxl.Workbook) -> bytes:
        """Sauvegarde un workbook en bytes"""
        try:
            # Create a new BytesIO object
            output = BytesIO()
            
            # Save workbook
            workbook.save(output)
            
            # Get the bytes
            output.seek(0)
            result = output.getvalue()
            
            # Close BytesIO
            output.close()
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde workbook: {str(e)}")
            # If error is due to images, try saving without them
            try:
                logger.info("Tentative de sauvegarde sans images...")
                return self._save_workbook_without_images(workbook)
            except:
                raise e
    
    def _save_workbook_without_images(self, workbook: openpyxl.Workbook) -> bytes:
        """Sauvegarde un workbook sans les images"""
        try:
            # Create a copy without images
            output = BytesIO()
            
            # Remove images from all sheets
            for sheet in workbook.worksheets:
                if hasattr(sheet, '_images'):
                    sheet._images = []
            
            # Save workbook
            workbook.save(output)
            
            # Get the bytes
            output.seek(0)
            result = output.getvalue()
            output.close()
            
            logger.warning("Workbook sauvegardé sans images")
            return result
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde sans images: {str(e)}")
            raise
    
    def sheet_to_dataframe(self, workbook: openpyxl.Workbook, sheet_name: str, 
                       show_formulas: bool = False) -> pd.DataFrame:
        """Convertit une feuille en DataFrame"""
        if sheet_name not in workbook.sheetnames:
            raise ValueError(f"Feuille '{sheet_name}' non trouvée")
        
        sheet = workbook[sheet_name]
        data = []
        
        # Si on veut les valeurs calculées et qu'on a le chemin du fichier
        if not show_formulas and hasattr(self, 'current_path') and self.current_path:
            try:
                # Charger en mode data_only pour avoir les valeurs
                wb_values = openpyxl.load_workbook(self.current_path, data_only=True)
                sheet_values = wb_values[sheet_name]
                for row in sheet_values.iter_rows(values_only=True):
                    data.append(list(row))
                wb_values.close()
            except:
                # Fallback sur les valeurs actuelles
                for row in sheet.iter_rows(values_only=True):
                    data.append(list(row))
        else:
            # Mode formules ou pas de chemin
            for row in sheet.iter_rows(values_only=True):
                data.append(list(row))
        
        if data:
            df = pd.DataFrame(data)
            # Important: ne pas remplir avec des chaînes vides
            # Cela permet l'édition dans toutes les cellules
            return df
        else:
            # IMPORTANT: Créer un DataFrame avec au moins quelques lignes et colonnes
            # pour permettre l'édition dans Streamlit
            min_rows = 20  # Nombre minimum de lignes
            min_cols = 10  # Nombre minimum de colonnes
            
            # Obtenir les dimensions actuelles de la feuille
            max_row = max(sheet.max_row, min_rows)
            max_col = max(sheet.max_column, min_cols)
            
            # Créer un DataFrame avec des valeurs None (pas des chaînes vides)
            df = pd.DataFrame(index=range(max_row), columns=range(max_col))
            
            return df
    
    def dataframe_to_sheet(self, df: pd.DataFrame, workbook: openpyxl.Workbook, 
                        sheet_name: str, start_row: int = 1, start_col: int = 1):
        """Écrit un DataFrame dans une feuille"""
        if sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
        else:
            sheet = workbook.create_sheet(sheet_name)
        
        # D'abord, effacer toutes les cellules existantes dans la plage
        # pour éviter les données résiduelles
        for row in sheet.iter_rows(min_row=start_row, max_row=start_row + len(df) - 1,
                                min_col=start_col, max_col=start_col + len(df.columns) - 1):
            for cell in row:
                cell.value = None
        
        # Écrire les nouvelles données
        for r_idx, row in enumerate(df.values):
            for c_idx, value in enumerate(row):
                try:
                    # Écrire toutes les valeurs, y compris les cellules vides
                    # pour s'assurer que les suppressions sont prises en compte
                    if pd.notna(value) and str(value).strip() != '':
                        # Convertir les valeurs pour éviter les problèmes de type
                        if isinstance(value, (int, float)):
                            sheet.cell(row=start_row + r_idx, column=start_col + c_idx, value=value)
                        else:
                            sheet.cell(row=start_row + r_idx, column=start_col + c_idx, value=str(value))
                    else:
                        # Explicitement mettre None pour les cellules vides
                        sheet.cell(row=start_row + r_idx, column=start_col + c_idx, value=None)
                        
                except Exception as e:
                    logger.warning(f"Erreur écriture cellule ({start_row + r_idx}, {start_col + c_idx}): {str(e)}")
        
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
                'has_formulas': False,
                'has_images': False
            }
            
            # Vérifier s'il y a des formules
            for row in sheet.iter_rows(max_row=min(100, sheet.max_row)):  # Limit scan
                for cell in row:
                    if cell.value and isinstance(cell.value, str) and cell.value.startswith('='):
                        sheet_info['has_formulas'] = True
                        break
                if sheet_info['has_formulas']:
                    break
            
            # Check for images
            if hasattr(sheet, '_images') and sheet._images:
                sheet_info['has_images'] = True
            
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
    
    def cleanup_temp_files(self):
        """Nettoie les fichiers temporaires"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
                    logger.info(f"Fichier temporaire supprimé: {temp_file}")
            except Exception as e:
                logger.warning(f"Impossible de supprimer {temp_file}: {str(e)}")
        self.temp_files = []
    
    def __del__(self):
        """Destructeur pour nettoyer les fichiers temporaires"""
        self.cleanup_temp_files()