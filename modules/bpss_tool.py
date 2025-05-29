# modules/bpss_tool.py
import pandas as pd
import openpyxl
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class BPSSTool:
    """Outil BPSS pour traitement des fichiers budgétaires"""
    
    def __init__(self):
        self.config = {
            'default_year': 2025,
            'default_ministry': '38',
            'default_program': '150'
        }
    
    def process_files(self, ppes_path: str, dpp18_path: str, bud45_path: str,
                     year: int, ministry_code: str, program_code: str,
                     target_workbook: openpyxl.Workbook) -> openpyxl.Workbook:
        """Traite les fichiers BPSS et met à jour le workbook cible"""
        try:
            # Charger les données
            logger.info("Chargement des fichiers BPSS...")
            
            # PP-E-S
            sheet_names = self._get_sheet_names(ministry_code, program_code)
            df_pp_categ = pd.read_excel(ppes_path, sheet_name=sheet_names['pp_categ'])
            df_entrants = pd.read_excel(ppes_path, sheet_name=sheet_names['entrants'])
            df_sortants = pd.read_excel(ppes_path, sheet_name=sheet_names['sortants'])
            
            # DPP18 et BUD45
            df_dpp18 = pd.read_excel(dpp18_path)
            df_bud45 = pd.read_excel(bud45_path)
            
            # Appliquer les traitements
            target_workbook = self._load_ppes_data(
                target_workbook, df_pp_categ, df_entrants, df_sortants, program_code
            )
            target_workbook = self._load_dpp18_data(
                target_workbook, df_dpp18, program_code
            )
            target_workbook = self._load_bud45_data(
                target_workbook, df_bud45, program_code
            )
            
            logger.info("Traitement BPSS terminé")
            return target_workbook
            
        except Exception as e:
            logger.error(f"Erreur traitement BPSS: {str(e)}")
            raise
    
    def _get_sheet_names(self, ministry_code: str, program_code: str) -> Dict[str, str]:
        """Génère les noms de feuilles selon les codes"""
        return {
            'pp_categ': f"MIN_{ministry_code}_DETAIL_Prog_PP_CATEG",
            'entrants': f"MIN_{ministry_code}_DETAIL_Prog_Entrants",
            'sortants': f"MIN_{ministry_code}_DETAIL_Prog_Sortants"
        }
    
    def _load_ppes_data(self, wb: openpyxl.Workbook, df_pp_categ: pd.DataFrame,
                       df_entrants: pd.DataFrame, df_sortants: pd.DataFrame,
                       program_code: str) -> openpyxl.Workbook:
        """Charge les données PP-E-S dans le workbook"""
        # Filtrer par programme
        code_prefix = program_code[:3]
        
        df1 = df_pp_categ[df_pp_categ['nom_prog'].astype(str).str[:3] == code_prefix]
        df2 = df_entrants[df_entrants['nom_prog'].astype(str).str[:3] == code_prefix]
        df3 = df_sortants[df_sortants['nom_prog'].astype(str).str[:3] == code_prefix]
        
        # Créer ou obtenir la feuille
        sheet_name = "Données PP-E-S"
        if sheet_name not in wb.sheetnames:
            wb.create_sheet(sheet_name)
        
        sheet = wb[sheet_name]
        
        # Écrire les données
        start_rows = [7, 113, 218]  # Positions de départ
        dataframes = [df1, df2, df3]
        
        for start_row, df in zip(start_rows, dataframes):
            for r_idx, row in enumerate(df.values):
                for c_idx, value in enumerate(row):
                    sheet.cell(row=start_row + r_idx, column=3 + c_idx, value=value)
        
        # Traitement spécial "Indicié"
        df_indicie = df1[df1.get('marqueur_masse_indiciaire', '') == 'Indicié']
        if not df_indicie.empty:
            if 'Accueil' not in wb.sheetnames:
                wb.create_sheet('Accueil')
            
            accueil_sheet = wb['Accueil']
            if len(df_indicie.columns) > 5:
                accueil_sheet.cell(row=43, column=2, value=df_indicie.iloc[0, 1])
                accueil_sheet.cell(row=43, column=3, value=df_indicie.iloc[0, 5])
        
        logger.info("Données PP-E-S chargées")
        return wb
    
    def _load_dpp18_data(self, wb: openpyxl.Workbook, df_dpp18: pd.DataFrame,
                        program_code: str) -> openpyxl.Workbook:
        """Charge les données DPP18 dans le workbook"""
        sheet_name = "INF DPP 18"
        if sheet_name not in wb.sheetnames:
            wb.create_sheet(sheet_name)
        
        sheet = wb[sheet_name]
        
        # Header (5 premières lignes)
        header = df_dpp18.head(5)
        for r_idx, row in enumerate(header.values):
            for c_idx, value in enumerate(row):
                sheet.cell(row=1 + r_idx, column=2 + c_idx, value=value)
        
        # Filtrage par programme
        code_prefix = program_code[:3]
        df_filtered = df_dpp18[
            df_dpp18.iloc[:, 0].astype(str).str.contains(code_prefix, na=False)
        ]
        
        # Écrire les données filtrées
        for r_idx, row in enumerate(df_filtered.values):
            for c_idx, value in enumerate(row):
                sheet.cell(row=6 + r_idx, column=2 + c_idx, value=value)
        
        logger.info("Données DPP18 chargées")
        return wb
    
    def _load_bud45_data(self, wb: openpyxl.Workbook, df_bud45: pd.DataFrame,
                        program_code: str) -> openpyxl.Workbook:
        """Charge les données BUD45 dans le workbook"""
        sheet_name = "INF BUD 45"
        if sheet_name not in wb.sheetnames:
            wb.create_sheet(sheet_name)
        
        sheet = wb[sheet_name]
        
        # Header
        header = df_bud45.head(5)
        for r_idx, row in enumerate(header.values):
            for c_idx, value in enumerate(row):
                sheet.cell(row=1 + r_idx, column=2 + c_idx, value=value)
        
        # Filtrage par programme (colonne 2)
        code_prefix = program_code[:3]
        if len(df_bud45.columns) > 1:
            df_filtered = df_bud45[
                df_bud45.iloc[:, 1].astype(str).str.contains(code_prefix, na=False)
            ]
            
            # Écrire les données filtrées
            for r_idx, row in enumerate(df_filtered.values):
                for c_idx, value in enumerate(row):
                    sheet.cell(row=6 + r_idx, column=2 + c_idx, value=value)
        
        logger.info("Données BUD45 chargées")
        return wb