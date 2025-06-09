# modules/embeddings_manager.py (version optimisée)
import numpy as np
from typing import List, Dict, Optional
import httpx
import asyncio
import faiss
import logging
from .tag_pattern_analyzer import TagPatternAnalyzer, TagPattern
from config import config

logger = logging.getLogger(__name__)

class OptimizedMistralEmbeddingsManager:
    """Gestionnaire d'embeddings optimisé pour les patterns"""
    
    def __init__(self):
        self.api_key = config.MISTRAL_API_KEY
        self.api_url = config.MISTRAL_EMBEDDINGS_URL
        self.model = config.MISTRAL_EMBED_MODEL
        self.pattern_analyzer = TagPatternAnalyzer()
        
        # Structures de données
        self.patterns = {}
        self.pattern_embeddings = {}
        self.pattern_index = None
        self.pattern_mappings = {}
        
        # Configuration
        self.batch_size = 10
        self.rate_limit_delay = 1.0
        
    async def build_optimized_index(self, tags: List[Dict], progress_callback=None) -> None:
        """Construit un index optimisé basé sur les patterns"""
        if progress_callback:
            progress_callback(0, "Analyse des patterns...")
        
        # Analyser et regrouper les tags
        self.patterns = self.pattern_analyzer.analyze_tags(tags)
        
        logger.info(f"Patterns uniques trouvés: {len(self.patterns)}")
        
        if progress_callback:
            progress_callback(20, f"{len(self.patterns)} patterns uniques identifiés")
        
        # Créer les textes pour embeddings (seulement les patterns uniques)
        pattern_texts = []
        pattern_ids = []
        
        for pattern_id, pattern in self.patterns.items():
            # Créer un texte représentatif du pattern
            text = f"{pattern.sheet_name} {pattern.description}"
            pattern_texts.append(text)
            pattern_ids.append(pattern_id)
        
        # Obtenir les embeddings pour les patterns uniques seulement
        if progress_callback:
            progress_callback(30, f"Génération des embeddings pour {len(pattern_texts)} patterns...")
        
        embeddings = await self._get_pattern_embeddings(pattern_texts, progress_callback)
        
        if embeddings is None or len(embeddings) == 0:
            logger.error("Aucun embedding généré")
            return
        
        # Normaliser
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        # Créer l'index FAISS
        if progress_callback:
            progress_callback(90, "Construction de l'index...")
        
        dimension = embeddings.shape[1]
        self.pattern_index = faiss.IndexFlatIP(dimension)
        self.pattern_index.add(embeddings.astype('float32'))
        
        # Stocker les mappings
        for i, pattern_id in enumerate(pattern_ids):
            self.pattern_mappings[i] = pattern_id
            self.pattern_embeddings[pattern_id] = embeddings[i]
        
        if progress_callback:
            progress_callback(100, "Index optimisé construit")
        
        logger.info(f"Index construit avec {len(pattern_ids)} patterns")
    
    async def _get_pattern_embeddings(self, texts: List[str], progress_callback=None) -> np.ndarray:
        """Obtient les embeddings pour les patterns avec gestion du rate limiting"""
        all_embeddings = []
        
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            
            if progress_callback:
                progress = 30 + (i / len(texts)) * 50  # 30-80%
                progress_callback(progress, f"Embeddings: {i}/{len(texts)} patterns...")
            
            try:
                embeddings = await self._get_embeddings_with_retry(batch)
                all_embeddings.extend(embeddings)
                
                # Pause entre les batches
                if i + self.batch_size < len(texts):
                    await asyncio.sleep(self.rate_limit_delay)
                    
            except Exception as e:
                logger.error(f"Erreur batch {i//self.batch_size}: {str(e)}")
                # Continuer avec des embeddings aléatoires pour ce batch
                all_embeddings.extend([np.random.randn(1024) for _ in batch])
        
        return np.array(all_embeddings)
    
    async def _get_embeddings_with_retry(self, texts: List[str], max_retries: int = 3) -> np.ndarray:
        """Obtient les embeddings avec retry"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        for attempt in range(max_retries):
            try:
                payload = {
                    "model": self.model,
                    "input": texts
                }
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        self.api_url,
                        headers=headers,
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        embeddings = [item['embedding'] for item in data['data']]
                        return np.array(embeddings)
                    
                    elif response.status_code == 429:
                        delay = min(5.0 * (2 ** attempt), 30.0)
                        logger.warning(f"Rate limit, attente {delay}s...")
                        await asyncio.sleep(delay)
                        
                    else:
                        logger.error(f"Erreur API: {response.status_code}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(2.0 * (attempt + 1))
                            
            except Exception as e:
                logger.error(f"Erreur: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2.0 * (attempt + 1))
                else:
                    raise
        
        raise Exception("Échec après toutes les tentatives")
    
    async def search_for_entry(self, entry: Dict, k: int = 10) -> List[Dict]:
        """Recherche optimisée pour une entrée"""
        if not self.pattern_index:
            logger.error("Index non construit")
            return []
        
        # D'abord, utiliser l'analyseur de patterns pour un pré-filtrage
        pattern_matches = self.pattern_analyzer.find_matching_pattern(entry, self.patterns)
        
        # Si on a des correspondances très fortes, les utiliser directement
        if pattern_matches and pattern_matches[0][1] > 0.8:
            # Récupérer les tags correspondants
            pattern = pattern_matches[0][0]
            entry_year = self._extract_year(entry)
            
            results = []
            if entry_year and entry_year in pattern.tag_ids_by_year:
                # Tags pour l'année spécifique
                tag_ids = pattern.tag_ids_by_year[entry_year]
                for tag_id in tag_ids[:k]:
                    results.append({
                        'tag_id': tag_id,
                        'score': pattern_matches[0][1],
                        'method': 'pattern_match_exact_year'
                    })
            else:
                # Tous les tags du pattern
                for year, tag_ids in pattern.tag_ids_by_year.items():
                    for tag_id in tag_ids[:max(1, k // len(pattern.years))]:
                        results.append({
                            'tag_id': tag_id,
                            'score': pattern_matches[0][1] * 0.8,
                            'method': 'pattern_match_any_year'
                        })
            
            return results[:k]
        
        # Sinon, utiliser les embeddings
        query_text = self._build_query_text(entry)
        
        try:
            # Obtenir l'embedding de la requête
            query_embeddings = await self._get_embeddings_with_retry([query_text])
            query_embedding = query_embeddings[0]
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
            
            # Rechercher les patterns similaires
            scores, indices = self.pattern_index.search(
                query_embedding.reshape(1, -1).astype('float32'),
                min(k, self.pattern_index.ntotal)
            )
            
            # Convertir en résultats
            results = []
            entry_year = self._extract_year(entry)
            
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:
                    continue
                
                pattern_id = self.pattern_mappings[idx]
                pattern = self.patterns[pattern_id]
                
                # Récupérer les tags pour ce pattern
                if entry_year and entry_year in pattern.tag_ids_by_year:
                    tag_ids = pattern.tag_ids_by_year[entry_year]
                    for tag_id in tag_ids:
                        results.append({
                            'tag_id': tag_id,
                            'score': float(score),
                            'method': 'embedding_with_year',
                            'pattern_id': pattern_id
                        })
                else:
                    # Prendre un échantillon de chaque année
                    for year, tag_ids in pattern.tag_ids_by_year.items():
                        if tag_ids:
                            results.append({
                                'tag_id': tag_ids[0],
                                'score': float(score) * 0.8,
                                'method': 'embedding_sample',
                                'pattern_id': pattern_id,
                                'year': year
                            })
            
            return results[:k]
            
        except Exception as e:
            logger.error(f"Erreur recherche: {str(e)}")
            
            # Fallback sur la recherche par pattern
            results = []
            for pattern, score in pattern_matches[:5]:
                for year, tag_ids in pattern.tag_ids_by_year.items():
                    if tag_ids:
                        results.append({
                            'tag_id': tag_ids[0],
                            'score': score,
                            'method': 'fallback_pattern'
                        })
            
            return results[:k]
    
    def _extract_year(self, entry: Dict) -> Optional[int]:
        """Extrait l'année d'une entrée"""
        import re
        year_pattern = re.compile(r'\b(202[0-9]|203[0-5])\b')
        
        text = f"{entry.get('Description', '')} {entry.get('Axe', '')}"
        match = year_pattern.search(text)
        
        if match:
            return int(match.group(0))
        return None
    
    def _build_query_text(self, entry: Dict) -> str:
        """Construit le texte de requête pour l'embedding"""
        parts = []
        
        if entry.get('Sheet'):
            parts.append(entry['Sheet'])
        if entry.get('Axe'):
            parts.append(entry['Axe'])
        if entry.get('Description'):
            parts.append(entry['Description'])
        
        return " ".join(parts)