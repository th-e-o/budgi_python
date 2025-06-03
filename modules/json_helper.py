# modules/json_helper.py
import json
import pandas as pd
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class JSONHelper:
    """Helper pour traiter les fichiers JSON de configuration"""
    
    def __init__(self):
        self.current_json = None
    
    def load_json(self, file_path: str) -> Dict[str, Any]:
        """Charge un fichier JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.current_json = json.load(f)
            logger.info(f"JSON chargé: {file_path}")
            return self.current_json
        except Exception as e:
            logger.error(f"Erreur chargement JSON: {str(e)}")
            raise
    
    def extract_labels(self, json_data: Dict[str, Any]) -> List[str]:
        """Extrait tous les labels uniques du JSON"""
        labels = []
        
        if 'tags' in json_data:
            tags = json_data['tags']
            
            if isinstance(tags, list):
                for tag in tags:
                    if isinstance(tag, dict) and 'labels' in tag:
                        tag_labels = tag['labels']
                        if isinstance(tag_labels, list):
                            labels.extend(tag_labels)
                        else:
                            labels.append(str(tag_labels))
            
            elif isinstance(tags, dict):
                for key, tag in tags.items():
                    if isinstance(tag, dict) and 'labels' in tag:
                        tag_labels = tag['labels']
                        if isinstance(tag_labels, list):
                            labels.extend(tag_labels)
                        else:
                            labels.append(str(tag_labels))
        
        # Retourner les labels uniques
        unique_labels = list(set(labels))
        logger.info(f"Extraction: {len(unique_labels)} labels uniques")
        return unique_labels
    
    def get_tags_for_mapping(self, json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prépare les tags pour le mapping budgétaire"""
        tags_list = []
        
        if 'tags' not in json_data:
            return tags_list
        
        tags = json_data['tags']
        
        if isinstance(tags, list):
            for i, tag in enumerate(tags):
                if isinstance(tag, dict):
                    tag_info = {
                        'id': tag.get('id', i),
                        'cell_address': tag.get('cell_address', ''),
                        'labels': tag.get('labels', []),
                        'sheet_name': tag.get('sheet_name', 'Sheet1')
                    }
                    tags_list.append(tag_info)
        
        return tags_list
    
    def update_tags_from_excel(self, json_data: Dict[str, Any], 
                              excel_data: pd.DataFrame,
                              source_cells: List[str]) -> Dict[str, Any]:
        """Met à jour les tags avec les données Excel"""
        if 'tags' not in json_data:
            return json_data
        
        updated_count = 0
        
        for tag in json_data['tags']:
            if 'source_cells' in tag:
                new_labels = []
                
                for cell_address in tag['source_cells']:
                    # Parser l'adresse (ex: "B10")
                    import re
                    match = re.match(r'([A-Z]+)(\d+)', cell_address)
                    if match:
                        col_letter = match.group(1)
                        row_num = int(match.group(2))
                        
                        # Convertir en index
                        col_idx = self._col_letter_to_index(col_letter)
                        
                        # Récupérer la valeur
                        if row_num <= len(excel_data) and col_idx < len(excel_data.columns):
                            value = excel_data.iloc[row_num - 1, col_idx]
                            if pd.notna(value) and str(value).strip():
                                new_labels.append(str(value))
                
                # Ajouter les nouveaux labels sans écraser
                existing_labels = tag.get('labels', [])
                if not isinstance(existing_labels, list):
                    existing_labels = [existing_labels]
                
                combined_labels = list(set(existing_labels + new_labels))
                if len(combined_labels) > len(existing_labels):
                    tag['labels'] = combined_labels
                    updated_count += 1
        
        logger.info(f"Tags mis à jour: {updated_count}")
        return json_data
    
    def _col_letter_to_index(self, col_letter: str) -> int:
        """Convertit une lettre de colonne en index (A->0, B->1, etc.)"""
        result = 0
        for char in col_letter:
            result = result * 26 + ord(char) - ord('A')
        return result