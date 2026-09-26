import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel

from app.config import UPLOADS_DIR, EXTRACTED_IMAGES_DIR, settings
from app.models.schemas import (
    KnowledgeGraphResponse, ConflictRecord, Entity, RDFTriple,
    EntityResolutionRecord, SourceDocumentMeta, GraphRAGQueryRequest,
    GraphRAGQueryResponse, PipelineStage, AgentModuleStatus
)
from app.services.graph_service import GraphService
from app.services.document_processor import DocumentProcessor
from app.services.demo_scenario import DemoScenarioLoader

router = APIRouter()

# Global Singleton Knowledge Graph Service
global_graph_service = GraphService()

def init_workspace():
    # Check if user uploaded custom reports exist
    user_files = sorted(list(UPLOADS_DIR.glob("Dummy_Report_*.pdf")))
    if user_files:
        global_graph_service.clear()
        for f in user_files:
            doc_data = DocumentProcessor.process_file(str(f), f.name)
            global_graph_service.ingest_document_data(doc_data)
    else:
        # Start with clean slate (0 sources, 0 fake data) per Requirement 1
        global_graph_service.clear()

init_workspace()

# --- SYSTEM & STATUS ENDPOINTS ---
@router.get("/status")
def get_system_status():
    graph_res = global_graph_service.get_full_graph_response()
    return {
        "status": "OPERATIONAL",
        "system": "TRINETRA Multimodal Intelligence Fusion System",
        "tagline": "From Fragmented Intelligence to Strategic Insight",
        "environment": "SECURE ANALYTICS ENVIRONMENT",
        "version": settings.VERSION,
        "alignment": "PS-05 Decentralized Knowledge Graph Builder Agent",
        "stats": graph_res.stats
    }

@router.get("/pipeline/status", response_model=List[PipelineStage])
def get_pipeline_status():
    """8-stage analysis pipeline conforming to Section 11."""
    return [
        PipelineStage(stage_number=1, name="SOURCE INGESTION", status="Complete", details="Multi-source document parsing (PDF, DOCX, TXT, Imagery)."),
        PipelineStage(stage_number=2, name="DOCUMENT UNDERSTANDING", status="Complete", details="Structural semantic segmentation and OCR extraction."),
        PipelineStage(stage_number=3, name="ENTITY EXTRACTION", status="Complete", details="Named Entity Recognition (People, Org, Locations, Events, Equipment)."),
        PipelineStage(stage_number=4, name="RELATIONSHIP MAPPING", status="Complete", details="RDF-style Subject-Predicate-Object triple extraction."),
        PipelineStage(stage_number=5, name="ENTITY RESOLUTION", status="Complete", details="Duplicate clustering & lexical variant harmonization."),
        PipelineStage(stage_number=6, name="KNOWLEDGE GRAPH BUILD", status="Complete", details="Decentralized network graph synthesis and indexing."),
        PipelineStage(stage_number=7, name="CONFLICT ANALYSIS", status="Complete", details="Cross-source attribute verification and discrepancy flagging."),
        PipelineStage(stage_number=8, name="SOURCE INDEXING", status="Complete", details="Provenance anchoring and citation traceability mapping.")
    ]

@router.get("/agents/status", response_model=List[AgentModuleStatus])
def get_agents_status():
    """Active analysis modules conforming to Section 12."""
    return [
        AgentModuleStatus(name="Document Analyzer", status="ONLINE", description="Parses multimodal reports, extract text layers, and embedded visual figures."),
        AgentModuleStatus(name="Entity & Relation Agent", status="ONLINE", description="Extracts domain entities and formal semantic relationships into RDF triples."),
        AgentModuleStatus(name="Entity Resolution Agent", status="ONLINE", description="Disambiguates aliases and resolves multi-document entity variants."),
        AgentModuleStatus(name="Knowledge Graph Agent", status="ONLINE", description="Maintains directed NetworkX topology with degree centrality & path indices."),
        AgentModuleStatus(name="Conflict Detection Agent", status="ONLINE", description="Audits multi-source factual discrepancies and flags conflicting attributes."),
        AgentModuleStatus(name="Query & Insight Agent", status="ONLINE", description="Executes GraphRAG multi-hop question answering with source citations.")
    ]

# --- DOCUMENT INGESTION (Section 10 & 28) ---
@router.get("/documents", response_model=List[SourceDocumentMeta])
def list_documents():
    return list(global_graph_service.sources.values())

@router.get("/sources/{source_id}", response_model=SourceDocumentMeta)
def get_source_by_id(source_id: str):
    if source_id not in global_graph_service.sources:
        raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found.")
    return global_graph_service.sources[source_id]

@router.delete("/documents/{source_id}")
def delete_document(source_id: str):
    """Deletes a document and prunes associated entities and relationships."""
    global_graph_service.remove_source(source_id)
    return {"message": f"Source '{source_id}' removed and knowledge graph pruned successfully."}

@router.post("/sources/{source_id}/reanalyze")
def reanalyze_source(source_id: str):
    """Re-runs processing on a specific source document."""
    if source_id not in global_graph_service.sources:
        raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found.")
    source_meta = global_graph_service.sources[source_id]
    fname = source_meta.filename
    file_path = UPLOADS_DIR / fname
    if not file_path.exists():
        matches = list(UPLOADS_DIR.glob(f"*{fname}*"))
        if matches:
            file_path = matches[0]
        else:
            raise HTTPException(status_code=404, detail=f"Source file '{fname}' not found on storage disk.")

    global_graph_service.remove_source(source_id)
    doc_data = DocumentProcessor.process_file(str(file_path), fname, doc_id=source_id)
    global_graph_service.ingest_document_data(doc_data)
    updated_meta = global_graph_service.sources.get(source_id)
    return {
        "message": f"Successfully reanalyzed {fname}",
        "source": updated_meta,
        "graph": global_graph_service.get_full_graph_response()
    }

@router.post("/documents/clear")
def clear_all_documents():
    """Wipes all documents and resets to empty knowledge graph."""
    global_graph_service.clear()
    return {"message": "All documents cleared. Workspace reset to clean slate."}

@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Uploads and ingests a document or image with autonomous extraction."""
    file_path = UPLOADS_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    doc_data = DocumentProcessor.process_file(str(file_path), file.filename)
    global_graph_service.ingest_document_data(doc_data)

    source_meta = global_graph_service.sources.get(doc_data["document_id"])
    return {
        "message": f"Successfully ingested {file.filename}",
        "document_id": doc_data["document_id"],
        "file_type": doc_data["file_type"],
        "extracted_entities": source_meta.entity_count if source_meta else 0,
        "extracted_relationships": source_meta.relationship_count if source_meta else 0
    }

@router.post("/documents/reingest-all")
def reingest_all_uploads():
    """Reingests all user uploaded documents in the uploads directory."""
    global_graph_service.clear()
    supported_exts = {".pdf", ".docx", ".doc", ".txt", ".png", ".jpg", ".jpeg"}
    user_files = [f for f in sorted(UPLOADS_DIR.iterdir()) if f.is_file() and f.suffix.lower() in supported_exts]
    for f in user_files:
        try:
            doc_data = DocumentProcessor.process_file(str(f), f.name)
            global_graph_service.ingest_document_data(doc_data)
        except Exception as e:
            logger.error(f"Error ingesting {f.name}: {e}")
    return global_graph_service.get_full_graph_response()

# --- KNOWLEDGE GRAPH & ENTITY APIS (Section 28) ---
@router.get("/graph", response_model=KnowledgeGraphResponse)
def get_knowledge_graph():
    return global_graph_service.get_full_graph_response()

@router.get("/entities", response_model=List[Entity])
def list_entities():
    return list(global_graph_service.entities.values())

@router.get("/entities/{entity_id}", response_model=Entity)
def get_entity_by_id(entity_id: str):
    if entity_id not in global_graph_service.entities:
        raise HTTPException(status_code=404, detail=f"Entity '{entity_id}' not found.")
    return global_graph_service.entities[entity_id]

@router.get("/relationships", response_model=List[RDFTriple])
@router.get("/triples", response_model=List[RDFTriple])
def list_triples():
    return list(global_graph_service.triples.values())

@router.get("/resolutions", response_model=List[EntityResolutionRecord])
def list_resolutions():
    return global_graph_service.resolutions

@router.get("/conflicts", response_model=List[ConflictRecord])
def list_conflicts():
    return global_graph_service.conflicts

# --- GRAPHRAG NATURAL LANGUAGE QUERY (Section 18 & 19) ---
@router.post("/query", response_model=GraphRAGQueryResponse)
def query_graph_rag(req: GraphRAGQueryRequest):
    return global_graph_service.answer_query(req.query)

# --- 1-CLICK DEMO LOADER (Section 26 & 29) ---
@router.post("/demo/load")
def reload_demo_data():
    DemoScenarioLoader.load_demo(global_graph_service)
    return global_graph_service.get_full_graph_response()

# --- RDF / JSON-LD / TURTLE EXPORT (Section 28) ---
@router.get("/export/jsonld")
def export_json_ld():
    data = global_graph_service.export_jsonld()
    return JSONResponse(content=data, media_type="application/ld+json")

@router.get("/export/turtle")
def export_turtle():
    ttl_str = global_graph_service.export_turtle()
    return PlainTextResponse(content=ttl_str, media_type="text/turtle")
