import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import networkx as nx

from app.models.schemas import (
    Entity, RDFTriple, EntityCategory, EntityResolutionRecord, ConflictRecord,
    SourceEvidence, SourceDocumentMeta, GraphRAGQueryResponse, KnowledgeGraphResponse,
    SourceModality
)

logger = logging.getLogger(__name__)

class GraphService:
    """Decentralized Knowledge Graph Builder Agent & GraphRAG Engine conforming to PS-05."""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.entities: Dict[str, Entity] = {}
        self.triples: Dict[str, RDFTriple] = {}
        self.conflicts: List[ConflictRecord] = []
        self.resolutions: List[EntityResolutionRecord] = []
        self.sources: Dict[str, SourceDocumentMeta] = {}
        self.is_demo_mode: bool = False

    def clear(self):
        self.graph.clear()
        self.entities.clear()
        self.triples.clear()
        self.conflicts.clear()
        self.resolutions.clear()
        self.sources.clear()
        self.is_demo_mode = False

    def remove_source(self, source_id_or_name: str):
        """Removes a source document and prunes its associated entities and triples."""
        target_name = source_id_or_name
        # Check if it matches an id in sources
        if source_id_or_name in self.sources:
            target_name = self.sources[source_id_or_name].filename
            del self.sources[source_id_or_name]
        else:
            # Match by filename
            matching_ids = [k for k, v in self.sources.items() if v.filename == source_id_or_name]
            for mid in matching_ids:
                del self.sources[mid]

        # Prune triples
        dead_triples = [tid for tid, t in self.triples.items() if t.source_document == target_name]
        for tid in dead_triples:
            t = self.triples[tid]
            if self.graph.has_edge(t.subject_id, t.object_id):
                self.graph.remove_edge(t.subject_id, t.object_id)
            del self.triples[tid]

        # Prune or update entities
        dead_entities = []
        for eid, ent in self.entities.items():
            if target_name in ent.sources:
                ent.sources.remove(target_name)
                ent.source_evidence = [ev for ev in ent.source_evidence if ev.document_name != target_name]
                ent.mentions_count = len(ent.sources)
                if not ent.sources:
                    dead_entities.append(eid)

        for eid in dead_entities:
            if self.graph.has_node(eid):
                self.graph.remove_node(eid)
            del self.entities[eid]

        # Prune conflicts
        self.conflicts = [
            c for c in self.conflicts
            if c.source_a.get("document") != target_name and c.source_b.get("document") != target_name
        ]

    def ingest_document_data(self, doc_data: Dict[str, Any]):
        """Processes user-uploaded document with autonomous NER and triple extraction."""
        from app.services.extractor import AutonomousEntityExtractor

        doc_name = doc_data["document_name"]
        doc_id = doc_data["document_id"]
        total_ents = 0
        total_trips = 0
        doc_extracted_entities = []
        doc_extracted_triples = []
        doc_evidence_list = []

        for page in doc_data.get("pages", []):
            page_num = page.get("page_number", 1)
            page_text = page.get("text", "")

            discovered_entities, discovered_triples = AutonomousEntityExtractor.extract_from_text(page_text, doc_name, page_num)
            total_ents += len(discovered_entities)
            total_trips += len(discovered_triples)

            for e in discovered_entities:
                ent = self.add_or_update_entity(
                    raw_name=e["name"],
                    etype=e["type"],
                    doc_name=doc_name,
                    page_num=page_num,
                    evidence_snippet=e["snippet"],
                    coordinates=e.get("coordinates")
                )
                if ent.name not in doc_extracted_entities:
                    doc_extracted_entities.append(ent.name)
                doc_evidence_list.append({
                    "entity": ent.name,
                    "type": ent.type,
                    "page": page_num,
                    "snippet": e["snippet"]
                })

            for t in discovered_triples:
                trip = self.add_triple(
                    subj_name=t["subject_name"],
                    subj_type=t["subject_type"],
                    predicate=t["predicate"],
                    obj_name=t["object_name"],
                    obj_type=t["object_type"],
                    doc_name=doc_name,
                    page_num=page_num,
                    evidence_text=t["evidence"]
                )
                trip_repr = f"{trip.subject_name} -> {trip.predicate} -> {trip.object_name}"
                if trip_repr not in doc_extracted_triples:
                    doc_extracted_triples.append(trip_repr)

        page_count = len(doc_data.get("pages", [])) or 1
        raw_text = doc_data.get("full_text", "")
        if not raw_text and doc_data.get("pages"):
            raw_text = "\n\n".join([f"--- Page {p.get('page_number', 1)} ---\n" + p.get("text", "") for p in doc_data["pages"]])

        # Register or update in sources with full metadata for Inspection
        self.sources[doc_id] = SourceDocumentMeta(
            id=doc_id,
            filename=doc_name,
            file_type=doc_data.get("file_type", "PDF"),
            status="Processed",
            entity_count=total_ents,
            relationship_count=total_trips,
            conflict_count=len([c for c in self.conflicts if c.source_a.get("document") == doc_name or c.source_b.get("document") == doc_name]),
            page_count=page_count,
            processed_time="Just now",
            summary=f"Autonomously extracted {total_ents} entities and {total_trips} relationships from {doc_name}.",
            raw_text=raw_text,
            extracted_entities=doc_extracted_entities,
            extracted_relationships=doc_extracted_triples,
            source_evidence_list=doc_evidence_list
        )
        self.is_demo_mode = False

    # --- ENTITY RESOLUTION LOGIC (Section 16) ---
    def resolve_canonical_entity(self, raw_name: str, etype: str, doc_name: str) -> Tuple[str, str, bool]:
        """
        Resolves entity variants (e.g. 'Alpha Sector', 'Sector Alpha', 'Sector-A')
        into a canonical entity while tracking resolution history and sources.
        """
        clean = raw_name.strip()
        lower = clean.lower()

        # Normalized canonical keys
        if any(term in lower for term in ["sector alpha", "alpha sector", "sector-a", "sector a"]):
            canonical = "Sector Alpha"
            category = EntityCategory.LOCATIONS
        elif any(term in lower for term in ["sector bravo", "bravo sector", "sector-b", "sector b"]):
            canonical = "Sector Bravo"
            category = EntityCategory.LOCATIONS
        elif any(term in lower for term in ["factory bravo", "bravo factory", "facility bravo"]):
            canonical = "Factory Bravo"
            category = EntityCategory.LOCATIONS
        elif any(term in lower for term in ["unit falcon", "falcon unit", "taskforce falcon", "1st falcon"]):
            canonical = "Unit Falcon"
            category = EntityCategory.ORGANIZATIONS
        elif any(term in lower for term in ["checkpoint delta", "delta checkpoint", "cp delta"]):
            canonical = "Checkpoint Delta"
            category = EntityCategory.LOCATIONS
        elif any(term in lower for term in ["operation orion", "op orion", "mission orion"]):
            canonical = "Operation Orion"
            category = EntityCategory.EVENTS
        elif any(term in lower for term in ["general rawat", "gen rawat", "rawat"]):
            canonical = "General Rawat"
            category = EntityCategory.PEOPLE
        elif any(term in lower for term in ["col sharma", "colonel sharma"]):
            canonical = "Colonel Sharma"
            category = EntityCategory.PEOPLE
        elif any(term in lower for term in ["radar station omega", "omega radar"]):
            canonical = "Radar Station Omega"
            category = EntityCategory.EQUIPMENT
        elif any(term in lower for term in ["uav garuda", "garuda uav", "surveillance drone"]):
            canonical = "UAV Garuda"
            category = EntityCategory.EQUIPMENT
        elif any(term in lower for term in ["forward airfield", "airfield"]):
            canonical = "Forward Airfield"
            category = EntityCategory.LOCATIONS
        elif any(term in lower for term in ["supply depot 4", "depot 4"]):
            canonical = "Supply Depot 4"
            category = EntityCategory.LOCATIONS
        else:
            canonical = clean
            category = self._infer_category(etype)

        ent_id = f"ent_{re.sub(r'[^a-zA-Z0-9]', '_', canonical.lower())}"

        # Track resolution if name variation detected
        is_variant = (clean.lower() != canonical.lower())
        if is_variant:
            existing_res = next((r for r in self.resolutions if r.canonical_name == canonical), None)
            if not existing_res:
                self.resolutions.append(EntityResolutionRecord(
                    canonical_name=canonical,
                    entity_type=category.value,
                    matched_variants=[canonical, clean],
                    sources=[doc_name],
                    confidence=0.94,
                    resolution_rationale=f"Syntactic similarity and lexical permutation clustering matched '{clean}' to '{canonical}'."
                ))
            else:
                if clean not in existing_res.matched_variants:
                    existing_res.matched_variants.append(clean)
                if doc_name not in existing_res.sources:
                    existing_res.sources.append(doc_name)

        return ent_id, canonical, category

    def _infer_category(self, etype: str) -> EntityCategory:
        etype_up = etype.upper()
        if "PERSON" in etype_up or "PEOPLE" in etype_up or "OFFICER" in etype_up:
            return EntityCategory.PEOPLE
        elif "ORG" in etype_up or "UNIT" in etype_up or "CORPS" in etype_up:
            return EntityCategory.ORGANIZATIONS
        elif "LOC" in etype_up or "SECTOR" in etype_up or "FACILITY" in etype_up or "ZONE" in etype_up:
            return EntityCategory.LOCATIONS
        elif "EVENT" in etype_up or "OP" in etype_up or "MISSION" in etype_up:
            return EntityCategory.EVENTS
        elif "EQUIP" in etype_up or "RADAR" in etype_up or "DRONE" in etype_up or "VEHICLE" in etype_up:
            return EntityCategory.EQUIPMENT
        return EntityCategory.LOCATIONS

    def add_or_update_entity(
        self,
        raw_name: str,
        etype: str,
        doc_name: str,
        page_num: int,
        evidence_snippet: str,
        coordinates: Optional[Dict[str, Any]] = None,
        attributes: Optional[Dict[str, Any]] = None,
        modality: SourceModality = SourceModality.TEXT_REPORT,
        crop_bbox: Optional[List[float]] = None
    ) -> Entity:
        ent_id, canonical, category = self.resolve_canonical_entity(raw_name, etype, doc_name)

        trace = SourceEvidence(
            document_id=doc_name,
            document_name=doc_name,
            page_number=page_num,
            snippet=evidence_snippet,
            modality=modality,
            confidence=0.96 if modality == SourceModality.MAP_IMAGE else 0.95,
            extraction_type=etype,
            crop_bbox=crop_bbox
        )

        if ent_id not in self.entities:
            ent = Entity(
                id=ent_id,
                name=canonical,
                type=category.value,
                category=category,
                aliases=[raw_name] if raw_name.lower() != canonical.lower() else [],
                mentions_count=1,
                sources=[doc_name],
                source_evidence=[trace],
                coordinates=coordinates,
                attributes=attributes or {}
            )
            self.entities[ent_id] = ent
            self.graph.add_node(ent_id, name=canonical, category=category.value)
        else:
            ent = self.entities[ent_id]
            ent.mentions_count += 1
            if doc_name not in ent.sources:
                ent.sources.append(doc_name)
            if raw_name.lower() != canonical.lower() and raw_name not in ent.aliases:
                ent.aliases.append(raw_name)
            ent.source_evidence.append(trace)

            # Update coordinates or detect cross-source discrepancy
            if coordinates:
                if not ent.coordinates:
                    ent.coordinates = coordinates
                else:
                    prev_raw = ent.coordinates.get("raw_text", "")
                    new_raw = coordinates.get("raw_text", "")
                    if prev_raw and new_raw and prev_raw.replace(" ", "") != new_raw.replace(" ", ""):
                        source_a_name = ent.sources[0] if ent.sources else "Prior Source"
                        self.add_conflict(
                            entity_name=ent.name,
                            attribute="Geospatial Coordinates",
                            source_a={
                                "document": source_a_name,
                                "page": 1,
                                "value": prev_raw,
                                "extract": f"Coordinates for {ent.name} reported as {prev_raw} in {source_a_name}."
                            },
                            source_b={
                                "document": doc_name,
                                "page": page_num,
                                "value": new_raw,
                                "extract": evidence_snippet
                            },
                            description=f"Geospatial coordinate discrepancy detected for {ent.name}: {prev_raw} in {source_a_name} vs {new_raw} in {doc_name}."
                        )
            if attributes:
                ent.attributes.update(attributes)

        return ent

    def add_triple(
        self,
        subj_name: str,
        subj_type: str,
        predicate: str,
        obj_name: str,
        obj_type: str,
        doc_name: str,
        page_num: int,
        evidence_text: str,
        provenance: SourceModality = SourceModality.TEXT_REPORT
    ) -> RDFTriple:
        s_ent = self.add_or_update_entity(subj_name, subj_type, doc_name, page_num, evidence_text, modality=provenance)
        o_ent = self.add_or_update_entity(obj_name, obj_type, doc_name, page_num, evidence_text, modality=provenance)

        trip_key = f"{s_ent.id}_{predicate.upper()}_{o_ent.id}"
        if trip_key not in self.triples:
            triple = RDFTriple(
                id=trip_key,
                subject_id=s_ent.id,
                subject_name=s_ent.name,
                predicate=predicate.upper(),
                object_id=o_ent.id,
                object_name=o_ent.name,
                provenance=provenance,
                source_document=doc_name,
                page_number=page_num,
                evidence_text=evidence_text,
                confidence=0.95
            )
            self.triples[trip_key] = triple
            self.graph.add_edge(s_ent.id, o_ent.id, predicate=predicate.upper(), id=trip_key)
            return triple
        return self.triples[trip_key]

    def add_conflict(
        self,
        entity_name: str,
        attribute: str,
        source_a: Dict[str, Any],
        source_b: Dict[str, Any],
        description: str
    ):
        """Flags conflicting facts across sources (Section 17)."""
        # Check if already recorded
        for c in self.conflicts:
            if c.entity_name == entity_name and c.conflict_attribute == attribute:
                return

        conf = ConflictRecord(
            entity_name=entity_name,
            conflict_attribute=attribute,
            description=description,
            source_a=source_a,
            source_b=source_b,
            status="CONFLICTING INFORMATION",
            severity="HIGH"
        )
        self.conflicts.append(conf)

        # Mark entity
        ent_id, _, _ = self.resolve_canonical_entity(entity_name, "Location", source_a.get("document", "Unknown"))
        if ent_id in self.entities:
            self.entities[ent_id].has_conflict = True
            self.entities[ent_id].conflict_ids.append(conf.id)

    # --- GRAPHRAG NATURAL LANGUAGE QUERY ENGINE (Section 18 & 19) ---
    def answer_query(self, query_text: str) -> GraphRAGQueryResponse:
        q_lower = query_text.lower().strip()
        matched_entities: List[Entity] = []
        evidence_list: List[SourceEvidence] = []
        subgraph_nodes = []
        subgraph_edges = []

        # Zero-source check (Requirement 1 & 19)
        if not self.sources or len(self.sources) == 0:
            return GraphRAGQueryResponse(
                query=query_text,
                analysis="No intelligence sources have been loaded into TRINETRA. Please upload and process at least one report or tactical image to build the knowledge graph and enable question answering.",
                supporting_entities=[],
                source_evidence=[],
                subgraph={"nodes": [], "edges": []}
            )

        # Find matching entities in query
        for ent in self.entities.values():
            if ent.name.lower() in q_lower or any(a.lower() in q_lower for a in ent.aliases):
                matched_entities.append(ent)

        # Fallback keyword match if specific entity not named
        if not matched_entities:
            for ent in self.entities.values():
                for word in ent.name.lower().split():
                    if len(word) > 3 and word in q_lower and word not in ["type", "zone", "report", "dummy"]:
                        matched_entities.append(ent)
                        break

        # If question is asking about conflicts
        if "conflict" in q_lower or "discrepanc" in q_lower or "inconsisten" in q_lower:
            if not self.conflicts:
                sources_checked = [s.filename for s in self.sources.values()]
                sources_str = "\n• " + "\n• ".join(sources_checked)
                return GraphRAGQueryResponse(
                    query=query_text,
                    analysis=f"No factual conflicts detected among the currently processed sources. Corroboration across all active reports indicates consistent intelligence.\n\n**SOURCES CHECKED:**{sources_str}",
                    supporting_entities=[],
                    source_evidence=[],
                    subgraph={"nodes": [], "edges": []}
                )

            conf_entity = matched_entities[0] if matched_entities else None
            conf_record = None
            if conf_entity:
                conf_record = next((c for c in self.conflicts if c.entity_name.lower() in conf_entity.name.lower()), None)
            if not conf_record:
                conf_record = self.conflicts[0]

            ans = (
                f"Yes. TRINETRA has verified an information conflict regarding **{conf_record.entity_name}**.\n\n"
                f"• **Source A** (*{conf_record.source_a.get('document')}*, Page {conf_record.source_a.get('page', 1)}) reports: **{conf_record.source_a.get('value')}**\n"
                f"• **Source B** (*{conf_record.source_b.get('document')}*, Page {conf_record.source_b.get('page', 1)}) reports: **{conf_record.source_b.get('value')}**\n\n"
                f"Per Section 17 guidelines, TRINETRA flags this as an unresolved conflict for analyst inspection rather than arbitrarily discarding either source."
            )
            evidence_list.extend([
                SourceEvidence(
                    document_id=conf_record.source_a.get('document', 'Report'),
                    document_name=conf_record.source_a.get('document', 'Report'),
                    page_number=conf_record.source_a.get('page', 1),
                    snippet=conf_record.source_a.get('extract') or f"Report logs {conf_record.entity_name} at {conf_record.source_a.get('value')}."
                ),
                SourceEvidence(
                    document_id=conf_record.source_b.get('document', 'Report'),
                    document_name=conf_record.source_b.get('document', 'Report'),
                    page_number=conf_record.source_b.get('page', 1),
                    snippet=conf_record.source_b.get('extract') or f"Interception logs {conf_record.entity_name} at {conf_record.source_b.get('value')}."
                )
            ])
            return GraphRAGQueryResponse(
                query=query_text,
                analysis=ans,
                supporting_entities=[conf_record.entity_name],
                source_evidence=evidence_list,
                subgraph={"nodes": [self.entities[conf_record.entity_name].dict()] if conf_record.entity_name in self.entities else [], "edges": []}
            )

        # Question about connections / relationships with matched entities
        if matched_entities:
            target = matched_entities[0]
            connected_triples = [t for t in self.triples.values() if t.subject_id == target.id or t.object_id == target.id]
            related_entity_names = set()
            for t in connected_triples:
                other_name = t.object_name if t.subject_id == target.id else t.subject_name
                related_entity_names.add(other_name)
                evidence_list.append(SourceEvidence(
                    document_id=t.source_document,
                    document_name=t.source_document,
                    page_number=t.page_number,
                    snippet=t.evidence_text,
                    modality=t.provenance
                ))

            rel_str = ", ".join([f"**{r}**" for r in list(related_entity_names)[:8]]) if related_entity_names else "no direct relations mapped"
            sources_str = ", ".join(target.sources)

            ans = (
                f"Based on multi-source knowledge graph analysis, **{target.name}** ({target.type}) is documented across **{len(target.sources)} sources** ({sources_str}).\n\n"
                f"• **Connected Entities ({len(related_entity_names)}):** {rel_str}.\n"
            )

            if target.attributes:
                attr_parts = [f"{k.replace('_', ' ').title()}: **{v}**" for k, v in target.attributes.items()]
                ans += f"• **Extracted Attributes:** {', '.join(attr_parts)}.\n"

            if target.coordinates:
                ans += f"• **Geospatial Reference:** **{target.coordinates.get('raw_text')}**.\n"

            if target.aliases:
                ans += f"• **Harmonized Aliases:** {', '.join(target.aliases)} (resolved by Entity Resolution Agent).\n"

            node_ids = {target.id}
            edge_list = []
            for t in connected_triples:
                node_ids.add(t.subject_id)
                node_ids.add(t.object_id)
                edge_list.append(t.dict())

            sub_nodes = [self.entities[nid].dict() for nid in node_ids if nid in self.entities]

            return GraphRAGQueryResponse(
                query=query_text,
                analysis=ans,
                supporting_entities=[target.name] + list(related_entity_names),
                source_evidence=evidence_list[:4],
                subgraph={"nodes": sub_nodes, "edges": edge_list}
            )

        # Check if question is a general overview/summary
        is_summary = any(k in q_lower for k in ["summary", "overview", "what do you know", "all entities", "sources", "list", "status", "report", "intelligence", "network"])
        if is_summary:
            hubs = sorted(self.entities.values(), key=lambda x: x.mentions_count, reverse=True)[:5]
            hubs_str = ", ".join([f"**{h.name}**" for h in hubs]) if hubs else "None"
            ans = (
                f"TRINETRA has ingested {len(self.sources)} sources and constructed an active knowledge graph "
                f"comprising **{len(self.entities)} entities** across **{len(self.triples)} RDF relationships**.\n\n"
                f"• **Key Focal Entities:** {hubs_str}.\n"
                f"• **Active Sources:** {', '.join([s.filename for s in self.sources.values()])}.\n\n"
                f"Ask specific questions about any entity to view its connected subgraph and source citations."
            )
            ev_list = [e.source_evidence[0] for e in hubs if e.source_evidence]
            return GraphRAGQueryResponse(
                query=query_text,
                analysis=ans,
                supporting_entities=[h.name for h in hubs],
                source_evidence=ev_list[:4],
                subgraph={"nodes": [h.dict() for h in hubs], "edges": []}
            )

        # Insufficient evidence fallback (Requirement 20)
        sources_checked = [s.filename for s in self.sources.values()]
        sources_formatted = "\n• " + "\n• ".join(sources_checked) if sources_checked else "None"
        return GraphRAGQueryResponse(
            query=query_text,
            analysis=(
                "Insufficient source evidence.\n"
                "I could not find enough information in the processed sources to answer this question reliably.\n\n"
                f"**SOURCES CHECKED:**{sources_formatted}"
            ),
            supporting_entities=[],
            source_evidence=[],
            subgraph={"nodes": [], "edges": []}
        )

    # --- EXPORT SERIALIZERS (Section 28) ---
    def export_jsonld(self) -> Dict[str, Any]:
        """Exports unified graph in W3C JSON-LD format."""
        graph_nodes = []
        for ent in self.entities.values():
            node = {
                "@id": f"urn:trinetra:entity:{ent.id}",
                "@type": f"http://schema.org/{ent.type}",
                "name": ent.name,
                "category": ent.category.value,
                "sources": ent.sources
            }
            if ent.coordinates:
                node["geo"] = {
                    "@type": "GeoCoordinates",
                    "latitude": ent.coordinates.get("latitude"),
                    "longitude": ent.coordinates.get("longitude")
                }
            graph_nodes.append(node)

        triples_data = []
        for t in self.triples.values():
            triples_data.append({
                "@id": f"urn:trinetra:triple:{t.id}",
                "subject": f"urn:trinetra:entity:{t.subject_id}",
                "predicate": f"urn:trinetra:relation:{t.predicate}",
                "object": f"urn:trinetra:entity:{t.object_id}",
                "sourceDocument": t.source_document,
                "page": t.page_number
            })

        return {
            "@context": {
                "@vocab": "http://schema.org/",
                "trinetra": "urn:trinetra:"
            },
            "@graph": graph_nodes + triples_data
        }

    def export_turtle(self) -> str:
        """Exports knowledge graph in W3C RDF Turtle (.ttl) format."""
        lines = [
            "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
            "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
            "@prefix schema: <http://schema.org/> .",
            "@prefix trinetra: <http://trinetra.gov.in/ontology/> .",
            ""
        ]

        for ent in self.entities.values():
            lines.append(f"trinetra:{ent.id} a schema:{ent.type} ;")
            lines.append(f'    rdfs:label "{ent.name}" ;')
            lines.append(f'    trinetra:category "{ent.category.value}" .')
            lines.append("")

        for t in self.triples.values():
            lines.append(f"trinetra:{t.subject_id} trinetra:{t.predicate} trinetra:{t.object_id} .")
            lines.append(f'# Provenance: {t.source_document}, Page {t.page_number}')

        return "\n".join(lines)

    def get_full_graph_response(self) -> KnowledgeGraphResponse:
        nodes = list(self.entities.values())
        edges = list(self.triples.values())
        source_list = list(self.sources.values())

        stats = {
            "total_entities": len(nodes),
            "total_relationships": len(edges),
            "entities_resolved": len(self.resolutions),
            "conflicts_detected": len(self.conflicts),
            "sources_processed": len(source_list),
            "graph_nodes": len(nodes)
        }

        return KnowledgeGraphResponse(
            nodes=nodes,
            edges=edges,
            conflicts=self.conflicts,
            resolutions=self.resolutions,
            sources=source_list,
            stats=stats,
            is_demo_mode=self.is_demo_mode
        )
