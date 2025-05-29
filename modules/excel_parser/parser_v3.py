import openpyxl
import pandas as pd
import re
from typing import Dict, List, Tuple, Optional
import concurrent.futures
from dataclasses import dataclass
import logging
from functools import lru_cache
import gc
from tqdm import tqdm

logger = logging.getLogger(__name__)

@dataclass
class ParserConfig:
    chunk_size: int = 800
    max_memory_mb: int = 1024
    workers: int = 4
    cache_enabled: bool = True
    progress_enabled: bool = True

@dataclass
class FormulaCell:
    sheet: str
    address: str
    row: int
    col: int
    formula: str
    r_code: Optional[str] = None
    dependencies: List[str] = None

class ExcelFormulaParser:
    """Parseur de formules Excel optimisé pour gros fichiers"""
    
    def __init__(self, config: Optional[ParserConfig] = None):
        self.config = config or ParserConfig()
        self._ref_cache = {}
        self._formula_converters = self._init_converters()
    
    def _init_converters(self) -> Dict:
        """Initialise les convertisseurs de formules"""
        return {
            'SUM': self._convert_sum,
            'MAX': self._convert_max,
            'MIN': self._convert_min,
            'IF': self._convert_if,
            'SUMIF': self._convert_sumif,
            'AVERAGE': self._convert_average,
            'COUNT': self._convert_count,
            'ROUND': self._convert_round,
        }
    
    @lru_cache(maxsize=10000)
    def excel_col_to_num(self, col_str: str) -> int:
        """Convertit une colonne Excel (A, AB, etc.) en numéro"""
        if not col_str:
            return 1
        
        result = 0
        for char in col_str:
            result = result * 26 + ord(char) - ord('A') + 1
        return result
    
    def parse_excel_file(self, file_path: str, emit_script: bool = True) -> Dict:
        """Parse un fichier Excel et extrait les formules"""
        logger.info(f"Parsing Excel file: {file_path}")
        
        # Charger le workbook
        wb = openpyxl.load_workbook(file_path, data_only=False)
        
        # Extraire toutes les formules
        all_formulas = []
        
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            sheet_formulas = self._extract_sheet_formulas(sheet, sheet_name)
            all_formulas.extend(sheet_formulas)
        
        wb.close()
        
        logger.info(f"Found {len(all_formulas)} formulas")
        
        # Filtrer les erreurs Excel
        filtered_formulas = self._filter_excel_errors(all_formulas)
        logger.info(f"Filtered to {len(filtered_formulas)} valid formulas")
        
        # Convertir les formules
        if self.config.progress_enabled:
            converted_formulas = self._convert_formulas_with_progress(filtered_formulas)
        else:
            converted_formulas = self._convert_formulas_batch(filtered_formulas)
        
        # Générer le script si demandé
        script_file = None
        if emit_script and converted_formulas:
            script_file = self._generate_python_script(converted_formulas, file_path)
        
        # Statistiques
        success_count = sum(1 for f in converted_formulas if f.r_code and not f.r_code.startswith('#'))
        error_count = len(converted_formulas) - success_count
        
        return {
            'formulas': converted_formulas,
            'script_file': script_file,
            'statistics': {
                'total': len(all_formulas),
                'success': success_count,
                'errors': error_count,
                'success_rate': round(100 * success_count / len(all_formulas), 1) if all_formulas else 0
            }
        }
    
    def _extract_sheet_formulas(self, sheet, sheet_name: str) -> List[FormulaCell]:
        """Extrait les formules d'une feuille"""
        formulas = []
        
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value and isinstance(cell.value, str) and cell.value.startswith('='):
                    formula = FormulaCell(
                        sheet=sheet_name,
                        address=cell.coordinate,
                        row=cell.row,
                        col=cell.column,
                        formula=cell.value[1:]  # Enlever le '='
                    )
                    formulas.append(formula)
        
        return formulas
    
    def _filter_excel_errors(self, formulas: List[FormulaCell]) -> List[FormulaCell]:
        """Filtre les formules contenant des erreurs Excel"""
        error_patterns = [
            '#REF!', '#N/A', '#VALUE!', '#DIV/0!', 
            '#NAME?', '#NULL!', '#NUM!'
        ]
        
        filtered = []
        for formula in formulas:
            if not any(error in formula.formula for error in error_patterns):
                # Filtrer aussi les fonctions non supportées temporairement
                if not re.search(r'\b(LEFT|RIGHT|MID|VLOOKUP|HLOOKUP)\b', formula.formula, re.IGNORECASE):
                    filtered.append(formula)
        
        return filtered
    
    def _convert_formulas_with_progress(self, formulas: List[FormulaCell]) -> List[FormulaCell]:
        """Convertit les formules avec une barre de progression"""
        chunk_size = self.config.chunk_size
        chunks = [formulas[i:i + chunk_size] for i in range(0, len(formulas), chunk_size)]
        
        converted = []
        with tqdm(total=len(formulas), desc="Converting formulas") as pbar:
            for chunk in chunks:
                chunk_results = self._convert_formulas_batch(chunk)
                converted.extend(chunk_results)
                pbar.update(len(chunk))
                
                # Gestion mémoire
                if len(converted) % (chunk_size * 5) == 0:
                    gc.collect()
        
        return converted
    
    def _convert_formulas_batch(self, formulas: List[FormulaCell]) -> List[FormulaCell]:
        """Convertit un batch de formules"""
        if self.config.workers > 1 and len(formulas) > 100:
            # Conversion parallèle
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.workers) as executor:
                futures = []
                for formula in formulas:
                    future = executor.submit(self._convert_single_formula, formula)
                    futures.append((formula, future))
                
                for formula, future in futures:
                    try:
                        formula.r_code = future.result(timeout=5)
                    except Exception as e:
                        formula.r_code = f"# Error: {str(e)}"
        else:
            # Conversion séquentielle
            for formula in formulas:
                try:
                    formula.r_code = self._convert_single_formula(formula)
                except Exception as e:
                    formula.r_code = f"# Error: {str(e)}"
        
        return formulas
    
    def _convert_single_formula(self, formula_cell: FormulaCell) -> str:
        """Convertit une formule Excel en code Python"""
        formula = formula_cell.formula
        
        # Nettoyer la formule
        formula = formula.replace('$', '').strip()
        
        # Conversion selon le type
        if re.match(r'^[A-Z]+\d+$', formula):
            # Référence simple
            return self._convert_cell_reference(formula)
        elif re.match(r'^[A-Z]+\d+:[A-Z]+\d+$', formula):
            # Plage
            return self._convert_range_reference(formula)
        elif re.match(r'^\d+(\.\d+)?$', formula):
            # Nombre
            return formula
        else:
            # Formule complexe
            return self._convert_complex_formula(formula)
    
    def _convert_cell_reference(self, ref: str) -> str:
        """Convertit une référence de cellule (A1) en indices Python"""
        match = re.match(r'^([A-Z]+)(\d+)$', ref)
        if match:
            col_str, row_str = match.groups()
            col = self.excel_col_to_num(col_str)
            row = int(row_str)
            return f"df.iloc[{row-1}, {col-1}]"
        return f"# Invalid ref: {ref}"
    
    def _convert_range_reference(self, range_ref: str) -> str:
        """Convertit une plage (A1:B5) en slice Python"""
        match = re.match(r'^([A-Z]+)(\d+):([A-Z]+)(\d+)$', range_ref)
        if match:
            start_col_str, start_row_str, end_col_str, end_row_str = match.groups()
            start_col = self.excel_col_to_num(start_col_str)
            start_row = int(start_row_str)
            end_col = self.excel_col_to_num(end_col_str)
            end_row = int(end_row_str)
            return f"df.iloc[{start_row-1}:{end_row}, {start_col-1}:{end_col}]"
        return f"# Invalid range: {range_ref}"
    
    def _convert_complex_formula(self, formula: str) -> str:
        """Convertit une formule complexe"""
        # Identifier la fonction principale
        match = re.match(r'^([A-Z]+)\((.*)\)$', formula, re.IGNORECASE)
        if match:
            func_name = match.group(1).upper()
            args_str = match.group(2)
            
            if func_name in self._formula_converters:
                return self._formula_converters[func_name](args_str)
        
        # Si pas reconnu, essayer de convertir les références
        converted = formula
        
        # Remplacer les références de cellules
        cell_refs = re.findall(r'\b[A-Z]+\d+\b', formula)
        for ref in cell_refs:
            converted = converted.replace(ref, self._convert_cell_reference(ref))
        
        # Remplacer les plages
        range_refs = re.findall(r'\b[A-Z]+\d+:[A-Z]+\d+\b', formula)
        for ref in range_refs:
            converted = converted.replace(ref, self._convert_range_reference(ref))
        
        return converted
    
    def _convert_sum(self, args: str) -> str:
        """Convertit une fonction SUM"""
        converted_args = self._convert_complex_formula(args)
        return f"np.nansum({converted_args})"
    
    def _convert_max(self, args: str) -> str:
        """Convertit une fonction MAX"""
        converted_args = self._convert_complex_formula(args)
        return f"np.nanmax({converted_args})"
    
    def _convert_min(self, args: str) -> str:
        """Convertit une fonction MIN"""
        converted_args = self._convert_complex_formula(args)
        return f"np.nanmin({converted_args})"
    
    def _convert_if(self, args: str) -> str:
        """Convertit une fonction IF"""
        # Simplification - nécessiterait un parsing plus sophistiqué
        parts = self._split_function_args(args)
        if len(parts) >= 3:
            condition = self._convert_complex_formula(parts[0])
            true_val = self._convert_complex_formula(parts[1])
            false_val = self._convert_complex_formula(parts[2])
            return f"({true_val} if {condition} else {false_val})"
        return f"# Complex IF: {args}"
    
    def _convert_sumif(self, args: str) -> str:
        """Convertit une fonction SUMIF"""
        # Simplification
        return f"# SUMIF not fully implemented: {args}"
    
    def _convert_average(self, args: str) -> str:
        """Convertit une fonction AVERAGE"""
        converted_args = self._convert_complex_formula(args)
        return f"np.nanmean({converted_args})"
    
    def _convert_count(self, args: str) -> str:
        """Convertit une fonction COUNT"""
        converted_args = self._convert_complex_formula(args)
        return f"np.count_nonzero(~np.isnan({converted_args}))"
    
    def _convert_round(self, args: str) -> str:
        """Convertit une fonction ROUND"""
        parts = self._split_function_args(args)
        if len(parts) >= 2:
            value = self._convert_complex_formula(parts[0])
            decimals = parts[1]
            return f"np.round({value}, {decimals})"
        return f"np.round({self._convert_complex_formula(args)})"
    
    def _split_function_args(self, args: str) -> List[str]:
        """Divise les arguments d'une fonction en tenant compte des parenthèses"""
        result = []
        current = ""
        depth = 0
        
        for char in args:
            if char == '(' :
                depth += 1
            elif char == ')':
                depth -= 1
            elif char == ',' and depth == 0:
                result.append(current.strip())
                current = ""
                continue
            
            current += char
        
        if current:
            result.append(current.strip())
        
        return result
    
    def _generate_python_script(self, formulas: List[FormulaCell], original_file: str) -> str:
        """Génère un script Python pour appliquer les formules"""
        script_name = original_file.replace('.xlsx', '_formulas.py')
        
        with open(script_name, 'w', encoding='utf-8') as f:
            f.write("# Auto-generated Excel formula script\n")
            f.write("import pandas as pd\n")
            f.write("import numpy as np\n")
            f.write("import openpyxl\n\n")
            
            f.write("def apply_formulas(excel_file):\n")
            f.write("    # Load workbook\n")
            f.write("    wb = openpyxl.load_workbook(excel_file)\n")
            f.write("    sheets = {}\n\n")
            
            # Grouper par feuille
            from collections import defaultdict
            formulas_by_sheet = defaultdict(list)
            for formula in formulas:
                if formula.r_code and not formula.r_code.startswith('#'):
                    formulas_by_sheet[formula.sheet].append(formula)
            
            # Générer le code pour chaque feuille
            for sheet_name, sheet_formulas in formulas_by_sheet.items():
                f.write(f"    # Sheet: {sheet_name}\n")
                f.write(f"    if '{sheet_name}' in wb.sheetnames:\n")
                f.write(f"        sheet = wb['{sheet_name}']\n")
                f.write(f"        df = pd.DataFrame(sheet.values)\n")
                f.write(f"        \n")
                
                for formula in sheet_formulas:
                    f.write(f"        # {formula.address}: {formula.formula}\n")
                    f.write(f"        try:\n")
                    f.write(f"            sheet['{formula.address}'].value = {formula.r_code}\n")
                    f.write(f"        except Exception as e:\n")
                    f.write(f"            print(f'Error in {formula.address}: {{e}}')\n")
                    f.write(f"        \n")
                
                f.write(f"        sheets['{sheet_name}'] = df\n\n")
            
            f.write("    # Save workbook\n")
            f.write("    wb.save(excel_file.replace('.xlsx', '_calculated.xlsx'))\n")
            f.write("    wb.close()\n")
            f.write("    return sheets\n")
        
        logger.info(f"Generated script: {script_name}")
        return script_name