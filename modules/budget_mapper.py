# modules/budget_mapper.py 
from modules.embedding_manager import OptimizedMistralEmbeddingsManager
import logging
from typing import List, Dict, Optional, Tuple, Set

logger = logging.getLogger(__name__)

class BudgetMapper:
    """Module optimisé pour mapper les entrées budgétaires aux cellules Excel"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.embeddings_manager = OptimizedMistralEmbeddingsManager()
        self.tag_lookup = {}

    async def map_entries_to_cells(self, entries: List[Dict], tags: List[Dict], 
                                progress_callback=None) -> List[Dict]:
        """Version optimisée du mapping"""
        if not entries or not tags:
            return []
        
        # Créer un lookup des tags
        self.tag_lookup = {tag['id']: tag for tag in tags}
        
        # Construire l'index optimisé
        await self.embeddings_manager.build_optimized_index(tags, progress_callback)
        
        all_mappings = []
        
        for idx, entry in enumerate(entries):
            if progress_callback:
                progress = 20 + (idx / len(entries)) * 80
                progress_callback(progress, f"Mapping {idx+1}/{len(entries)}")
            
            # Recherche optimisée
            results = await self.embeddings_manager.search_for_entry(entry, k=10)
            
            if not results:
                all_mappings.append(self._create_empty_mapping(entry))
                continue
            
            # Récupérer les tags complets
            candidate_tags = []
            for result in results:
                tag_id = result['tag_id']
                if tag_id in self.tag_lookup:
                    tag = self.tag_lookup[tag_id]
                    candidate_tags.append({
                        'tag': tag,
                        'score': result['score'],
                        'method': result.get('method', 'unknown')
                    })
            
            if not candidate_tags:
                all_mappings.append(self._create_empty_mapping(entry))
                continue
            
            # Décision
            if candidate_tags[0]['score'] > 0.85 and candidate_tags[0]['method'] in ['pattern_match_exact_year', 'embedding_with_year']:
                # Très haute confiance
                mapping = self._create_detailed_mapping(
                    entry,
                    candidate_tags[0]['tag'],
                    candidate_tags[0]['score'],
                    [candidate_tags[0]['method']]
                )
                all_mappings.append(mapping)
            else:
                # Utiliser le LLM pour décider
                best_mapping = await self._llm_select_from_candidates(entry, candidate_tags[:5])
                if best_mapping:
                    all_mappings.append(best_mapping)
                else:
                    # Fallback
                    mapping = self._create_detailed_mapping(
                        entry,
                        candidate_tags[0]['tag'],
                        candidate_tags[0]['score'],
                        ['fallback']
                    )
                    all_mappings.append(mapping)
        
        return all_mappings
    
    def _build_search_query(self, entry: Dict) -> str:
        """Construit une requête optimisée pour la recherche d'embeddings"""
        parts = []
        
        # Prioriser les champs importants
        if entry.get('Axe'):
            parts.append(f"Axe {entry['Axe']}")
        if entry.get('Description'):
            parts.append(entry['Description'])
        if entry.get('Nature'):
            parts.append(f"{entry['Nature']}")
        
        # Ajouter des informations contextuelles
        if entry.get('Montant'):
            montant = entry['Montant']
            if montant >= 1_000_000:
                parts.append("millions d'euros")
            elif montant >= 1_000:
                parts.append("milliers d'euros")
                
        # Ajouter l'année si présente dans la description
        import re
        year_pattern = r'\b(202[0-9]|203[0-5])\b'
        text = " ".join(parts)
        years = re.findall(year_pattern, text)
        if years:
            parts.extend([f"année {year}" for year in years])
                
        return " ".join(parts)
    
    async def _llm_select_from_candidates(self, entry: Dict, 
                                        candidates: List) -> Optional[Dict]:
        """Utilise le LLM pour sélectionner parmi les candidats basés sur embedding"""
        
        entry_desc = f"""
Entrée budgétaire:
- Axe: {entry.get('Axe', 'N/A')}
- Description: {entry.get('Description', 'N/A')}
- Montant: {entry.get('Montant', 'N/A')} {entry.get('Unité', '')}
- Nature: {entry.get('Nature', 'N/A')}
- Sheet cible: {entry.get('Sheet', 'N/A')}
"""
        
        candidates_desc = []
        for i, candidate in enumerate(candidates):
            tag = candidate.tag
            labels_preview = ', '.join(str(l)[:50] for l in tag.get('labels', [])[:3])
            candidates_desc.append(
                f"{i}) {tag.get('sheet_name')}!{tag.get('cell_address')} "
                f"[Similarité: {candidate.score:.3f}]\n   Labels: {labels_preview}"
            )
            
        prompt = f"""{entry_desc}

Cellules candidates (classées par similarité sémantique):
{chr(10).join(candidates_desc)}

Choisis le numéro (0-9) de la cellule la plus appropriée ou 'AUCUN'."""
        
        messages = [
            {"role": "system", "content": "Expert en mapping budgétaire. Répond uniquement avec le numéro ou 'AUCUN'."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = await self.llm_client.chat(messages)
            if response:
                import re
                match = re.search(r'\b(\d)\b', response)
                if match:
                    idx = int(match.group(1))
                    if 0 <= idx < len(candidates):
                        selected = candidates[idx]
                        return self._create_detailed_mapping(
                            entry, 
                            selected.tag,
                            selected.score,
                            ['llm_selected', f'from_top_{len(candidates)}']
                        )
        except Exception as e:
            logger.error(f"Erreur LLM: {str(e)}")
            
        return None