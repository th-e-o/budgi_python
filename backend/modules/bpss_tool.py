import pandas as pd
from typing import Dict, Any
import logging
import os

# Assuming your builder is in this location
from backend.core.excel_handler.excel_update_builder import ExcelUpdateBuilder

logger = logging.getLogger(__name__)


class BPSSTool:
    """
    Outil BPSS pour traitement des fichiers budgétaires.
    This version uses the ExcelUpdateBuilder to generate a list of changes
    instead of modifying a workbook object directly.
    """

    def __init__(self):
        self.config = {
            'default_year': 2025,
            'default_ministry': '38',
            'default_program': '150'
        }

    def process_files(self, ppes_path: str, dpp18_path: str, bud45_path: str,
                      year: int, ministry_code: str, program_code: str) -> ExcelUpdateBuilder:
        """
        Processes BPSS files and returns an ExcelUpdateBuilder instance
        containing all the required modifications.
        """
        try:
            # Initialize the builder
            updates_builder = ExcelUpdateBuilder()

            # File verification (no changes here)
            for path, name in [(ppes_path, 'PP-E-S'), (dpp18_path, 'DPP18'), (bud45_path, 'BUD45')]:
                if not os.path.exists(path):
                    raise FileNotFoundError(f"File {name} not found: {path}")
                logger.info(f"File {name} found: {path}")

            # Load data into pandas DataFrames (no changes here)
            logger.info("Loading BPSS files into memory...")
            df_pp_categ, df_entrants, df_sortants = self._load_ppes_dataframes(ppes_path, ministry_code, program_code)
            df_dpp18 = self._load_generic_dataframe(dpp18_path, 'DPP18')
            df_bud45 = self._load_generic_dataframe(bud45_path, 'BUD45')

            # Populate the builder with update operations
            self._create_ppes_updates(updates_builder, df_pp_categ, df_entrants, df_sortants, program_code)
            self._create_dpp18_updates(updates_builder, df_dpp18, program_code)
            self._create_bud45_updates(updates_builder, df_bud45, program_code)

            logger.info(f"BPSS processing complete. Generated {len(updates_builder.updates)} update operations.")
            return updates_builder

        except Exception as e:
            logger.error(f"Error during BPSS processing: {str(e)}", exc_info=True)
            raise

    def _get_sheet_names(self, ministry_code: str, program_code: str) -> Dict[str, str]:
        """Generates the expected sheet names for the PP-E-S file."""
        return {
            'pp_categ': f"MIN_{ministry_code}_DETAIL_Prog_PP_CATEG",
            'entrants': f"MIN_{ministry_code}_DETAIL_Prog_Entrants",
            'sortants': f"MIN_{ministry_code}_DETAIL_Prog_Sortants"
        }

    def _load_ppes_dataframes(self, ppes_path, ministry_code, program_code):
        """Loads all three required DataFrames from the PP-E-S Excel file."""
        sheet_names = self._get_sheet_names(ministry_code, program_code)
        try:
            df_pp_categ = pd.read_excel(ppes_path, sheet_name=sheet_names['pp_categ'])
            df_entrants = pd.read_excel(ppes_path, sheet_name=sheet_names['entrants'])
            df_sortants = pd.read_excel(ppes_path, sheet_name=sheet_names['sortants'])
            return df_pp_categ, df_entrants, df_sortants
        except Exception as e:
            logger.warning(f"Could not load PP-E-S with calculated sheet names: {str(e)}. Falling back to discovery.")
            xl_file = pd.ExcelFile(ppes_path)
            available_sheets = xl_file.sheet_names

            # Fallback
            pp_categ_sheet = next((s for s in available_sheets if 'pp_categ' in s.lower() or 'categ' in s.lower()),
                                  available_sheets[0])
            entrants_sheet = next((s for s in available_sheets if 'entrant' in s.lower()), available_sheets[1])
            sortants_sheet = next((s for s in available_sheets if 'sortant' in s.lower()), available_sheets[2])

            logger.info(f"Using discovered sheets: {pp_categ_sheet}, {entrants_sheet}, {sortants_sheet}")
            df_pp_categ = pd.read_excel(ppes_path, sheet_name=pp_categ_sheet)
            df_entrants = pd.read_excel(ppes_path, sheet_name=entrants_sheet)
            df_sortants = pd.read_excel(ppes_path, sheet_name=sortants_sheet)
            return df_pp_categ, df_entrants, df_sortants

    def _load_generic_dataframe(self, file_path, file_id):
        """Loads a DataFrame from an Excel file, robustly handling errors."""
        try:
            return pd.read_excel(file_path)
        except Exception as e:
            logger.warning(f"Error loading {file_id}: {str(e)}. Attempting to load first sheet explicitly.")
            return pd.read_excel(file_path, sheet_name=0)

    def _create_ppes_updates(self, builder: ExcelUpdateBuilder, df_pp_categ: pd.DataFrame,
                             df_entrants: pd.DataFrame, df_sortants: pd.DataFrame,
                             program_code: str):
        """Generates update operations for PP-E-S data."""
        sheet_name = "Données PP-E-S"
        builder.create_sheet_if_not_exists(sheet_name)

        code_prefix = program_code[:3]
        df1 = df_pp_categ[df_pp_categ['nom_prog'].astype(str).str[:3] == code_prefix]
        df2 = df_entrants[df_entrants['nom_prog'].astype(str).str[:3] == code_prefix]
        df3 = df_sortants[df_sortants['nom_prog'].astype(str).str[:3] == code_prefix]

        # openpyxl is 1-based, builder is 0-based.
        start_rows = [7, 113, 218]  # 1-based start rows in Excel
        dataframes = [df1, df2, df3]

        for start_row, df in zip(start_rows, dataframes):
            df_limited = df.head(100)
            for r_idx, row_data in enumerate(df_limited.values):
                for c_idx, value in enumerate(row_data):
                    # Convert to 0-based index for the builder
                    # Destination starts at column B (index 1)
                    builder.update_cell_value(sheet_name,
                                              row=(start_row - 1) + r_idx,
                                              column=1 + c_idx,
                                              value=value)

        # --- "Indicié" Special Treatment ---
        df_indicie = df1[df1.iloc[:, 3] == 'Indicié'] if len(df1.columns) > 3 else pd.DataFrame()  # Safer access
        if df_indicie.empty:
            logger.warning("No 'Indicié' data found in PP-E-S source.")
        else:
            builder.create_sheet_if_not_exists("Accueil")
            # Clear old data in range B43:C54
            for r in range(43, 55):  # 1-based Excel rows
                builder.update_cell_value("Accueil", row=r - 1, column=1, value=None)  # Col B
                builder.update_cell_value("Accueil", row=r - 1, column=2, value=None)  # Col C

            # Write new data
            row_dest = 43  # 1-based
            for _, row_data in df_indicie.iterrows():
                if row_dest > 54: break
                code_categorie = row_data.get('code_categorie')
                nom_categorie = row_data.get('nom_categorie')
                if code_categorie and nom_categorie:
                    builder.update_cell_value("Accueil", row=row_dest - 1, column=1, value=str(code_categorie))
                    builder.update_cell_value("Accueil", row=row_dest - 1, column=2, value=str(nom_categorie))
                    row_dest += 1

        logger.info("Generated update operations for PP-E-S data.")

    def _create_dpp18_updates(self, builder: ExcelUpdateBuilder, df_dpp18: pd.DataFrame, program_code: str):
        """Generates update operations for DPP18 data."""
        sheet_name = "INF DPP 18"
        builder.create_sheet_if_not_exists(sheet_name)

        # Write header (first 5 rows), starting from column B (index 1)
        header = df_dpp18.head(5)
        for r_idx, row_data in enumerate(header.values):
            for c_idx, value in enumerate(row_data):
                builder.update_cell_value(sheet_name, row=r_idx, column=1 + c_idx, value=value)

        # Filter and write data, starting from row 6 (index 5)
        code_prefix = program_code[:3]
        df_filtered = df_dpp18[df_dpp18.iloc[:, 0].astype(str).str.contains(code_prefix, na=False)]
        for r_idx, row_data in enumerate(df_filtered.values):
            for c_idx, value in enumerate(row_data):
                builder.update_cell_value(sheet_name, row=5 + r_idx, column=1 + c_idx, value=value)

        logger.info("Generated update operations for DPP18 data.")

    def _create_bud45_updates(self, builder: ExcelUpdateBuilder, df_bud45: pd.DataFrame, program_code: str):
        """Generates update operations for BUD45 data."""
        sheet_name = "INF BUD 45"
        builder.create_sheet_if_not_exists(sheet_name)

        # Write header (first 5 rows), starting from column B (index 1)
        header = df_bud45.head(5)
        for r_idx, row_data in enumerate(header.values):
            for c_idx, value in enumerate(row_data):
                builder.update_cell_value(sheet_name, row=r_idx, column=1 + c_idx, value=value)

        # Filter and write data, starting from row 6 (index 5)
        code_prefix = program_code[:3]
        if len(df_bud45.columns) > 1:
            df_filtered = df_bud45[df_bud45.iloc[:, 1].astype(str).str.contains(code_prefix, na=False)]
            for r_idx, row_data in enumerate(df_filtered.values):
                for c_idx, value in enumerate(row_data):
                    builder.update_cell_value(sheet_name, row=5 + r_idx, column=1 + c_idx, value=value)

        logger.info("Generated update operations for BUD45 data.")