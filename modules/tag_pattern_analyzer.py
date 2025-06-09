# modules/tag_pattern_analyzer.py
import re
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class TagPattern:
    """Pattern de tag sans l'année"""
    template: str
    sheet_name: str
    description: str
    years: Set[int]
    tag_ids_by_year: Dict[int, List[str]]
    example_labels: List[str]

class TagPatternAnalyzer:
    """Analyse et regroupe les tags par pattern"""
    
    def __init__(self):
        self.patterns = {}
        self.year_pattern = re.compile(r'\b(202[0-9]|203[0-5])\b')
        
    def analyze_tags(self, tags: List[Dict]) -> Dict[str, TagPattern]:
        """Analyse les tags et extrait les patterns uniques"""
        pattern_groups = defaultdict(lambda: {
            'years': set(),
            'tag_ids_by_year': defaultdict(list),
            'tags': []
        })
        
        for tag in tags:
            # Extraire le pattern
            pattern_key, year = self._extract_pattern(tag)
            
            if pattern_key:
                group = pattern_groups[pattern_key]
                if year:
                    group['years'].add(year)
                    group['tag_ids_by_year'][year].append(tag['id'])
                else:
                    group['tag_ids_by_year'][0].append(tag['id'])  # 0 pour sans année
                group['tags'].append(tag)
        
        # Créer les TagPattern
        patterns = {}
        pattern_id = 0
        
        for pattern_key, group_data in pattern_groups.items():
            sheet_name, description = pattern_key
            
            # Prendre un exemple de labels
            example_tag = group_data['tags'][0]
            example_labels = example_tag.get('labels', [])
            
            pattern = TagPattern(
                template=f"{sheet_name} | {description}",
                sheet_name=sheet_name,
                description=description,
                years=group_data['years'],
                tag_ids_by_year=dict(group_data['tag_ids_by_year']),
                example_labels=example_labels
            )
            
            patterns[f"pattern_{pattern_id}"] = pattern
            pattern_id += 1
        
        logger.info(f"Réduit {len(tags)} tags à {len(patterns)} patterns uniques")
        return patterns
    
    def _extract_pattern(self, tag: Dict) -> Tuple[Optional[Tuple[str, str]], Optional[int]]:
        """Extrait le pattern et l'année d'un tag"""
        labels = tag.get('labels', [])
        if not labels:
            return None, None
        
        sheet_name = tag.get('sheet_name', '')
        
        # Reconstruire la description sans l'année
        description_parts = []
        year_found = None
        
        for label in labels:
            label_str = str(label)
            
            # Vérifier si c'est une année
            year_match = self.year_pattern.search(label_str)
            if year_match and label_str.strip() == year_match.group(0):
                # C'est juste une année
                year_found = int(year_match.group(0))
                continue
            
            # Si ce n'est pas le sheet_name, l'ajouter à la description
            if label_str != sheet_name:
                # Remplacer l'année dans le label si elle existe
                cleaned_label = self.year_pattern.sub('[YEAR]', label_str)
                description_parts.append(cleaned_label)
        
        if description_parts:
            description = " | ".join(description_parts)
            pattern_key = (sheet_name, description)
            return pattern_key, year_found
        
        return None, None
    
    def find_matching_pattern(self, entry: Dict, patterns: Dict[str, TagPattern]) -> List[Tuple[TagPattern, float]]:
        """Trouve les patterns correspondants pour une entrée"""
        entry_text = f"{entry.get('Axe', '')} {entry.get('Description', '')}".lower()
        entry_sheet = entry.get('Sheet', '')
        
        # Extraire l'année de l'entrée
        entry_year = None
        year_match = self.year_pattern.search(entry_text)
        if year_match:
            entry_year = int(year_match.group(0))
        
        matches = []
        
        for pattern_id, pattern in patterns.items():
            # Filtre par sheet si spécifié
            if entry_sheet and pattern.sheet_name != entry_sheet:
                continue
            
            # Calculer le score de correspondance
            score = self._calculate_pattern_score(entry_text, entry_year, pattern)
            
            if score > 0:
                matches.append((pattern, score))
        
        # Trier par score décroissant
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches
    
    def _calculate_pattern_score(self, entry_text: str, entry_year: Optional[int], 
                                pattern: TagPattern) -> float:
        """Calcule le score de correspondance avec un pattern"""
        score = 0.0
        
        # Nettoyer les textes
        pattern_desc = pattern.description.lower().replace('[year]', '')
        
        # Correspondance de mots-clés
        entry_words = set(entry_text.split())
        pattern_words = set(pattern_desc.split())
        
        # Enlever les mots courts et communs
        entry_words = {w for w in entry_words if len(w) > 3}
        pattern_words = {w for w in pattern_words if len(w) > 3}
        
        # CORRECTION: Vérifier qu'on ne divise pas par zéro
        if entry_words and pattern_words:
            common_words = entry_words & pattern_words
            if common_words:
                min_len = min(len(entry_words), len(pattern_words))
                if min_len > 0:  # Protection contre division par zéro
                    score = len(common_words) / min_len
        
        # Bonus si l'année correspond
        if entry_year and entry_year in pattern.years:
            score += 0.3
        
        return score