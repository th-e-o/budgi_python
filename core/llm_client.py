import httpx
import json
from typing import List, Dict, Optional
import logging
from config import config

logger = logging.getLogger(__name__)

class MistralClient:
    def __init__(self):
        self.api_key = config.MISTRAL_API_KEY
        self.api_url = config.MISTRAL_API_URL
        self.model = config.MISTRAL_MODEL
        self.preprompt = {
            "role": "system",
            "content": (
                "Vous êtes BudgiBot, un assistant intelligent dédié à la Direction du Budget française. "
                "Vos réponses doivent être concises, professionnelles et adaptées à un public expert. "
                "Si l'utilisateur envoie un fichier, proposez une synthèse en deux lignes et demandez ce qu'il attend. "
                "Suggérez l'outil BPSS si l'utilisateur parle de remplir un fichier ou produire un fichier final."
            )
        }
    
    async def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> Optional[str]:
        """Envoie une requête chat à l'API Mistral"""
        if not self.api_key:
            logger.error("Clé API Mistral manquante")
            return None
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Ajouter le preprompt
        full_messages = [self.preprompt] + messages
        
        payload = {
            "model": model or self.model,
            "messages": full_messages
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    logger.error(f"Erreur API Mistral: {response.status_code} - {response.text}")
                    return None
                
                data = response.json()
                return data["choices"][0]["message"]["content"]
                
        except Exception as e:
            logger.error(f"Erreur lors de l'appel API Mistral: {str(e)}")
            return None
    
    async def analyze_labels(self, labels: List[str]) -> Optional[Dict]:
        """Analyse les labels pour identifier axes et contexte"""
        if not labels:
            return None
        
        labels_txt = ", ".join(labels)
        prompt = (
            f"Tu es un assistant budgétaire. "
            f"Analyse la liste de labels suivants et identifie les axes pertinents et leur contexte pour une extraction budgétaire. "
            f"Labels : {labels_txt} "
            f"Retourne STRICTEMENT un JSON avec deux champs : "
            f'{{\"axes\": [...], \"contexte_general\": \"...\"}} '
            f"NE FOURNIS PAS D'EXPLICATION HORS JSON."
        )
        
        messages = [{"role": "system", "content": prompt}]
        response = await self.chat(messages)
        
        if response:
            try:
                # Nettoyer la réponse
                cleaned = response.replace("```json", "").replace("```", "").strip()
                return json.loads(cleaned)
            except json.JSONDecodeError:
                logger.error("Impossible de parser la réponse JSON")
                return None
        return None
    
    async def extract_budget_data(self, content: str) -> Optional[List[Dict]]:
        """Extrait les données budgétaires d'un texte"""
        prompt = (
            "Tu es un assistant budgétaire. "
            "Analyse le texte fourni et retourne UNIQUEMENT un tableau JSON avec les données budgétaires détectées au format : "
            '[ {"Axe":..., "Description":..., "Montant":..., "Unité":..., "Probabilite":..., "Date":..., "Nature":...} ]'
        )
        
        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": content}
        ]
        
        response = await self.chat(messages)
        
        if response:
            try:
                # Extraire le tableau JSON
                import re
                match = re.search(r'\[.*?\]', response, re.DOTALL)
                if match:
                    return json.loads(match.group())
            except json.JSONDecodeError:
                logger.error("Impossible de parser les données budgétaires")
                return None
        return None