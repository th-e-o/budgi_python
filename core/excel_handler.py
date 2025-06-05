# core/excel_handler.py - Version qui conserve VRAIMENT la mise en forme
import openpyxl
import pandas as pd
from io import BytesIO
from typing import Optional, Union, Dict, Any, List
import logging
import tempfile
import os
from copy import copy
import warnings

logger = logging.getLogger(__name__)

class ExcelHandler:
    """Gère les opérations sur les fichiers Excel avec conservation complète de la mise en forme"""
    
    def __init__(self):
        self.current_workbook = None
        self.current_path = None
        self.temp_files = []
        self.original_workbook = None  # Garder une référence au workbook original
        warnings.filterwarnings('ignore', category=UserWarning, module='openpyxl')
    
    def load_workbook(self, file_path: str) -> openpyxl.Workbook:
        """Charge un workbook depuis un fichier"""
        try:
            wb = openpyxl.load_workbook(
                file_path, 
                data_only=False,      # Garder les formules
                keep_vba=True,        # Garder le VBA
                keep_links=True,      # Garder les liens
                rich_text=True        # Garder le texte enrichi
            )
            self.current_workbook = wb
            self.current_path = file_path
            # Garder une copie pour la mise en forme
            self.original_workbook = wb
            logger.info(f"Workbook chargé avec mise en forme: {file_path}")
            return wb
        except Exception as e:
            logger.error(f"Erreur chargement workbook: {str(e)}")
            raise
    
    def load_workbook_from_bytes(self, file_bytes: bytes) -> openpyxl.Workbook:
        """Charge un workbook depuis des bytes avec conservation de la mise en forme"""
        try:
            # Créer un fichier temporaire
            fd, temp_path = tempfile.mkstemp(suffix='.xlsx')
            
            try:
                # Écrire les bytes
                with os.fdopen(fd, 'wb') as tmp_file:
                    tmp_file.write(file_bytes)
                
                self.temp_files.append(temp_path)
                
                # Charger avec toutes les options pour préserver la mise en forme
                wb = openpyxl.load_workbook(
                    temp_path,
                    data_only=False,
                    keep_vba=True,
                    keep_links=True,
                    rich_text=True
                )
                
                self.current_workbook = wb
                self.current_path = temp_path
                self.original_workbook = wb  # Garder la référence
                logger.info("Workbook chargé depuis bytes avec mise en forme préservée")
                return wb
                
            except Exception as e:
                if os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                raise
                
        except Exception as e:
            logger.error(f"Erreur chargement workbook depuis bytes: {str(e)}")
            raise
    
    def save_workbook_to_bytes(self, workbook: openpyxl.Workbook) -> bytes:
        """Sauvegarde le workbook SANS PERDRE la mise en forme"""
        # IMPORTANT: Ne pas créer de nouveau workbook!
        # On utilise le workbook existant qui a déjà toute la mise en forme
        
        fd, temp_path = tempfile.mkstemp(suffix='.xlsx')
        os.close(fd)
        
        try:
            # Sauvegarder directement le workbook modifié
            workbook.save(temp_path)
            logger.info(f"Workbook sauvegardé avec mise en forme dans: {temp_path}")
            
            # Lire le fichier
            with open(temp_path, 'rb') as f:
                data = f.read()
            
            logger.info(f"Fichier Excel exporté: {len(data)} octets")
            return data
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde: {str(e)}")
            raise
        finally:
            # Nettoyer
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    self.temp_files.append(temp_path)
    
    def sheet_to_dataframe(self, workbook: openpyxl.Workbook, sheet_name: str, 
                          show_formulas: bool = False) -> pd.DataFrame:
        """Convertit une feuille en DataFrame pour l'édition"""
        from openpyxl.cell.cell import MergedCell
        
        if sheet_name not in workbook.sheetnames:
            raise ValueError(f"Feuille '{sheet_name}' non trouvée")
        
        sheet = workbook[sheet_name]
        data = []
        
        # Lire les données
        for row in sheet.iter_rows():
            row_data = []
            for cell in row:
                # Gérer les MergedCell
                if isinstance(cell, MergedCell):
                    # Pour les cellules fusionnées, prendre la valeur de la cellule origine
                    # Trouver la cellule origine de la fusion
                    for merged_range in sheet.merged_cells.ranges:
                        if cell.coordinate in merged_range:
                            # Prendre la valeur de la première cellule de la plage
                            origin_cell = sheet[merged_range.start_cell.coordinate]
                            row_data.append(origin_cell.value)
                            break
                    else:
                        row_data.append(None)
                elif show_formulas:
                    row_data.append(cell.value)
                else:
                    if hasattr(cell, 'value'):
                        if isinstance(cell.value, str) and cell.value.startswith('='):
                            # Pour les formules, essayer d'obtenir la valeur calculée
                            # Si on a un chemin, recharger en mode data_only
                            if self.current_path and os.path.exists(self.current_path):
                                try:
                                    wb_values = openpyxl.load_workbook(self.current_path, data_only=True)
                                    calculated_value = wb_values[sheet_name].cell(cell.row, cell.column).value
                                    wb_values.close()
                                    row_data.append(calculated_value)
                                except:
                                    row_data.append(f"[{cell.value}]")
                            else:
                                row_data.append(f"[{cell.value}]")
                        else:
                            row_data.append(cell.value)
                    else:
                        row_data.append(None)
            data.append(row_data)
        
        # Créer le DataFrame
        df = pd.DataFrame(data) if data else pd.DataFrame()
        
        # S'assurer d'avoir une taille minimale pour l'édition
        min_rows = 20
        min_cols = 10
        
        current_rows = len(df)
        current_cols = len(df.columns) if not df.empty else 0
        
        # Étendre si nécessaire
        if current_rows < min_rows:
            empty_rows = pd.DataFrame(
                index=range(current_rows, min_rows), 
                columns=df.columns if not df.empty else range(min_cols)
            )
            df = pd.concat([df, empty_rows], ignore_index=True)
        
        if current_cols < min_cols:
            for i in range(current_cols, min_cols):
                df[i] = None
        
        return df
    
    def dataframe_to_sheet(self, df: pd.DataFrame, workbook: openpyxl.Workbook, 
                          sheet_name: str, start_row: int = 1, start_col: int = 1):
        """Écrit un DataFrame dans une feuille SANS TOUCHER à la mise en forme"""
        from openpyxl.cell.cell import MergedCell
        
        if sheet_name not in workbook.sheetnames:
            raise ValueError(f"Feuille '{sheet_name}' non trouvée")
            
        sheet = workbook[sheet_name]
        
        # IMPORTANT: Ne PAS effacer la feuille!
        # On met à jour UNIQUEMENT les valeurs
        
        for r_idx, row in enumerate(df.values):
            for c_idx, value in enumerate(row):
                try:
                    target_row = start_row + r_idx
                    target_col = start_col + c_idx
                    cell = sheet.cell(row=target_row, column=target_col)
                    
                    # Ne pas essayer de modifier une MergedCell
                    if isinstance(cell, MergedCell):
                        # Pour les cellules fusionnées, il faut modifier la cellule origine
                        for merged_range in sheet.merged_cells.ranges:
                            if cell.coordinate in merged_range:
                                # Modifier la cellule origine de la fusion
                                origin_cell = sheet[merged_range.start_cell.coordinate]
                                if pd.isna(value) or value is None or str(value).strip() == '':
                                    origin_cell.value = None
                                elif isinstance(value, str) and value.startswith('='):
                                    origin_cell.value = value
                                elif isinstance(value, (int, float)):
                                    origin_cell.value = value
                                else:
                                    origin_cell.value = str(value)
                                break
                        continue
                    
                    # Pour les cellules normales, juste changer la valeur
                    # SANS TOUCHER AU STYLE!
                    if pd.isna(value) or value is None or str(value).strip() == '':
                        cell.value = None
                    elif isinstance(value, str) and value.startswith('='):
                        cell.value = value
                    elif isinstance(value, (int, float)):
                        cell.value = value
                    else:
                        cell.value = str(value)
                        
                except Exception as e:
                    logger.warning(f"Erreur écriture cellule ({target_row}, {target_col}): {str(e)}")
        
        logger.info(f"DataFrame écrit dans '{sheet_name}' avec mise en forme préservée")
    
    def get_sheet_info(self, workbook: openpyxl.Workbook) -> Dict[str, Any]:
        """Récupère les informations sur les feuilles du workbook"""
        info = {
            'sheets': [],
            'total_sheets': len(workbook.sheetnames),
            'has_vba': hasattr(workbook, 'vba_archive') and workbook.vba_archive is not None,
            'has_styles': True  # On préserve toujours les styles maintenant
        }
        
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            sheet_info = {
                'name': sheet_name,
                'max_row': sheet.max_row,
                'max_column': sheet.max_column,
                'has_formulas': False,
                'has_images': hasattr(sheet, '_images') and bool(sheet._images),
                'has_charts': hasattr(sheet, '_charts') and bool(sheet._charts),
                'has_merged_cells': len(sheet.merged_cells.ranges) > 0
            }
            
            # Vérifier les formules
            for row in sheet.iter_rows(max_row=min(100, sheet.max_row)):
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
        """Met à jour une cellule spécifique SANS toucher au style"""
        from openpyxl.cell.cell import MergedCell
        
        if sheet_name not in workbook.sheetnames:
            raise ValueError(f"Feuille '{sheet_name}' non trouvée")
        
        sheet = workbook[sheet_name]
        cell = sheet.cell(row=row, column=col)
        
        # Vérifier si c'est une MergedCell
        if isinstance(cell, MergedCell):
            # Trouver et modifier la cellule origine
            for merged_range in sheet.merged_cells.ranges:
                if cell.coordinate in merged_range:
                    origin_cell = sheet[merged_range.start_cell.coordinate]
                    origin_cell.value = value
                    logger.info(f"Cellule origine mise à jour: {merged_range.start_cell.coordinate}")
                    return
            logger.warning(f"Impossible de trouver l'origine de la cellule fusionnée {sheet_name}!{openpyxl.utils.get_column_letter(col)}{row}")
            return
        
        # Pour une cellule normale, juste mettre à jour la valeur
        cell.value = value
        logger.info(f"Cellule mise à jour: {sheet_name}!{openpyxl.utils.get_column_letter(col)}{row}")
    
    def apply_formulas_to_workbook(self, workbook: openpyxl.Workbook, 
                                formulas: List['FormulaCell']) -> openpyxl.Workbook:
        """Applique les formules au workbook en préservant les styles"""
        # Cette méthode met à jour UNIQUEMENT les valeurs calculées
        # sans toucher à la mise en forme
        
        for formula in formulas:
            if formula.value is not None and not formula.error:
                try:
                    self.update_cell(
                        workbook,
                        formula.sheet,
                        formula.row,
                        formula.col,
                        formula.value
                    )
                except Exception as e:
                    logger.error(f"Erreur application formule {formula.sheet}!{formula.address}: {str(e)}")
        
        return workbook
    
    def save_workbook_to_file(self, workbook: openpyxl.Workbook, file_path: str) -> bool:
        """Sauvegarde le workbook directement dans un fichier"""
        try:
            # Sauvegarder directement avec toute la mise en forme
            workbook.save(file_path)
            logger.info(f"Workbook sauvegardé avec mise en forme dans: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde fichier: {str(e)}")
            return False


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