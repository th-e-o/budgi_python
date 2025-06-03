import openpyxl
import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple, Optional, Any, Set
import concurrent.futures
from dataclasses import dataclass
import logging
from functools import lru_cache
import gc
from tqdm import tqdm
from collections import defaultdict
import ast
import operator

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
    python_code: Optional[str] = None
    dependencies: List[str] = None
    value: Any = None
    error: Optional[str] = None

class ExcelFormulaParser:
    """Parseur de formules Excel optimisé - implémentation complète basée sur le parseur R"""
    
    def __init__(self, config: Optional[ParserConfig] = None):
        self.config = config or ParserConfig()
        self._ref_cache = {}
        self._formula_converters = self._init_converters()
        self._named_ranges = {}
        self._sheets_data = {}
        
    def _init_converters(self) -> Dict:
        """Initialise les convertisseurs de formules"""
        return {
            'SUM': self._convert_sum,
            'MAX': self._convert_max,
            'MIN': self._convert_min,
            'AVERAGE': self._convert_average,
            'COUNT': self._convert_count,
            'COUNTA': self._convert_counta,
            'ROUND': self._convert_round,
            'INT': self._convert_int,
            'IF': self._convert_if,
            'SUMIF': self._convert_sumif,
            'IFERROR': self._convert_iferror,
            'TEXT': self._convert_text,
            'CONCATENATE': self._convert_concatenate,
            'AND': self._convert_and,
            'OR': self._convert_or,
            'NOT': self._convert_not,
            'ISBLANK': self._convert_isblank,
            'DATE': self._convert_date,
            'OFFSET': self._convert_offset,
            'INDIRECT': self._convert_indirect,
            'VLOOKUP': self._convert_vlookup,
            'INDEX': self._convert_index,
            'MATCH': self._convert_match,
            'LEN': self._convert_len,
            'TRIM': self._convert_trim,
            'UPPER': self._convert_upper,
            'LOWER': self._convert_lower,
            'MID': self._convert_mid,
            'SUBSTITUTE': self._convert_substitute,
            'ABS': self._convert_abs,
            'SQRT': self._convert_sqrt,
            'POWER': self._convert_power,
            'MOD': self._convert_mod,
        }
    
    @lru_cache(maxsize=10000)
    def excel_col_to_num(self, col_str: str) -> int:
        """Convertit une colonne Excel (A, AB, etc.) en numéro (1-based)"""
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
        wb = openpyxl.load_workbook(file_path, data_only=False, keep_vba=False)
        
        # Charger les named ranges
        self._load_named_ranges(wb)
        
        # Charger toutes les données des feuilles pour référence
        self._load_sheets_data(wb)
        
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
        
        # Extraire les dépendances
        for formula in filtered_formulas:
            formula.dependencies = self._extract_dependencies(formula)
        
        # Ordonner les formules selon les dépendances
        ordered_formulas = self._topological_sort(filtered_formulas)
        
        # Convertir les formules
        if self.config.progress_enabled:
            converted_formulas = self._convert_formulas_with_progress(ordered_formulas)
        else:
            converted_formulas = self._convert_formulas_batch(ordered_formulas)
        
        # Générer le script si demandé
        script_file = None
        if emit_script and converted_formulas:
            script_file = self._generate_python_script(converted_formulas, file_path)
        
        # Statistiques
        success_count = sum(1 for f in converted_formulas if f.python_code and not f.error)
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
    
    def _load_named_ranges(self, wb):
        """Charge les plages nommées du workbook"""
        self._named_ranges = {}
        if hasattr(wb, 'defined_names'):
            for name in wb.defined_names:
                # Extraire la référence
                if hasattr(name, 'value'):
                    self._named_ranges[name.name] = name.value
    
    def _load_sheets_data(self, wb):
        """Charge toutes les données des feuilles pour référence"""
        self._sheets_data = {}
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            # Créer un DataFrame pour chaque feuille
            data = []
            for row in sheet.iter_rows(values_only=True):
                data.append(list(row))
            if data:
                self._sheets_data[sheet_name] = pd.DataFrame(data)
            else:
                self._sheets_data[sheet_name] = pd.DataFrame()
    
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
            has_error = any(error in formula.formula for error in error_patterns)
            if not has_error:
                filtered.append(formula)
            else:
                formula.error = "Contains Excel error"
                filtered.append(formula)  # On garde mais on marque l'erreur
        
        return filtered
    
    def _extract_dependencies(self, formula: FormulaCell) -> List[str]:
        """Extrait les dépendances d'une formule"""
        dependencies = []
        
        # Pattern pour les références de cellules
        # Sheet!Cell ou Cell
        pattern = r"(?:(?:'[^']+'|[A-Za-z0-9_]+)!)?([A-Z]+[0-9]+)(?::([A-Z]+[0-9]+))?"
        
        matches = re.finditer(pattern, formula.formula)
        for match in matches:
            full_match = match.group(0)
            
            # Déterminer la feuille
            if '!' in full_match:
                sheet_part = full_match.split('!')[0].strip("'")
            else:
                sheet_part = formula.sheet
            
            # Extraire les cellules
            cell1 = match.group(1)
            cell2 = match.group(2)
            
            if cell2:  # C'est une plage
                # Calculer toutes les cellules dans la plage
                col1 = re.match(r'([A-Z]+)', cell1).group(1)
                row1 = int(re.match(r'[A-Z]+(\d+)', cell1).group(1))
                col2 = re.match(r'([A-Z]+)', cell2).group(1)
                row2 = int(re.match(r'[A-Z]+(\d+)', cell2).group(1))
                
                col1_num = self.excel_col_to_num(col1)
                col2_num = self.excel_col_to_num(col2)
                
                for r in range(min(row1, row2), max(row1, row2) + 1):
                    for c in range(min(col1_num, col2_num), max(col1_num, col2_num) + 1):
                        col_letter = self._num_to_col(c)
                        dependencies.append(f"{sheet_part}!{col_letter}{r}")
            else:
                dependencies.append(f"{sheet_part}!{cell1}")
        
        # Dédupliquer
        return list(set(dependencies))
    
    def _num_to_col(self, num: int) -> str:
        """Convertit un numéro de colonne en lettre Excel"""
        result = ""
        while num > 0:
            num -= 1
            result = chr(num % 26 + ord('A')) + result
            num //= 26
        return result
    
    def _topological_sort(self, formulas: List[FormulaCell]) -> List[FormulaCell]:
        """Trie les formules selon leurs dépendances"""
        # Créer un mapping des adresses vers les formules
        formula_map = {}
        for formula in formulas:
            key = f"{formula.sheet}!{formula.address}"
            formula_map[key] = formula
        
        # Créer le graphe de dépendances
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        for formula in formulas:
            key = f"{formula.sheet}!{formula.address}"
            in_degree[key] = 0
        
        for formula in formulas:
            key = f"{formula.sheet}!{formula.address}"
            for dep in formula.dependencies:
                if dep in formula_map:
                    graph[dep].append(key)
                    in_degree[key] += 1
        
        # Tri topologique
        queue = [key for key in in_degree if in_degree[key] == 0]
        sorted_formulas = []
        
        while queue:
            current = queue.pop(0)
            if current in formula_map:
                sorted_formulas.append(formula_map[current])
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Ajouter les formules restantes (cycles potentiels)
        for formula in formulas:
            if formula not in sorted_formulas:
                sorted_formulas.append(formula)
        
        return sorted_formulas
    
    def _convert_formulas_with_progress(self, formulas: List[FormulaCell]) -> List[FormulaCell]:
        """Convertit les formules avec une barre de progression"""
        with tqdm(total=len(formulas), desc="Converting formulas") as pbar:
            for formula in formulas:
                self._convert_single_formula(formula)
                pbar.update(1)
        
        return formulas
    
    def _convert_formulas_batch(self, formulas: List[FormulaCell]) -> List[FormulaCell]:
        """Convertit un batch de formules"""
        for formula in formulas:
            self._convert_single_formula(formula)
        
        return formulas
    
    def _convert_single_formula(self, formula_cell: FormulaCell):
        """Convertit une formule Excel en code Python"""
        try:
            formula_cell.python_code = self._parse_formula(
                formula_cell.formula, 
                formula_cell.sheet
            )
        except Exception as e:
            formula_cell.error = str(e)
            formula_cell.python_code = f"# Error: {str(e)}"
    
    def _parse_formula(self, formula: str, current_sheet: str) -> str:
        """Parse et convertit une formule Excel en Python"""
        # Nettoyer la formule
        formula = formula.strip()
        
        # Si c'est un nombre ou une chaîne
        if self._is_number(formula):
            return formula
        elif formula.startswith('"') and formula.endswith('"'):
            return formula
        elif formula in ['TRUE', 'FALSE']:
            return formula.title()
        
        # Gérer les pourcentages
        if formula.endswith('%'):
            num = formula[:-1]
            if self._is_number(num):
                return f"({num}/100)"
        
        # Chercher les opérateurs binaires (dans l'ordre de priorité inverse)
        for ops in [['&'], ['+', '-'], ['*', '/'], ['=', '<>', '<=', '>=', '<', '>']]:
            result = self._try_split_binary(formula, ops, current_sheet)
            if result:
                return result
        
        # Si c'est une référence de cellule ou une plage
        if self._is_cell_reference(formula):
            return self._convert_cell_reference(formula, current_sheet)
        
        # Si c'est une fonction
        if '(' in formula:
            return self._parse_function(formula, current_sheet)
        
        # Sinon, c'est peut-être un nom défini
        if formula in self._named_ranges:
            return self._convert_cell_reference(self._named_ranges[formula], current_sheet)
        
        # Par défaut
        return f'"{formula}"'
    
    def _is_number(self, s: str) -> bool:
        """Vérifie si une chaîne est un nombre"""
        try:
            float(s)
            return True
        except ValueError:
            return False
    
    def _is_cell_reference(self, s: str) -> bool:
        """Vérifie si c'est une référence de cellule"""
        # Simple référence A1 ou plage A1:B2
        if re.match(r'^[A-Z]+\d+(?::[A-Z]+\d+)?$', s):
            return True
        # Avec feuille Sheet!A1 ou 'Sheet'!A1
        if re.match(r"^(?:'[^']+'|[A-Za-z0-9_]+)![A-Z]+\d+(?::[A-Z]+\d+)?$", s):
            return True
        return False
    
    def _try_split_binary(self, formula: str, operators: List[str], current_sheet: str) -> Optional[str]:
        """Essaie de diviser la formule sur un opérateur binaire"""
        # Parser en respectant les parenthèses et les guillemets
        depth = 0
        in_string = False
        quote_char = None
        
        for i in range(len(formula)):
            char = formula[i]
            
            # Gestion des chaînes
            if not in_string and char in ['"', "'"]:
                in_string = True
                quote_char = char
            elif in_string and char == quote_char:
                # Vérifier si c'est un guillemet échappé
                if i + 1 < len(formula) and formula[i + 1] == quote_char:
                    continue
                in_string = False
                quote_char = None
            elif in_string:
                continue
            
            # Gestion des parenthèses
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            
            # Si on est au niveau racine, chercher les opérateurs
            if depth == 0 and not in_string:
                for op in operators:
                    if formula[i:i+len(op)] == op:
                        left = formula[:i].strip()
                        right = formula[i+len(op):].strip()
                        
                        if left and right:
                            left_py = self._parse_formula(left, current_sheet)
                            right_py = self._parse_formula(right, current_sheet)
                            
                            # Mapper les opérateurs Excel vers Python
                            if op == '&':
                                return f'str({left_py}) + str({right_py})'
                            elif op == '<>':
                                return f'{left_py} != {right_py}'
                            elif op == '=':
                                return f'{left_py} == {right_py}'
                            else:
                                return f'{left_py} {op} {right_py}'
        
        return None
    
    def _parse_function(self, formula: str, current_sheet: str) -> str:
        """Parse une fonction Excel"""
        match = re.match(r'^([A-Z]+)\((.*)\)$', formula, re.IGNORECASE)
        if not match:
            return f'# Invalid function: {formula}'
        
        func_name = match.group(1).upper()
        args_str = match.group(2)
        
        # Parser les arguments
        args = self._split_arguments(args_str)
        
        # Convertir chaque argument
        converted_args = []
        for arg in args:
            converted_args.append(self._parse_formula(arg.strip(), current_sheet))
        
        # Utiliser le convertisseur approprié
        if func_name in self._formula_converters:
            return self._formula_converters[func_name](converted_args, current_sheet, args)
        else:
            # Fonction non supportée, essayer un appel générique
            return f"{func_name.lower()}({', '.join(converted_args)})"
    
    def _split_arguments(self, args_str: str) -> List[str]:
        """Divise les arguments d'une fonction en respectant les parenthèses"""
        if not args_str:
            return []
        
        args = []
        current_arg = ""
        depth = 0
        in_string = False
        quote_char = None
        
        for char in args_str:
            if not in_string and char in ['"', "'"]:
                in_string = True
                quote_char = char
            elif in_string and char == quote_char:
                in_string = False
                quote_char = None
            elif not in_string:
                if char == '(':
                    depth += 1
                elif char == ')':
                    depth -= 1
                elif char == ',' and depth == 0:
                    args.append(current_arg)
                    current_arg = ""
                    continue
            
            current_arg += char
        
        if current_arg:
            args.append(current_arg)
        
        return args
    
    def _convert_cell_reference(self, ref: str, current_sheet: str) -> str:
        """Convertit une référence de cellule Excel en code Python"""
        # Gérer les références avec feuille
        sheet = current_sheet
        cell_part = ref
        
        if '!' in ref:
            sheet_part, cell_part = ref.split('!', 1)
            sheet = sheet_part.strip("'")
        
        # Si c'est une plage
        if ':' in cell_part:
            start, end = cell_part.split(':')
            return self._convert_range_reference(start, end, sheet)
        
        # Référence simple
        match = re.match(r'^([A-Z]+)(\d+)$', cell_part)
        if match:
            col_str, row_str = match.groups()
            col = self.excel_col_to_num(col_str)
            row = int(row_str)
            
            if sheet == current_sheet:
                return f"ws.iloc[{row-1}, {col-1}]"
            else:
                return f"sheets['{sheet}'].iloc[{row-1}, {col-1}]"
        
        return f"# Invalid ref: {ref}"
    
    def _convert_range_reference(self, start: str, end: str, sheet: str) -> str:
        """Convertit une plage Excel en slice Python"""
        start_match = re.match(r'^([A-Z]+)(\d+)$', start)
        end_match = re.match(r'^([A-Z]+)(\d+)$', end)
        
        if start_match and end_match:
            start_col = self.excel_col_to_num(start_match.group(1))
            start_row = int(start_match.group(2))
            end_col = self.excel_col_to_num(end_match.group(1))
            end_row = int(end_match.group(2))
            
            return f"sheets['{sheet}'].iloc[{start_row-1}:{end_row}, {start_col-1}:{end_col}]"
        
        return f"# Invalid range: {start}:{end}"
    
    # Convertisseurs de fonctions
    def _convert_sum(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        if len(args) == 1:
            return f"np.nansum({args[0]})"
        else:
            return f"np.nansum([{', '.join(args)}])"
    
    def _convert_average(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        if len(args) == 1:
            return f"np.nanmean({args[0]})"
        else:
            return f"np.nanmean([{', '.join(args)}])"
    
    def _convert_max(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        if len(args) == 1:
            return f"np.nanmax({args[0]})"
        else:
            return f"np.nanmax([{', '.join(args)}])"
    
    def _convert_min(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        if len(args) == 1:
            return f"np.nanmin({args[0]})"
        else:
            return f"np.nanmin([{', '.join(args)}])"
    
    def _convert_count(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        if len(args) == 1:
            return f"np.count_nonzero(~np.isnan({args[0]}.values.flatten()))"
        else:
            return f"sum(not pd.isna(x) for x in [{', '.join(args)}])"
    
    def _convert_counta(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        if len(args) == 1:
            return f"np.count_nonzero({args[0]}.values.flatten() != '')"
        else:
            return f"sum(x != '' and x is not None for x in [{', '.join(args)}])"
    
    def _convert_round(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        if len(args) >= 2:
            return f"np.round({args[0]}, {args[1]})"
        else:
            return f"np.round({args[0]})"
    
    def _convert_int(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        return f"int({args[0]})"
    
    def _convert_if(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        if len(args) >= 3:
            return f"({args[1]} if {args[0]} else {args[2]})"
        elif len(args) == 2:
            return f"({args[1]} if {args[0]} else '')"
        else:
            return "# Invalid IF"
    
    def _convert_sumif(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        """Convertit SUMIF - basé sur la logique R"""
        if len(args) < 2:
            return "# SUMIF requires at least 2 arguments"
        
        range_arg = args[0]
        criteria_raw = raw_args[1].strip()
        sum_range = args[2] if len(args) >= 3 else range_arg
        
        # Analyser le critère
        criteria_code = self._convert_sumif_criteria(criteria_raw, range_arg, current_sheet)
        
        return f"np.nansum({sum_range}.values[{criteria_code}])"
    
    def _convert_sumif_criteria(self, criteria: str, range_ref: str, current_sheet: str) -> str:
        """Convertit un critère SUMIF en condition Python"""
        criteria = criteria.strip()
        
        # Critères de comparaison
        if criteria.startswith(('>', '<', '=')):
            op_match = re.match(r'^([><=]+)(.*)$', criteria)
            if op_match:
                op, value = op_match.groups()
                if op == '=':
                    op = '=='
                
                # Si c'est un nombre
                if self._is_number(value):
                    return f"{range_ref}.values {op} {value}"
                else:
                    # C'est une chaîne
                    return f"{range_ref}.values {op} {self._parse_formula(value, current_sheet)}"
        
        # Wildcard patterns (* et ?)
        if '*' in criteria or '?' in criteria:
            # Convertir en regex
            pattern = criteria.replace('*', '.*').replace('?', '.')
            return f"{range_ref}.astype(str).str.match('{pattern}')"
        
        # Référence de cellule
        if self._is_cell_reference(criteria):
            ref_value = self._parse_formula(criteria, current_sheet)
            return f"{range_ref}.values == {ref_value}"
        
        # Valeur simple
        if self._is_number(criteria):
            return f"{range_ref}.values == {criteria}"
        else:
            # Chaîne
            criteria_clean = criteria.strip('"')
            return f"{range_ref}.values == '{criteria_clean}'"
    
    def _convert_iferror(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        if len(args) >= 2:
            return f"(lambda: {args[1]} if pd.isna({args[0]}) or isinstance({args[0]}, Exception) else {args[0]})()"
        else:
            return "# Invalid IFERROR"
    
    def _convert_text(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        return f"str({args[0]})"
    
    def _convert_concatenate(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        return f"''.join(str(x) for x in [{', '.join(args)}])"
    
    def _convert_and(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        return f"({' and '.join(args)})"
    
    def _convert_or(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        return f"({' or '.join(args)})"
    
    def _convert_not(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        return f"(not {args[0]})"
    
    def _convert_isblank(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        return f"(pd.isna({args[0]}) or {args[0]} == '')"
    
    def _convert_date(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        if len(args) >= 3:
            return f"pd.Timestamp({args[0]}, {args[1]}, {args[2]})"
        else:
            return "# Invalid DATE"
    
    def _convert_offset(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        """Convertit OFFSET - basé sur la logique R"""
        if len(args) < 3:
            return "# OFFSET requires at least 3 arguments"
        
        # Parser la référence de base
        base_ref = raw_args[0].strip()
        row_offset = args[1]
        col_offset = args[2]
        
        # Extraire les coordonnées de base
        if '!' in base_ref:
            sheet, cell = base_ref.split('!', 1)
            sheet = sheet.strip("'")
        else:
            sheet = current_sheet
            cell = base_ref
        
        match = re.match(r'^([A-Z]+)(\d+)$', cell)
        if match:
            base_col = self.excel_col_to_num(match.group(1))
            base_row = int(match.group(2))
            
            return f"sheets['{sheet}'].iloc[{base_row-1} + ({row_offset}), {base_col-1} + ({col_offset})]"
        
        return "# Invalid OFFSET reference"
    
    def _convert_indirect(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        # INDIRECT est complexe car il évalue dynamiquement
        return f"eval({args[0]})"  # Attention: utiliser avec précaution
    
    def _convert_vlookup(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        if len(args) < 3:
            return "# VLOOKUP requires at least 3 arguments"
        
        lookup_value = args[0]
        table_array = args[1]
        col_index = args[2]
        range_lookup = args[3] if len(args) > 3 else "True"
        
        return f"vlookup({lookup_value}, {table_array}, {col_index}, {range_lookup})"
    
    def _convert_index(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        if len(args) >= 2:
            return f"{args[0]}.iloc[{args[1]}-1" + (f", {args[2]}-1]" if len(args) > 2 else "]")
        return "# Invalid INDEX"
    
    def _convert_match(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        if len(args) >= 2:
            lookup_value = args[0]
            lookup_array = args[1]
            match_type = args[2] if len(args) > 2 else "1"
            
            return f"match_index({lookup_value}, {lookup_array}, {match_type})"
        return "# Invalid MATCH"
    
    def _convert_len(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        return f"len(str({args[0]}))"
    
    def _convert_trim(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        return f"str({args[0]}).strip()"
    
    def _convert_upper(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        return f"str({args[0]}).upper()"
    
    def _convert_lower(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        return f"str({args[0]}).lower()"
    
    def _convert_mid(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        if len(args) >= 3:
            text = args[0]
            start = args[1]
            length = args[2]
            return f"str({text})[{start}-1:{start}-1+{length}]"
        return "# Invalid MID"
    
    def _convert_substitute(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        if len(args) >= 3:
            text = args[0]
            old = args[1]
            new = args[2]
            instance = args[3] if len(args) > 3 else None
            
            if instance:
                return f"substitute({text}, {old}, {new}, {instance})"
            else:
                return f"str({text}).replace({old}, {new})"
        return "# Invalid SUBSTITUTE"
    
    def _convert_abs(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        return f"abs({args[0]})"
    
    def _convert_sqrt(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        return f"np.sqrt({args[0]})"
    
    def _convert_power(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        if len(args) >= 2:
            return f"pow({args[0]}, {args[1]})"
        return "# Invalid POWER"
    
    def _convert_mod(self, args: List[str], current_sheet: str, raw_args: List[str]) -> str:
        if len(args) >= 2:
            return f"({args[0]} % {args[1]})"
        return "# Invalid MOD"
    
    def _generate_python_script(self, formulas: List[FormulaCell], original_file: str) -> str:
        """Génère un script Python pour appliquer les formules"""
        script_name = original_file.replace('.xlsx', '_formulas.py')
        
        with open(script_name, 'w', encoding='utf-8') as f:
            f.write("""# Auto-generated Excel formula script
import pandas as pd
import numpy as np
import openpyxl
from datetime import datetime

# Helper functions
def vlookup(lookup_value, table_array, col_index, range_lookup=True):
    \"\"\"VLOOKUP implementation\"\"\"
    try:
        if range_lookup:
            # Approximate match
            idx = table_array.iloc[:, 0].searchsorted(lookup_value)
            if idx > 0:
                idx -= 1
        else:
            # Exact match
            mask = table_array.iloc[:, 0] == lookup_value
            if mask.any():
                idx = mask.idxmax()
            else:
                return np.nan
        
        return table_array.iloc[idx, col_index - 1]
    except:
        return np.nan

def match_index(lookup_value, lookup_array, match_type=1):
    \"\"\"MATCH implementation\"\"\"
    try:
        if match_type == 0:
            # Exact match
            return (lookup_array == lookup_value).idxmax() + 1
        elif match_type == 1:
            # Less than or equal
            return lookup_array[lookup_array <= lookup_value].idxmax() + 1
        else:
            # Greater than or equal
            return lookup_array[lookup_array >= lookup_value].idxmin() + 1
    except:
        return np.nan

def substitute(text, old, new, instance=None):
    \"\"\"SUBSTITUTE implementation\"\"\"
    text = str(text)
    if instance is None:
        return text.replace(old, new)
    else:
        parts = text.split(old)
        if len(parts) > instance:
            return old.join(parts[:instance]) + new + old.join(parts[instance:])
        return text

def apply_formulas(excel_file):
    \"\"\"Apply Excel formulas to the workbook\"\"\"
    # Load workbook
    wb = openpyxl.load_workbook(excel_file, data_only=False)
    
    # Load all sheets into DataFrames
    sheets = {}
    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]
        data = []
        for row in sheet.iter_rows(values_only=True):
            data.append(list(row))
        sheets[sheet_name] = pd.DataFrame(data)
    
    # Apply formulas
""")
            
            # Grouper par feuille
            from collections import defaultdict
            formulas_by_sheet = defaultdict(list)
            for formula in formulas:
                if formula.python_code and not formula.error:
                    formulas_by_sheet[formula.sheet].append(formula)
            
            # Générer le code pour chaque feuille
            for sheet_name, sheet_formulas in formulas_by_sheet.items():
                f.write(f"\n    # Sheet: {sheet_name}\n")
                f.write(f"    ws = sheets['{sheet_name}']\n")
                
                for formula in sheet_formulas:
                    f.write(f"    # {formula.address}: {formula.formula}\n")
                    f.write(f"    try:\n")
                    f.write(f"        result = {formula.python_code}\n")
                    f.write(f"        wb[\"{sheet_name}\"][\"{formula.address}\"].value = result\n")
                    f.write(f"        ws.iloc[{formula.row-1}, {formula.col-1}] = result\n")
                    f.write(f"    except Exception as e:\n")
                    f.write(f"        print(f'Error in {formula.address}: {{e}}')\n")
                    f.write(f"    \n")
            
            f.write("""
    # Save workbook
    output_file = excel_file.replace('.xlsx', '_calculated.xlsx')
    wb.save(output_file)
    wb.close()
    print(f"Formulas applied. Output saved to: {output_file}")
    return sheets

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        apply_formulas(sys.argv[1])
    else:
        print("Usage: python script.py <excel_file>")
""")
        
        logger.info(f"Generated script: {script_name}")
        return script_name

    def apply_formulas_to_workbook(self, workbook: openpyxl.Workbook, 
                                  formulas: List[FormulaCell]) -> openpyxl.Workbook:
        """Applique directement les formules au workbook"""
        # Charger toutes les feuilles en DataFrames
        sheets = {}
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            data = []
            for row in sheet.iter_rows(values_only=True):
                data.append(list(row))
            sheets[sheet_name] = pd.DataFrame(data) if data else pd.DataFrame()
        
        # Créer un environnement d'exécution
        exec_globals = {
            'sheets': sheets,
            'np': np,
            'pd': pd,
            'datetime': datetime,
            'vlookup': self._vlookup_impl,
            'match_index': self._match_index_impl,
            'substitute': self._substitute_impl,
        }
        
        # Appliquer chaque formule
        success_count = 0
        error_count = 0
        
        for formula in formulas:
            if formula.python_code and not formula.error:
                try:
                    # Créer un environnement local avec la feuille courante
                    exec_locals = {'ws': sheets[formula.sheet]}
                    
                    # Évaluer la formule
                    result = eval(formula.python_code, exec_globals, exec_locals)
                    
                    # Mettre à jour le workbook
                    sheet = workbook[formula.sheet]
                    sheet.cell(row=formula.row, column=formula.col, value=result)
                    
                    # Mettre à jour le DataFrame aussi
                    sheets[formula.sheet].iloc[formula.row-1, formula.col-1] = result
                    
                    formula.value = result
                    success_count += 1
                    
                except Exception as e:
                    formula.error = str(e)
                    error_count += 1
                    logger.error(f"Error in {formula.sheet}!{formula.address}: {str(e)}")
        
        logger.info(f"Applied formulas: {success_count} success, {error_count} errors")
        return workbook
    
    # Implémentations des fonctions helper
    @staticmethod
    def _vlookup_impl(lookup_value, table_array, col_index, range_lookup=True):
        """Implémentation de VLOOKUP"""
        try:
            if range_lookup:
                idx = table_array.iloc[:, 0].searchsorted(lookup_value)
                if idx > 0:
                    idx -= 1
            else:
                mask = table_array.iloc[:, 0] == lookup_value
                if mask.any():
                    idx = mask.idxmax()
                else:
                    return np.nan
            
            return table_array.iloc[idx, col_index - 1]
        except:
            return np.nan
    
    @staticmethod
    def _match_index_impl(lookup_value, lookup_array, match_type=1):
        """Implémentation de MATCH"""
        try:
            if match_type == 0:
                return (lookup_array == lookup_value).idxmax() + 1
            elif match_type == 1:
                return lookup_array[lookup_array <= lookup_value].idxmax() + 1
            else:
                return lookup_array[lookup_array >= lookup_value].idxmin() + 1
        except:
            return np.nan
    
    @staticmethod
    def _substitute_impl(text, old, new, instance=None):
        """Implémentation de SUBSTITUTE"""
        text = str(text)
        if instance is None:
            return text.replace(old, new)
        else:
            parts = text.split(old)
            if len(parts) > instance:
                return old.join(parts[:instance]) + new + old.join(parts[instance:])
            return text