import re
import pandas as pd
from typing import List, Dict, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BudgetEntry:
    axe: str
    description: str
    montant: float
    unite: str = "€"
    probabilite: float = 0.0
    date: Optional[str] = None
    nature: Optional[str] = None
    source_phrase: Optional[str] = None
    cellule_cible: Optional[str] = None

class BudgetExtractor:
    """Extrait et traite les données budgétaires"""
    
    def __init__(self):
        self.patterns = {
            'montant': r'(\d{1,3}(?:\s?\d{3})*(?:,\d+)?)\s*(M€|millions?\s*d[\'']?euros?|Md€|milliards?\s*d[\'']?euros?)',
            'reference': r'[A-Z]+\d+(?::[A-Z]+\d+)?',
            'pourcentage': r'\d+(?:,\d+)?\s*%'
        }
    
    async def extract(self, content: str, llm_client) -> List[Dict]:
        """Extrait les données budgétaires d'un contenu"""
        # Appel LLM pour extraction structurée
        budget_data = await llm_client.extract_budget_data(content)
        
        if not budget_data:
            return []
        
        # Enrichir avec les phrases sources
        enriched_data = self._attach_source_phrases(budget_data, content)
        
        return enriched_data
    
    def _attach_source_phrases(self, budget_data: List[Dict], full_text: str) -> List[Dict]:
        """Attache les phrases sources aux données extraites"""
        # Découper le texte en phrases
        sentences = self._split_into_sentences(full_text)
        
        for entry in budget_data:
            # Chercher la phrase contenant le montant
            montant_str = str(entry.get('Montant', ''))
            best_match = None
            
            for sentence in sentences:
                if self._contains_amount(sentence, montant_str):
                    # Vérifier aussi si la description est mentionnée
                    desc_words = entry.get('Description', '').lower().split()
                    if any(word in sentence.lower() for word in desc_words if len(word) > 3):
                        best_match = sentence
                        break
                    elif not best_match:
                        best_match = sentence
            
            entry['SourcePhrase'] = best_match
        
        return budget_data
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Découpe un texte en phrases"""
        # Ajouter un point après les lignes sans ponctuation finale
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line[-1] in '.!?':
                line += '.'
            processed_lines.append(line)
        
        text = ' '.join(processed_lines)
        
        # Découper en phrases
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _contains_amount(self, sentence: str, amount: str) -> bool:
        """Vérifie si une phrase contient un montant"""
        # Normaliser le montant (enlever espaces, convertir virgules)
        normalized_amount = amount.replace(' ', '').replace(',', '.')
        
        # Chercher le montant avec différents formats
        patterns = [
            amount,  # Format original
            amount.replace(' ', ''),  # Sans espaces
            amount.replace(' ', ' '),  # Avec espaces normaux
            normalized_amount  # Normalisé
        ]
        
        sentence_lower = sentence.lower()
        return any(p.lower() in sentence_lower for p in patterns)
    
    def map_to_cells(self, entries: pd.DataFrame, tags: List[Dict], llm_client) -> pd.DataFrame:
        """Mappe les entrées budgétaires aux cellules Excel"""
        # Implémenter la logique de mapping
        # Cette partie nécessiterait l'intégration avec le LLM pour le mapping intelligent
        pass