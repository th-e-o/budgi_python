# modules/budget_mapper.py 
from modules.embedding_manager import OptimizedMistralEmbeddingsManager
import logging
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime  # AJOUTER CET IMPORT
import pandas as pd  # AJOUTER CET IMPORT si pas déjà présent
import asyncio
import re  # AJOUTER CET IMPORT si pas déjà présent

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
    
    def _create_detailed_mapping(self, entry: Dict, tag: Dict, score: float, 
                           matches: List[str] = None) -> Dict:
        """Crée un mapping détaillé entre une entrée et un tag"""
        return {
            'entry_id': entry.get('id', ''),
            'Description': entry.get('Description', ''),
            'Montant': entry.get('Montant', 0),
            'Axe': entry.get('Axe', ''),
            'Nature': entry.get('Nature', ''),
            'Sheet': entry.get('Sheet', ''),
            'tag_id': tag.get('id', ''),
            'cellule': f"{tag.get('sheet_name', '')}!{tag.get('cell_address', '')}",
            'sheet_name': tag.get('sheet_name', ''),
            'cell_address': tag.get('cell_address', ''),
            'confidence_score': score,
            'matches': matches or [],
            'labels': tag.get('labels', []),
            'mapped': True
        }

    def _create_empty_mapping(self, entry: Dict) -> Dict:
        """Crée un mapping vide pour une entrée non mappée"""
        return {
            'entry_id': entry.get('id', ''),
            'Description': entry.get('Description', ''),
            'Montant': entry.get('Montant', 0),
            'Axe': entry.get('Axe', ''),
            'Nature': entry.get('Nature', ''),
            'Sheet': entry.get('Sheet', ''),
            'tag_id': None,
            'cellule': None,
            'sheet_name': None,
            'cell_address': None,
            'confidence_score': 0.0,
            'matches': [],
            'labels': [],
            'mapped': False
        }

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

    def validate_and_prepare_mapping(self, mapping: List[Dict], 
                                workbook) -> Tuple[List[Dict], List[str]]:
        """Valide et prépare le mapping pour application dans Excel"""
        validated_mapping = []
        validation_issues = []
        
        for entry_mapping in mapping:
            if not entry_mapping.get('mapped'):
                continue
                
            # Vérifier que la cellule existe
            sheet_name = entry_mapping.get('sheet_name')
            cell_address = entry_mapping.get('cell_address')
            
            if not sheet_name or not cell_address:
                validation_issues.append(
                    f"⚠️ Mapping invalide pour '{entry_mapping.get('Description')}': "
                    f"cellule non spécifiée"
                )
                continue
            
            if sheet_name not in workbook.sheetnames:
                validation_issues.append(
                    f"⚠️ Feuille '{sheet_name}' non trouvée dans le workbook"
                )
                continue
            
            # Vérifier le format de l'adresse de cellule
            import re
            if not re.match(r'^[A-Z]+[0-9]+$', cell_address):
                validation_issues.append(
                    f"⚠️ Adresse de cellule invalide: {cell_address}"
                )
                continue
            
            validated_mapping.append(entry_mapping)
        
        return validated_mapping, validation_issues

    def enrich_entries_with_mapping(self, entries_df: pd.DataFrame, 
                                mapping: List[Dict]) -> pd.DataFrame:
        """Enrichit le DataFrame des entrées avec les informations de mapping"""
        import pandas as pd
        
        # Créer un DataFrame du mapping
        mapping_df = pd.DataFrame(mapping)
        
        # Ajouter les colonnes de mapping
        entries_df['CelluleCible'] = ''
        entries_df['ConfidenceScore'] = 0.0
        entries_df['IsMapped'] = False
        entries_df['LabelsTag'] = ''     # NOUVEAU : Labels du tag
        
        # Appliquer le mapping
        for idx, mapping_entry in enumerate(mapping):
            # Trouver l'entrée correspondante
            # Utiliser la description et le montant pour matcher
            mask = (
                (entries_df['Description'] == mapping_entry['Description']) &
                (entries_df['Montant'] == mapping_entry['Montant'])
            )
            
            if mask.any():
                entries_df.loc[mask, 'CelluleCible'] = mapping_entry.get('cellule', '')
                entries_df.loc[mask, 'ConfidenceScore'] = mapping_entry.get('confidence_score', 0.0)
                entries_df.loc[mask, 'IsMapped'] = mapping_entry.get('mapped', False)
        
                if mapping_entry.get('mapped'):
                    # ID du tag
                    tag_id = mapping_entry.get('tag_id', '')
                    
                    # Labels du tag (formatés pour l'affichage)
                    labels = mapping_entry.get('labels', [])
                    if labels:
                        # Joindre les labels avec un séparateur
                        labels_str = " | ".join(str(l) for l in labels[:5])  # Limiter à 5 labels
                        if len(labels) > 5:
                            labels_str += f" ... (+{len(labels)-5})"
                        entries_df.loc[mask, 'LabelsTag'] = labels_str
        
        return entries_df

    def generate_mapping_report(self, mapping: List[Dict], entries_df) -> Dict:
        """Génère un rapport détaillé du mapping"""
        import pandas as pd
        
        total_entries = len(entries_df)
        mapped_entries = [m for m in mapping if m.get('mapped')]
        unmapped_entries = [m for m in mapping if not m.get('mapped')]
        
        # Analyser par confiance
        confidence_bins = {
            'Très élevé (>90%)': [],
            'Élevé (70-90%)': [],
            'Moyen (50-70%)': [],
            'Faible (<50%)': []
        }
        
        for m in mapped_entries:
            score = m.get('confidence_score', 0)
            if score > 0.9:
                confidence_bins['Très élevé (>90%)'].append(m)
            elif score > 0.7:
                confidence_bins['Élevé (70-90%)'].append(m)
            elif score > 0.5:
                confidence_bins['Moyen (50-70%)'].append(m)
            else:
                confidence_bins['Faible (<50%)'].append(m)
        
        # Compter par confiance
        by_confidence = {k: len(v) for k, v in confidence_bins.items()}
        
        # Calculer les métriques
        mapping_rate = (len(mapped_entries) / total_entries * 100) if total_entries > 0 else 0
        avg_confidence = (
            sum(m.get('confidence_score', 0) for m in mapped_entries) / len(mapped_entries)
        ) if mapped_entries else 0
        
        # Identifier les entrées à faible confiance
        low_confidence_items = []
        for m in mapped_entries:
            if m.get('confidence_score', 0) < 0.7:
                low_confidence_items.append({
                    'description': m.get('Description', ''),
                    'montant': m.get('Montant', 0),
                    'cellule': m.get('cellule', ''),
                    'confidence': m.get('confidence_score', 0),
                    'matches': m.get('matches', [])
                })
        
        # Identifier les non mappés
        unmapped_items = []
        for m in unmapped_entries:
            unmapped_items.append({
                'description': m.get('Description', ''),
                'montant': m.get('Montant', 0),
                'axe': m.get('Axe', ''),
                'nature': m.get('Nature', '')
            })
        
        return {
            'summary': {
                'total_entries': total_entries,
                'mapped_entries': len(mapped_entries),
                'unmapped_entries': len(unmapped_entries),
                'mapping_rate': mapping_rate,
                'average_confidence': avg_confidence
            },
            'by_confidence': by_confidence,
            'low_confidence': low_confidence_items,
            'unmapped': unmapped_items
        }

    def apply_mapping_to_excel(self, workbook, mapping: List[Dict], 
                            entries_df) -> Tuple[int, List[str], List[Dict]]:
        """Applique le mapping dans le workbook Excel"""
        success_count = 0
        errors = []
        modified_cells = []
        
        for mapping_entry in mapping:
            if not mapping_entry.get('mapped'):
                continue
            
            try:
                sheet_name = mapping_entry.get('sheet_name')
                cell_address = mapping_entry.get('cell_address')
                montant = mapping_entry.get('Montant', 0)
                
                if sheet_name not in workbook.sheetnames:
                    errors.append(f"Feuille '{sheet_name}' non trouvée")
                    continue
                
                sheet = workbook[sheet_name]
                
                # Écrire la valeur
                sheet[cell_address] = montant
                
                success_count += 1
                modified_cells.append({
                    'sheet': sheet_name,
                    'cell': cell_address,
                    'value': montant,
                    'description': mapping_entry.get('Description', '')
                })
                
            except Exception as e:
                errors.append(f"Erreur pour {mapping_entry.get('cellule', '?')}: {str(e)}")
        
        return success_count, errors, modified_cells

    def create_mapping_summary(self, mapping: List[Dict], 
                            modified_cells: List[Dict]) -> str:
        """Crée un résumé textuel du mapping"""
        summary_lines = []
        summary_lines.append("=== RÉSUMÉ DU MAPPING ===")
        summary_lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary_lines.append("")
        
        # Statistiques
        total = len(mapping)
        mapped = len([m for m in mapping if m.get('mapped')])
        summary_lines.append(f"Total entrées: {total}")
        summary_lines.append(f"Entrées mappées: {mapped}")
        summary_lines.append(f"Taux de mapping: {(mapped/total*100):.1f}%")
        summary_lines.append("")
        
        # Détails par sheet
        by_sheet = {}
        for cell in modified_cells:
            sheet = cell['sheet']
            if sheet not in by_sheet:
                by_sheet[sheet] = []
            by_sheet[sheet].append(cell)
        
        summary_lines.append("=== MODIFICATIONS PAR FEUILLE ===")
        for sheet, cells in by_sheet.items():
            summary_lines.append(f"\n{sheet}: {len(cells)} cellules")
            for cell in cells[:5]:  # Limiter à 5 exemples
                summary_lines.append(f"  - {cell['cell']}: {cell['value']:,.2f} €")
            if len(cells) > 5:
                summary_lines.append(f"  ... et {len(cells) - 5} autres")
        
        return "\n".join(summary_lines)
    
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
            tag = candidate['tag']  # CORRECTION ICI : candidate['tag'] au lieu de candidate.tag
            labels_preview = ', '.join(str(l)[:50] for l in tag.get('labels', [])[:3])
            candidates_desc.append(
                f"{i}) {tag.get('sheet_name')}!{tag.get('cell_address')} "
                f"[Similarité: {candidate['score']:.3f}]\n   Labels: {labels_preview}"  # Et ici candidate['score']
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
                            selected['tag'],  # CORRECTION : selected['tag'] au lieu de selected.tag
                            selected['score'],  # CORRECTION : selected['score'] au lieu de selected.score
                            ['llm_selected', f'from_top_{len(candidates)}']
                        )
        except Exception as e:
            logger.error(f"Erreur LLM: {str(e)}")
            
        return None