import re
import uuid
import logging
from typing import Dict, Any, List, Optional, Tuple
from app.models.schemas import (
    VisualEntity, VisualRelationship, VisualSourceTrace, CoordinateData,
    ConflictFlag, KnowledgeGraphResponse, SourceModality
)
from app.services.vision_engine import VisionEngine
from app.services.coordinate_extractor import CoordinateExtractor

logger = logging.getLogger(__name__)

class FusionEngine:
    """Core Intelligence Engine responsible for Multimodal Report + Image Fusion (Section 9.C - 9.G)"""

    def __init__(self):
        self.vision_engine = VisionEngine()
        self.entities: Dict[str, VisualEntity] = {}
        self.relationships: Dict[str, VisualRelationship] = {}
        self.conflicts: List[ConflictFlag] = []
        self.documents: Dict[str, Dict[str, Any]] = {}

    def clear(self):
        self.entities.clear()
        self.relationships.clear()
        self.conflicts.clear()
        self.documents.clear()

    def ingest_and_fuse_document(self, doc_data: Dict[str, Any]) -> KnowledgeGraphResponse:
        """
        Ingests a processed document (pages, text, embedded images),
        extracts text entities, analyzes images/maps with surrounding context,
        fuses textual and visual intelligence, and updates the unified knowledge graph.
        """
        doc_id = doc_data["document_id"]
        doc_name = doc_data["document_name"]
        self.documents[doc_id] = doc_data

        # 1. Extract text-level intelligence from all pages
        for page in doc_data.get("pages", []):
            page_num = page["page_number"]
            page_text = page["text"]

            self._extract_text_entities_and_relations(page_text, doc_id, doc_name, page_num)

            # 2. Extract visual intelligence from each embedded image on this page
            for img_info in page.get("images", []):
                img_path = img_info["file_path"]
                surrounding = img_info.get("surrounding_text", "")
                overlaid = img_info.get("overlaid_text", "")

                vision_result = self.vision_engine.analyze_image_or_map(
                    image_path=img_path,
                    document_id=doc_id,
                    document_name=doc_name,
                    page_number=page_num,
                    surrounding_text=surrounding,
                    explicit_ocr_text=overlaid
                )

                # Fuse visual findings into the unified graph
                self._fuse_visual_results(vision_result, doc_id, doc_name, page_num, surrounding)

        return self.get_unified_graph()

    def _extract_text_entities_and_relations(self, text: str, doc_id: str, doc_name: str, page_num: int):
        """Extracts text entities, events, coordinates, and relationships from narrative text."""
        if not text:
            return

        # Check for explicit coordinates in text
        coord = CoordinateExtractor.parse_coordinate_text(text)
        text_coord_trace = None
        if coord:
            text_coord_trace = VisualSourceTrace(
                document_id=doc_id,
                document_name=doc_name,
                page_number=page_num,
                extracted_label=coord.raw_text,
                extraction_type="COORDINATE_IN_TEXT",
                confidence=0.98,
                surrounding_text=text[:140],
                detection_method="TEXT_REPORT_PARSER"
            )
            coord.source_trace = text_coord_trace

        # Check for tactical entities mentioned in text
        entity_patterns = [
            (r'Sector\s+([A-Za-z0-9]+)', "SECTOR"),
            (r'Factory\s+([A-Za-z0-9]+)', "FACILITY"),
            (r'Checkpoint\s+([A-Za-z0-9]+)', "CHECKPOINT"),
            (r'Depot\s+([A-Za-z0-9]+)', "FACILITY"),
            (r'Airfield\s*([A-Za-z0-9]*)', "FACILITY"),
            (r'Radar\s*([A-Za-z0-9]*)', "FACILITY"),
            (r'Event\s+([A-Za-z0-9]+)', "EVENT"),
            (r'Operation\s+([A-Za-z0-9]+)', "EVENT")
        ]

        found_in_page = []

        for pattern, etype in entity_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for m in matches:
                full_name = m.group(0).strip()
                ent_key = self._normalize_entity_name(full_name)

                trace = VisualSourceTrace(
                    document_id=doc_id,
                    document_name=doc_name,
                    page_number=page_num,
                    extracted_label=full_name,
                    extraction_type=etype,
                    confidence=0.95,
                    surrounding_text=text[max(0, m.start()-40):min(len(text), m.end()+40)].strip(),
                    detection_method="TEXT_REPORT_PARSER"
                )

                if ent_key not in self.entities:
                    self.entities[ent_key] = VisualEntity(
                        id=ent_key,
                        name=full_name,
                        type=etype,
                        modality=SourceModality.TEXT_REPORT,
                        traceability=[trace],
                        confidence=0.95
                    )
                else:
                    self.entities[ent_key].traceability.append(trace)

                entity_obj = self.entities[ent_key]
                found_in_page.append(entity_obj)

                # Bind or check coordinate conflict across documents
                if coord and etype in ["SECTOR", "FACILITY", "CHECKPOINT"]:
                    self._merge_or_flag_coordinates(entity_obj, coord, f"Text Report ({doc_name})")

        # Detect narrative relationships: e.g. "observation was reported near Sector Alpha" or "Event A associated with Sector Alpha"
        sec_ent = next((e for e in found_in_page if e.type == "SECTOR"), None)
        evt_ent = next((e for e in found_in_page if e.type == "EVENT"), None)

        if not evt_ent and "observation" in text.lower():
            # Create synthetic Event entity for observed activity
            evt_key = f"event_obs_{doc_id}_{page_num}"
            evt_ent = VisualEntity(
                id=evt_key,
                name="Event A (Observation Activity)",
                type="EVENT",
                modality=SourceModality.TEXT_REPORT,
                traceability=[VisualSourceTrace(
                    document_id=doc_id,
                    document_name=doc_name,
                    page_number=page_num,
                    extracted_label="Observation Reported",
                    extraction_type="EVENT",
                    confidence=0.92,
                    surrounding_text=text[:120],
                    detection_method="TEXT_REPORT_PARSER"
                )]
            )
            self.entities[evt_key] = evt_ent

        if sec_ent and evt_ent:
            rel_id = f"rel_{evt_ent.id}_{sec_ent.id}"
            if rel_id not in self.relationships:
                self.relationships[rel_id] = VisualRelationship(
                    id=rel_id,
                    source=evt_ent.id,
                    target=sec_ent.id,
                    relation_type="OBSERVED_AT",
                    label="reported near",
                    provenance=SourceModality.TEXT_REPORT,
                    evidence_text=f"Report [{doc_name}, p.{page_num}] states observation activity near {sec_ent.name}",
                    confidence=0.94,
                    traceability=evt_ent.traceability[0] if evt_ent.traceability else None
                )

    def _fuse_visual_results(
        self,
        vision_res: Dict[str, Any],
        doc_id: str,
        doc_name: str,
        page_num: int,
        surrounding_text: str
    ):
        """
        Co-references visual entities & map features with narrative report entities.
        Addresses Section 9.C (Report + Image Fusion) & 9.D (Text inside Maps).
        """
        vis_coords: List[CoordinateData] = vision_res.get("coordinates", [])
        vis_entities: List[VisualEntity] = vision_res.get("entities", [])
        vis_relations: List[VisualRelationship] = vision_res.get("relationships", [])

        # Step 1: Add or resolve visual entities into global catalog
        for v_ent in vis_entities:
            ent_key = self._normalize_entity_name(v_ent.name)

            if ent_key in self.entities:
                # Entity was already known (either from text report or prior map)
                existing = self.entities[ent_key]
                existing.traceability.extend(v_ent.traceability)

                # Upgrade modality to fused if found in both text and image
                if existing.modality == SourceModality.TEXT_REPORT:
                    existing.modality = SourceModality.REPORT_IMAGE_FUSION

                # If map gives coordinates, check for conflicts or update
                if v_ent.coordinates:
                    self._merge_or_flag_coordinates(existing, v_ent.coordinates, f"Map Image ({doc_name})")
            else:
                v_ent.id = ent_key
                self.entities[ent_key] = v_ent

        # Step 2: Bind unassigned visual coordinates to co-referenced sector in surrounding report text
        for coord in vis_coords:
            # Check if surrounding text mentions a sector or facility
            for ent_key, entity in self.entities.items():
                if entity.name.lower() in surrounding_text.lower() and entity.type in ["SECTOR", "FACILITY", "CHECKPOINT"]:
                    self._merge_or_flag_coordinates(entity, coord, f"Map Image ({doc_name})")

        # Step 3: Establish Section 9.C & 9.D Report + Image Fusion relationships
        for v_rel in vis_relations:
            # Re-map source/target to canonical entity IDs
            src_key = self._normalize_entity_name(v_rel.source.replace("vis_", "").replace("ent_", "").replace("_", " "))
            tgt_key = self._normalize_entity_name(v_rel.target.replace("vis_", "").replace("ent_", "").replace("_", " "))

            if src_key in self.entities and tgt_key in self.entities:
                rel_id = f"rel_{src_key}_{tgt_key}"
                self.relationships[rel_id] = VisualRelationship(
                    id=rel_id,
                    source=src_key,
                    target=tgt_key,
                    relation_type=v_rel.relation_type,
                    label=v_rel.label,
                    provenance=SourceModality.MAP_IMAGE,
                    evidence_text=f"Visual link confirmed on {v_rel.evidence_text} [{doc_name}, Page {page_num}]",
                    confidence=v_rel.confidence,
                    traceability=v_rel.traceability
                )

    def _merge_or_flag_coordinates(self, entity: VisualEntity, new_coord: CoordinateData, new_source_label: str):
        """
        Section 9.E:
        - Store coordinates as structured attributes.
        - Merge if referring to same location.
        - Flag conflict if coordinates across sources mismatch (> 800m).
        """
        if not entity.coordinates:
            entity.coordinates = new_coord
            if new_coord.source_trace:
                entity.traceability.append(new_coord.source_trace)
            return

        existing_coord = entity.coordinates
        existing_source = existing_coord.source_trace.document_name if existing_coord.source_trace else "Prior Record"

        # Check for conflict
        conflict = CoordinateExtractor.check_coordinate_conflict(
            entity_name=entity.name,
            coord_a=existing_coord,
            source_a_name=existing_source,
            coord_b=new_coord,
            source_b_name=new_source_label,
            distance_threshold_meters=800.0
        )

        if conflict:
            # Avoid duplicate conflict alerts for same entity and source
            duplicate = any(
                c.entity_name == entity.name and
                abs(c.source_b.get("latitude", 0) - new_coord.latitude) < 0.001 and
                abs(c.source_b.get("longitude", 0) - new_coord.longitude) < 0.001
                for c in self.conflicts
            )
            if not duplicate:
                entity.has_conflict = True
                entity.conflict_ids.append(conflict.id)
                self.conflicts.append(conflict)
                logger.warning(f"CONFLICT DETECTED for {entity.name}: {conflict.description}")
        else:
            # Within tolerance: merge information, keep highest precision, append provenance
            if new_coord.source_trace:
                entity.traceability.append(new_coord.source_trace)

    def _normalize_entity_name(self, name: str) -> str:
        clean = re.sub(r'[^a-zA-Z0-9]', '_', name.lower().strip())
        return f"ent_{clean}"

    def get_unified_graph(self) -> KnowledgeGraphResponse:
        """Returns the unified multi-modal knowledge graph complying with Section 9.G"""
        node_list = list(self.entities.values())
        edge_list = list(self.relationships.values())

        stats = {
            "total_entities": len(node_list),
            "total_relationships": len(edge_list),
            "fused_entities": len([n for n in node_list if n.modality == SourceModality.REPORT_IMAGE_FUSION]),
            "visual_entities": len([n for n in node_list if n.modality == SourceModality.MAP_IMAGE]),
            "text_entities": len([n for n in node_list if n.modality == SourceModality.TEXT_REPORT]),
            "conflicts_flagged": len(self.conflicts)
        }

        return KnowledgeGraphResponse(
            nodes=node_list,
            edges=edge_list,
            conflicts=self.conflicts,
            stats=stats
        )
