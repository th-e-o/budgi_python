# modules/embeddings_manager.py
import numpy as np
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
import faiss
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EmbeddingResult:
    """Résultat d'une recherche par embedding"""
    tag_id: str
    score: float
    tag: Dict
    sheet_name: str

class EmbeddingsManager:
    """Gestionnaire d'embeddings pour la recherche sémantique"""
    
    def __init__(self, model_name: str = "camembert-base"):
        # Utiliser CamemBERT pour le français
        self.model = SentenceTransformer(f"sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        self.index = None
        self.tag_mappings = {}
        self.embeddings_cache = {}
        
    def build_index(self, tags: List[Dict]) -> None:
        """Construit l'index FAISS avec les embeddings des tags"""
        # Créer les textes à encoder pour chaque tag
        tag_texts = []
        valid_tags = []
        
        for tag in tags:
            # Combiner tous les labels du tag pour créer une représentation textuelle
            labels = tag.get('labels', [])
            if not labels:
                continue
                
            # Créer un texte représentatif du tag
            tag_text = " ".join(str(label) for label in labels[:5])  # Limiter pour éviter trop de bruit
            tag_texts.append(tag_text)
            valid_tags.append(tag)
            
        if not tag_texts:
            logger.warning("Aucun tag valide pour construire l'index")
            return
            
        # Générer les embeddings
        logger.info(f"Génération des embeddings pour {len(tag_texts)} tags...")
        embeddings = self.model.encode(tag_texts, show_progress_bar=True)
        
        # Normaliser les embeddings pour la similarité cosinus
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        # Créer l'index FAISS
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner Product = Cosine similarity avec vecteurs normalisés
        self.index.add(embeddings.astype('float32'))
        
        # Stocker les mappings
        for i, tag in enumerate(valid_tags):
            self.tag_mappings[i] = tag
            
        logger.info(f"Index construit avec {len(valid_tags)} tags")
        
    def search_similar_tags(self, query: str, sheet_filter: Optional[str] = None, 
                          k: int = 20) -> List[EmbeddingResult]:
        """Recherche les k tags les plus similaires à la requête"""
        if not self.index:
            logger.error("Index non construit")
            return []
            
        # Encoder la requête
        query_embedding = self.model.encode([query])
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        # Rechercher dans l'index
        scores, indices = self.index.search(query_embedding.astype('float32'), k * 2)  # *2 pour avoir de la marge avec le filtre
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:  # FAISS retourne -1 pour les résultats non trouvés
                continue
                
            tag = self.tag_mappings.get(idx)
            if not tag:
                continue
                
            # Appliquer le filtre de sheet si spécifié
            if sheet_filter and tag.get('sheet_name') != sheet_filter:
                continue
                
            results.append(EmbeddingResult(
                tag_id=tag.get('id', str(idx)),
                score=float(score),
                tag=tag,
                sheet_name=tag.get('sheet_name', '')
            ))
            
            if len(results) >= k:
                break
                
        return results
        
    def get_embedding_for_entry(self, entry: Dict) -> np.ndarray:
        """Génère l'embedding pour une entrée budgétaire"""
        # Créer une représentation textuelle de l'entrée
        text_parts = []
        
        if entry.get('Axe'):
            text_parts.append(f"Axe: {entry['Axe']}")
        if entry.get('Description'):
            text_parts.append(entry['Description'])
        if entry.get('Nature'):
            text_parts.append(f"Nature: {entry['Nature']}")
        if entry.get('SourcePhrase'):
            # Prendre seulement le début pour éviter trop de bruit
            text_parts.append(entry['SourcePhrase'][:200])
            
        entry_text = " ".join(text_parts)
        
        # Utiliser le cache si possible
        if entry_text in self.embeddings_cache:
            return self.embeddings_cache[entry_text]
            
        # Générer l'embedding
        embedding = self.model.encode([entry_text])[0]
        embedding = embedding / np.linalg.norm(embedding)
        
        # Mettre en cache
        self.embeddings_cache[entry_text] = embedding
        
        return embedding