# modules/budget_mapper.py
import pandas as pd
from typing import List, Dict, Optional, Tuple
import logging
import re

logger = logging.getLogger(__name__)

class BudgetMapper:
    """Module pour mapper les entrées budgétaires aux cellules Excel"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
    
    async def map_entries_to_cells(self, entries: List[Dict], tags: List[Dict]) -> List[Dict]:
        """Mappe les entrées budgétaires aux cellules Excel via les tags"""
        if not entries or not tags:
            return []
        
        # Formater les entrées pour le LLM
        entries_text = self._format_entries_for_llm(entries)
        tags_text = self._format_tags_for_llm(tags)
        
        # Prompt pour le LLM
        system_prompt = """Tu es un assistant budgétaire expert.
Pour chaque entrée budgétaire, choisis la cellule Excel la plus pertinente parmi la liste de tags.
Réponds exclusivement avec un tableau JSON au format suivant :
[
  {
    "Axe": "...",
    "Description": "...",
    "cellule": "B10",
    "tags_utilisés": ["Label1", "Label2"],
    "tag_id": 4
  },
  ...
]
Assure-toi que les tag_id et tags_utilisés correspondent exactement à ceux présents dans les tags disponibles."""
        
        user_prompt = f"""Éléments budgétaires :
{entries_text}

Tags disponibles :
{tags_text}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Appel au LLM
        response = await self.llm_client.chat(messages)
        
        if not response:
            logger.error("Pas de réponse du LLM pour le mapping")
            return []
        
        # Parser la réponse
        try:
            import json
            # Extraire le JSON de la réponse
            json_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if json_match:
                mapping = json.loads(json_match.group())
                return mapping
            else:
                logger.error("Aucun JSON trouvé dans la réponse")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"Erreur parsing JSON: {str(e)}")
            return []
    
    def _format_entries_for_llm(self, entries: List[Dict]) -> str:
        """Formate les entrées budgétaires pour le LLM"""
        lines = []
        for entry in entries:
            line = f"- Axe: '{entry.get('Axe', '')}', " \
                   f"Description: '{entry.get('Description', '')}', " \
                   f"Montant: {entry.get('Montant', 0)}"
            lines.append(line)
        return "\n".join(lines)
    
    def _format_tags_for_llm(self, tags: List[Dict]) -> str:
        """Formate les tags pour le LLM"""
        lines = []
        for i, tag in enumerate(tags):
            labels = ", ".join(tag.get('labels', []))
            line = f"{i}) Cellule {tag.get('cell_address', '')} – " \
                   f"labels : {labels} – ID: {tag.get('id', i)}"
            lines.append(line)
        return "\n".join(lines)
    
    def apply_mapping_to_excel(self, workbook, mapping: List[Dict], 
                              entries_data: pd.DataFrame) -> Tuple[int, List[str]]:
        """Applique le mapping au workbook Excel"""
        success_count = 0
        errors = []
        
        for i, mapping_entry in enumerate(mapping):
            try:
                # Trouver l'entrée correspondante
                entry_idx = None
                for idx, entry in entries_data.iterrows():
                    if (entry.get('Axe') == mapping_entry.get('Axe') and 
                        entry.get('Description') == mapping_entry.get('Description')):
                        entry_idx = idx
                        break
                
                if entry_idx is None:
                    errors.append(f"Entrée non trouvée: {mapping_entry.get('Axe')}")
                    continue
                
                # Récupérer les informations
                sheet_name = mapping_entry.get('sheet_name', 'Sheet1')
                cell_address = mapping_entry.get('cellule')
                montant = entries_data.loc[entry_idx, 'Montant']
                
                # Parser l'adresse de cellule
                row, col = self._parse_cell_address(cell_address)
                
                # Écrire dans le workbook
                if sheet_name in workbook.sheetnames:
                    sheet = workbook[sheet_name]
                    sheet.cell(row=row, column=col, value=montant)
                    success_count += 1
                    logger.info(f"Écrit {montant} dans {sheet_name}!{cell_address}")
                else:
                    errors.append(f"Feuille non trouvée: {sheet_name}")
                    
            except Exception as e:
                errors.append(f"Erreur mapping ligne {i}: {str(e)}")
                logger.error(f"Erreur mapping: {str(e)}")
        
        return success_count, errors
    
    def _parse_cell_address(self, address: str) -> Tuple[int, int]:
        """Parse une adresse de cellule Excel (ex: 'B10') en (row, col)"""
        match = re.match(r'([A-Z]+)(\d+)', address.upper())
        if not match:
            raise ValueError(f"Adresse invalide: {address}")
        
        col_str, row_str = match.groups()
        
        # Convertir la colonne
        col = 0
        for char in col_str:
            col = col * 26 + (ord(char) - ord('A') + 1)
        
        return int(row_str), col
    
    def enrich_entries_with_mapping(self, entries: pd.DataFrame, 
                                   mapping: List[Dict]) -> pd.DataFrame:
        """Enrichit les entrées avec les informations de mapping"""
        # Créer un dictionnaire pour lookup rapide
        mapping_dict = {}
        for m in mapping:
            key = (m.get('Axe'), m.get('Description'))
            mapping_dict[key] = {
                'CelluleCible': m.get('cellule'),
                'TagID': m.get('tag_id'),
                'TagsUtilises': ', '.join(m.get('tags_utilisés', []))
            }
        
        # Ajouter les colonnes si elles n'existent pas
        if 'CelluleCible' not in entries.columns:
            entries['CelluleCible'] = ''
        if 'TagID' not in entries.columns:
            entries['TagID'] = ''
        if 'TagsUtilises' not in entries.columns:
            entries['TagsUtilises'] = ''
        
        # Enrichir les données
        for idx, row in entries.iterrows():
            key = (row.get('Axe'), row.get('Description'))
            if key in mapping_dict:
                entries.loc[idx, 'CelluleCible'] = mapping_dict[key]['CelluleCible']
                entries.loc[idx, 'TagID'] = mapping_dict[key]['TagID']
                entries.loc[idx, 'TagsUtilises'] = mapping_dict[key]['TagsUtilises']
        
        return entries