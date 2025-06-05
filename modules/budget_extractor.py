# modules/budget_extractor.py
import re
import pandas as pd
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class BudgetExtractor:
    """Extrait les données budgétaires depuis du texte"""
    
    def __init__(self):
        self.currency_patterns = {
            'M€': 1_000_000,
            'Md€': 1_000_000_000,
            'k€': 1_000,
            '€': 1
        }
    
    async def extract(self, content: str, llm_client, excel_sheets: List[str] = None) -> List[Dict]:
        """Extrait les données budgétaires avec assignation de sheet"""
        try:
            # Prompt modifié pour inclure les sheets disponibles
            if excel_sheets:
                sheets_info = f"\nSheets disponibles dans l'Excel : {', '.join(excel_sheets)}"
                prompt = (
                    "Tu es un assistant budgétaire. "
                    "Analyse le texte et retourne un tableau JSON avec les données budgétaires. "
                    f"{sheets_info}\n"
                    "Pour chaque entrée, ajoute un champ 'Sheet' avec le nom de la feuille la plus appropriée. "
                    "Format: [{\"Axe\":..., \"Description\":..., \"Montant\":..., \"Sheet\":..., ...}]"
                )
            else:
                # Prompt classique sans sheets
                prompt = "..."
                
            # Extraction avec le LLM
            budget_data = await llm_client.extract_budget_data_with_prompt(content, prompt)
            
            # Si pas de sheets dans la réponse mais qu'on a des sheets Excel
            if excel_sheets and budget_data:
                for entry in budget_data:
                    if 'Sheet' not in entry:
                        # Assigner une sheet par défaut basée sur des mots-clés
                        entry['Sheet'] = self._guess_sheet(entry, excel_sheets)
                        
            return budget_data
            
        except Exception as e:
            logger.error(f"Erreur extraction: {str(e)}")
            return []

    def _normalize_amount(self, amount_str: str) -> float:
        """Normalise un montant en nombre"""
        # Nettoyer la chaîne
        amount_str = amount_str.replace(' ', '').replace(',', '.')
        
        # Extraire le nombre et l'unité
        for unit, multiplier in self.currency_patterns.items():
            if unit in amount_str:
                number_str = amount_str.replace(unit, '').strip()
                try:
                    return float(number_str) * multiplier
                except ValueError:
                    pass
        
        # Essayer de parser directement
        try:
            return float(amount_str)
        except ValueError:
            return 0.0
    
    def _attach_source_phrases(self, budget_data: List[Dict], full_text: str) -> List[Dict]:
        """Attache les phrases sources aux données extraites"""
        #TODO Modifier le code pour que la source phrase des mails soit seulement issue du corps du mail
        sentences = self._split_into_sentences(full_text)
        
        for entry in budget_data:
            montant = entry.get('Montant', '')
            description = entry.get('Description', '')
            
            best_match = None
            best_score = 0
            
            for sentence in sentences:
                score = 0
                sentence_lower = sentence.lower()
                
                # Vérifier la présence du montant
                if str(montant) in sentence:
                    score += 2
                
                # Vérifier la présence de mots de la description
                desc_words = description.lower().split()
                matching_words = sum(1 for word in desc_words 
                                   if len(word) > 3 and word in sentence_lower)
                score += matching_words
                
                if score > best_score:
                    best_score = score
                    best_match = sentence
            
            entry['SourcePhrase'] = best_match
        
        return budget_data
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Découpe un texte en phrases"""
        # Remplacer les sauts de ligne par des espaces
        text = text.replace('\n', ' ')
        
        # Découper sur la ponctuation
        sentences = re.split(r'[.!?]+', text)
        
        # Nettoyer et filtrer
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences