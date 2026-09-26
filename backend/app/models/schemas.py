from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum
import uuid

class EntityCategory(str, Enum):
    PEOPLE = "People"
    ORGANIZATIONS = "Organizations"
    LOCATIONS = "Locations"
    EVENTS = "Events"
    EQUIPMENT = "Equipment"

class SourceModality(str, Enum):
    TEXT_REPORT = "TEXT_REPORT"
    MAP_IMAGE = "MAP_IMAGE"
    EMBEDDED_IMAGE = "EMBEDDED_IMAGE"
    STANDALONE_IMAGE = "STANDALONE_IMAGE"
    IMAGE_FIGURE = "IMAGE_FIGURE"
    REPORT_IMAGE_FUSION = "REPORT_IMAGE_FUSION"

class SourceEvidence(BaseModel):
    document_id: str
    document_name: str
    page_number: int = 1
    snippet: str
    modality: SourceModality = SourceModality.TEXT_REPORT
    confidence: float = 0.95
    extraction_type: str = "TEXT_NER"
    crop_bbox: Optional[List[float]] = None

class Entity(BaseModel):
    id: str
    name: str
    type: str  # People, Organizations, Locations, Events, Equipment
    category: EntityCategory
    aliases: List[str] = Field(default_factory=list)
    mentions_count: int = 1
    sources: List[str] = Field(default_factory=list)
    source_evidence: List[SourceEvidence] = Field(default_factory=list)
    coordinates: Optional[Dict[str, Any]] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
    has_conflict: bool = False
    conflict_ids: List[str] = Field(default_factory=list)
    resolved_from: List[str] = Field(default_factory=list)

class RDFTriple(BaseModel):
    id: str = Field(default_factory=lambda: f"trip_{uuid.uuid4().hex[:8]}")
    subject_id: str
    subject_name: str
    predicate: str  # e.g. OPERATES_IN, HAS_FACILITY, ASSOCIATED_WITH, COMMANDS, DEPLOYED_TO
    object_id: str
    object_name: str
    provenance: SourceModality = SourceModality.TEXT_REPORT
    source_document: str
    page_number: int = 1
    evidence_text: str
    confidence: float = 0.95

class EntityResolutionRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"res_{uuid.uuid4().hex[:8]}")
    canonical_name: str
    entity_type: str
    matched_variants: List[str] = Field(default_factory=list)
    variants: Optional[List[str]] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    supporting_sources: Optional[List[str]] = Field(default_factory=list)
    confidence: float = 0.94
    resolution_rationale: str = ""
    evidence_snippets: Optional[List[str]] = Field(default_factory=list)
    status: str = "RESOLVED"

    def model_post_init(self, __context: Any) -> None:
        if self.variants and not self.matched_variants:
            self.matched_variants = self.variants
        if self.supporting_sources and not self.sources:
            self.sources = self.supporting_sources
        if self.evidence_snippets and not self.resolution_rationale:
            self.resolution_rationale = "; ".join(self.evidence_snippets)

class ConflictRecord(BaseModel):
    id: str = Field(default_factory=lambda: f"conf_{uuid.uuid4().hex[:8]}")
    entity_name: str
    conflict_attribute: str
    description: str
    source_a: Dict[str, Any]
    source_b: Dict[str, Any]
    status: str = "CONFLICTING INFORMATION"
    severity: str = "HIGH"

class PipelineStage(BaseModel):
    stage_number: int
    name: str
    status: str  # Complete, Processing, Pending
    details: str

class AgentModuleStatus(BaseModel):
    name: str
    status: str = "ONLINE"
    description: str

class SourceDocumentMeta(BaseModel):
    id: str
    filename: str
    file_type: str  # PDF, DOCX, TXT, IMAGE
    status: str = "Processed"  # Uploaded, Processing, Processed, Conflict, Error
    entity_count: int = 0
    relationship_count: int = 0
    conflict_count: int = 0
    page_count: int = 1
    processed_time: str = "Just now"
    summary: str = ""
    raw_text: str = ""
    extracted_entities: List[str] = Field(default_factory=list)
    extracted_relationships: List[str] = Field(default_factory=list)
    source_evidence_list: List[Dict[str, Any]] = Field(default_factory=list)

class GraphRAGQueryRequest(BaseModel):
    query: str

class GraphRAGQueryResponse(BaseModel):
    query: str
    analysis: str
    supporting_entities: List[str]
    source_evidence: List[SourceEvidence]
    subgraph: Dict[str, Any]

class KnowledgeGraphResponse(BaseModel):
    nodes: List[Entity]
    edges: List[RDFTriple]
    conflicts: List[ConflictRecord]
    resolutions: List[EntityResolutionRecord]
    sources: List[SourceDocumentMeta]
    stats: Dict[str, int]
    is_demo_mode: bool = False
