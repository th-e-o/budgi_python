# modules/json_helper.py
import json
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
import logging
import openpyxl
import re

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
    
    def load_json_from_content(self, content: str) -> Dict[str, Any]:
        """Charge un JSON depuis du contenu texte"""
        try:
            self.current_json = json.loads(content)
            logger.info("JSON chargé depuis contenu")
            return self.current_json
        except Exception as e:
            logger.error(f"Erreur parsing JSON: {str(e)}")
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
                            workbook: openpyxl.Workbook) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Met à jour les tags avec les données des cellules sources dans Excel
        et supprime les tags dupliqués (qui ont exactement les mêmes labels)
        Retourne le JSON mis à jour et la liste des modifications
        """
        if 'tags' not in json_data:
            return json_data, []
        
        modifications = []
        
        # Première passe : enrichir les tags
        for tag in json_data['tags']:
            if 'source_cells' in tag and tag['source_cells']:
                # Labels existants
                existing_labels = tag.get('labels', [])
                if not isinstance(existing_labels, list):
                    existing_labels = [existing_labels]
                
                # Nouveaux labels depuis les cellules sources
                new_labels = []
                sheet_name = tag.get('sheet_name', 'Sheet1')
                
                # Vérifier que la feuille existe
                if sheet_name not in workbook.sheetnames:
                    logger.warning(f"Feuille '{sheet_name}' non trouvée dans le workbook")
                    continue
                
                sheet = workbook[sheet_name]
                
                for cell_address in tag['source_cells']:
                    try:
                        # Récupérer la valeur de la cellule
                        cell_value = sheet[cell_address].value
                        
                        if cell_value is not None and str(cell_value).strip():
                            label = str(cell_value).strip()
                            if label not in existing_labels and label not in new_labels:
                                new_labels.append(label)
                    except Exception as e:
                        logger.warning(f"Erreur lecture cellule {sheet_name}!{cell_address}: {str(e)}")
                
                # Combiner les labels sans écraser
                if new_labels:
                    combined_labels = existing_labels + new_labels
                    tag['labels'] = combined_labels
                    
                    # Enregistrer la modification
                    modifications.append({
                        'cell': tag.get('cell_address', f"Tag {tag.get('id', '?')}"),
                        'sheet': sheet_name,
                        'added_labels': new_labels,
                        'existing_labels': existing_labels
                    })
        
        # Deuxième passe : identifier et supprimer les tags dupliqués
        tags_by_labels = {}
        unique_tags = []
        removed_count = 0
        
        for tag in json_data['tags']:
            # Créer une clé unique basée sur les labels triés
            labels = tag.get('labels', [])
            if isinstance(labels, list):
                # Trier les labels pour que l'ordre n'importe pas
                labels_key = tuple(sorted(str(l) for l in labels))
            else:
                labels_key = (str(labels),)
            
            # Vérifier si on a déjà vu ces labels
            if labels_key in tags_by_labels:
                # Tag dupliqué trouvé
                removed_count += 1
                logger.info(f"Tag dupliqué supprimé: {tag.get('sheet_name')}!{tag.get('cell_address')} - Labels: {labels_key}")
            else:
                # Nouveau tag unique
                tags_by_labels[labels_key] = tag
                unique_tags.append(tag)
        
        # Remplacer les tags par la liste nettoyée
        json_data['tags'] = unique_tags
        
        # Ajouter l'information sur le nettoyage aux modifications
        if removed_count > 0:
            modifications.append({
                'action': 'cleanup',
                'removed_duplicates': removed_count,
                'remaining_tags': len(unique_tags)
            })
        
        logger.info(f"Tags mis à jour: {len(modifications)} cellules modifiées, {removed_count} doublons supprimés")
        return json_data, modifications

    def deduplicate_tags(self, json_data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
        """
        Méthode utilitaire pour dédupliquer les tags sans mise à jour depuis Excel
        Retourne le JSON nettoyé et le nombre de doublons supprimés
        """
        if 'tags' not in json_data:
            return json_data, 0
        
        tags_by_labels = {}
        unique_tags = []
        removed_count = 0
        
        for tag in json_data['tags']:
            # Créer une clé unique basée sur les labels triés
            labels = tag.get('labels', [])
            if isinstance(labels, list):
                labels_key = tuple(sorted(str(l) for l in labels))
            else:
                labels_key = (str(labels),)
            
            if labels_key in tags_by_labels:
                removed_count += 1
                logger.info(f"Tag dupliqué supprimé: {tag.get('sheet_name')}!{tag.get('cell_address')}")
            else:
                tags_by_labels[labels_key] = tag
                unique_tags.append(tag)
        
        json_data['tags'] = unique_tags
        
        return json_data, removed_count
    
    def get_duplicate_tags_info(self, json_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Retourne des informations sur les tags dupliqués sans les supprimer
        Utile pour l'analyse avant le nettoyage
        """
        if 'tags' not in json_data:
            return []
        
        tags_by_labels = {}
        duplicates_info = []
        
        for tag in json_data['tags']:
            labels = tag.get('labels', [])
            if isinstance(labels, list):
                labels_key = tuple(sorted(str(l) for l in labels))
            else:
                labels_key = (str(labels),)
            
            if labels_key in tags_by_labels:
                # On a trouvé un doublon
                original = tags_by_labels[labels_key]
                duplicates_info.append({
                    'labels': list(labels_key),
                    'original_cell': f"{original.get('sheet_name')}!{original.get('cell_address')}",
                    'duplicate_cell': f"{tag.get('sheet_name')}!{tag.get('cell_address')}",
                    'tag_ids': [original.get('id'), tag.get('id')]
                })
            else:
                tags_by_labels[labels_key] = tag
        
        return duplicates_info

    def update_tags_from_dataframe(self, json_data: Dict[str, Any], 
                                  df: pd.DataFrame,
                                  sheet_name: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Version alternative qui utilise un DataFrame au lieu d'un workbook
        """
        if 'tags' not in json_data:
            return json_data, []
        
        modifications = []
        
        for tag in json_data['tags']:
            # Vérifier que c'est la bonne feuille
            if tag.get('sheet_name') != sheet_name:
                continue
                
            if 'source_cells' in tag and tag['source_cells']:
                existing_labels = tag.get('labels', [])
                if not isinstance(existing_labels, list):
                    existing_labels = [existing_labels]
                
                new_labels = []
                
                for cell_address in tag['source_cells']:
                    # Parser l'adresse
                    match = re.match(r'([A-Z]+)(\d+)', cell_address)
                    if match:
                        col_letter = match.group(1)
                        row_num = int(match.group(2))
                        
                        # Convertir en index
                        col_idx = self._col_letter_to_index(col_letter)
                        
                        # Récupérer la valeur
                        if row_num <= len(df) and col_idx < len(df.columns):
                            try:
                                value = df.iloc[row_num - 1, col_idx]
                                if pd.notna(value) and str(value).strip():
                                    label = str(value).strip()
                                    if label not in existing_labels and label not in new_labels:
                                        new_labels.append(label)
                            except:
                                pass
                
                if new_labels:
                    combined_labels = existing_labels + new_labels
                    tag['labels'] = combined_labels
                    
                    modifications.append({
                        'cell': tag.get('cell_address', f"Tag {tag.get('id', '?')}"),
                        'sheet': sheet_name,
                        'added_labels': new_labels,
                        'existing_labels': existing_labels
                    })
        
        return json_data, modifications
    
    def _col_letter_to_index(self, col_letter: str) -> int:
        """Convertit une lettre de colonne en index (A->0, B->1, etc.)"""
        result = 0
        for char in col_letter:
            result = result * 26 + ord(char) - ord('A')
        return result
    
    def get_source_cells_summary(self, json_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Retourne un résumé des cellules sources par feuille
        """
        summary = {}
        
        if 'tags' not in json_data:
            return summary
        
        for tag in json_data['tags']:
            sheet_name = tag.get('sheet_name', 'Sheet1')
            source_cells = tag.get('source_cells', [])
            
            if sheet_name not in summary:
                summary[sheet_name] = []
            
            summary[sheet_name].extend(source_cells)
        
        # Dédupliquer
        for sheet in summary:
            summary[sheet] = list(set(summary[sheet]))
            summary[sheet].sort()
        
        return summary
    
    def export_json(self, json_data: Dict[str, Any]) -> str:
        """Exporte le JSON en string formaté"""
        return json.dumps(json_data, indent=2, ensure_ascii=False)
    
    def save_json(self, json_data: Dict[str, Any], file_path: str):
        """Sauvegarde le JSON dans un fichier"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            logger.info(f"JSON sauvegardé: {file_path}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde JSON: {str(e)}")
            raise