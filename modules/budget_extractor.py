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
    
    async def extract(self, content: str, llm_client) -> List[Dict]:
        """Extrait les données budgétaires du contenu"""
        try:
            # Utiliser le LLM pour extraction structurée
            budget_data = await llm_client.extract_budget_data(content)
            
            if not budget_data:
                logger.warning("Aucune donnée budgétaire extraite par le LLM")
                return []
            
            # Enrichir avec les phrases sources
            enriched_data = self._attach_source_phrases(budget_data, content)
            
            # Normaliser les montants
            for entry in enriched_data:
                if 'Montant' in entry:
                    entry['Montant'] = self._normalize_amount(str(entry['Montant']))
            
            return enriched_data
            
        except Exception as e:
            logger.error(f"Erreur extraction budget: {str(e)}")
            return []
    
    def _extract_year_from_entry(self, entry: Dict) -> Optional[int]:
        """Extrait l'année d'une entrée budgétaire"""
        import re
        year_pattern = re.compile(r'\b(20[2-3][0-9])\b')
        
        # Chercher dans tous les champs
        search_fields = ['Date']
        
        for field in search_fields:
            if field in entry and entry[field]:
                text = str(entry[field])
                match = year_pattern.search(text)
                if match:
                    return int(match.group(1))
        
        return None

    
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

    def _extract_mail_body(self, full_text: str) -> str:
        """Extrait le corps d'un mail depuis le texte complet"""
        # Rechercher le marqueur du début du corps
        body_marker = "--- Contenu du message ---"
        
        if body_marker in full_text:
            # Extraire tout après le marqueur
            body_start = full_text.find(body_marker) + len(body_marker)
            body_content = full_text[body_start:].strip()
            
            # Rechercher et enlever la section des pièces jointes si présente
            attachments_marker = "\n\nPièces jointes ("
            if attachments_marker in body_content:
                attachments_start = body_content.find(attachments_marker)
                body_content = body_content[:attachments_start].strip()
            
            return body_content
        
        # Si pas de marqueur, retourner le texte complet
        return full_text

    def _is_mail_content(self, text: str) -> bool:
        """Détermine si le texte provient d'un mail"""
        return text.strip().startswith("Type de message : Mail")
    
    def _attach_source_phrases(self, budget_data: List[Dict], full_text: str) -> List[Dict]:
        """Attache les phrases sources aux données extraites"""
        # Déterminer le texte à utiliser pour la recherche
        search_text = full_text
        
        # Si c'est un mail, utiliser seulement le corps
        if self._is_mail_content(full_text):
            search_text = self._extract_mail_body(full_text)
            logger.info("Mail détecté - recherche des phrases sources dans le corps uniquement")
        
        # Découper en phrases
        sentences = self._split_into_sentences(search_text)
        
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
        """Découpe un texte en phrases en utilisant la ponctuation ET les retours à la ligne"""
        # D'abord découper sur les retours à la ligne
        lines = text.split('\n')
        
        sentences = []
        
        # Pour chaque ligne, découper sur la ponctuation
        for line in lines:
            if line.strip():
                # Découper la ligne sur la ponctuation
                line_sentences = re.split(r'[.!?]+', line)
                
                # Ajouter les phrases non vides
                for sentence in line_sentences:
                    if sentence.strip():
                        sentences.append(sentence.strip())
        
        return sentences