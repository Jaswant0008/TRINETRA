import json
import shutil
from pathlib import Path
from typing import Dict, Any
from app.config import UPLOADS_DIR, EXTRACTED_IMAGES_DIR
from app.models.schemas import SourceDocumentMeta, EntityCategory, SourceModality, EntityResolutionRecord
from app.services.graph_service import GraphService

class DemoScenarioLoader:
    """Loads the official fictional defense demonstration scenario conforming to PS-05."""

    @classmethod
    def load_demo(cls, graph_service: GraphService):
        graph_service.clear()
        graph_service.is_demo_mode = True

        demo_reports_dir = Path(__file__).resolve().parent.parent.parent / "data" / "demo" / "dummy_reports"
        
        # Copy demo files into uploads dir if available
        for f in ["Report_01_Reconnaissance.pdf", "Report_02_SIGINT_Intercept.pdf", "Report_03_Field_Incident.pdf", "Report_04_Tactical_Overhead_Scan.png"]:
            src = demo_reports_dir / f
            dst = UPLOADS_DIR / f
            if src.exists():
                try:
                    shutil.copy(str(src), str(dst))
                except Exception:
                    pass

        # Step 1: Register 3 Fictional PDF Reports + 1 Multimodal Scan
        reports_meta = [
            SourceDocumentMeta(
                id="doc_rep_01",
                filename="Report_01_Reconnaissance.pdf",
                file_type="PDF",
                status="Processed",
                entity_count=4,
                relationship_count=3,
                processed_time="2026-09-26 10:15",
                summary="Forward reconnaissance observations across Sector Alpha. Identifies Enemy Vehicle A equipped with Weapon X (Status: Active). Observer: Captain A. Sharma."
            ),
            SourceDocumentMeta(
                id="doc_rep_02",
                filename="Report_02_SIGINT_Intercept.pdf",
                file_type="PDF",
                status="Processed",
                entity_count=4,
                relationship_count=2,
                processed_time="2026-09-26 10:22",
                summary="Electronic signal intelligence intercept within Sector-A. Telemetry links Enemy Vehicle A to Unit Alpha command contingent. Analyst: A. Sharma."
            ),
            SourceDocumentMeta(
                id="doc_rep_03",
                filename="Report_03_Field_Incident.pdf",
                file_type="PDF",
                status="Conflict",
                entity_count=3,
                relationship_count=2,
                processed_time="2026-09-26 10:30",
                summary="After-action tactical incident report regarding Incident Y involving Unit Alpha. Follow-up damage logs Enemy Vehicle A as Inactive (Conflicting with Report 01). Debrief: Captain Sharma."
            ),
            SourceDocumentMeta(
                id="doc_rep_04",
                filename="Report_04_Tactical_Overhead_Scan.png",
                file_type="IMAGE",
                status="Analyzed",
                entity_count=3,
                relationship_count=2,
                processed_time="2026-09-26 10:35",
                summary="Tactical multimodal overhead scan. Optical telemetry corroborates spatial bounds of Sector Alpha, Enemy Vehicle A, Weapon X, and Unit Alpha."
            )
        ]

        for s in reports_meta:
            graph_service.sources[s.id] = s

        # Step 2: Populate Core Entities conforming to Section 7 & 8
        
        # 1. Equipment: Enemy Vehicle A (The central common entity)
        veh_a = graph_service.add_or_update_entity(
            raw_name="Enemy Vehicle A",
            etype="Equipment",
            doc_name="Report_01_Reconnaissance.pdf",
            page_num=2,
            evidence_snippet="Optical sensor logs verify that Enemy Vehicle A maintains full mobility and is actively equipped with Weapon X.",
            attributes={"status": "Active (Report 01) / Inactive (Report 03)", "classification": "Armoured Recon Platform"}
        )
        # Register Vehicle A in Report 02 & Report 03
        graph_service.add_or_update_entity(
            raw_name="Enemy Vehicle A",
            etype="Equipment",
            doc_name="Report_02_SIGINT_Intercept.pdf",
            page_num=1,
            evidence_snippet="Signals analysis indicates Enemy Vehicle A is linked to Unit Alpha via encrypted telemetry."
        )
        graph_service.add_or_update_entity(
            raw_name="Enemy Vehicle A",
            etype="Equipment",
            doc_name="Report_03_Field_Incident.pdf",
            page_num=1,
            evidence_snippet="Follow-up damage assessment indicates Enemy Vehicle A status: Inactive following electrical fire."
        )
        graph_service.add_or_update_entity(
            raw_name="Enemy Vehicle A",
            etype="Equipment",
            doc_name="Report_04_Tactical_Overhead_Scan.png",
            page_num=1,
            evidence_snippet="Multimodal scan figure 1 identifies Enemy Vehicle A bearing 042 deg North.",
            modality=SourceModality.IMAGE_FIGURE
        )

        # 2. Equipment: Weapon X
        wep_x = graph_service.add_or_update_entity(
            raw_name="Weapon X",
            etype="Equipment",
            doc_name="Report_01_Reconnaissance.pdf",
            page_num=1,
            evidence_snippet="Enemy Vehicle A is actively equipped with Weapon X (Heavy Multi-Spectrum Targeting System).",
            attributes={"type": "Multi-Spectrum Targeting Armament"}
        )
        graph_service.add_or_update_entity(
            raw_name="Weapon X",
            etype="Equipment",
            doc_name="Report_04_Tactical_Overhead_Scan.png",
            page_num=1,
            evidence_snippet="Weapon X interlink mounted on forward turret of Vehicle A.",
            modality=SourceModality.IMAGE_FIGURE
        )

        # 3. Organization: Unit Alpha
        unit_alpha = graph_service.add_or_update_entity(
            raw_name="Unit Alpha",
            etype="Organizations",
            doc_name="Report_02_SIGINT_Intercept.pdf",
            page_num=1,
            evidence_snippet="Radio telemetry and transponders indicate Enemy Vehicle A is directly linked to Unit Alpha (Command Contingent).",
            attributes={"role": "Command Battalion", "echelon": "Tactical Headquarters"}
        )
        graph_service.add_or_update_entity(
            raw_name="Unit Alpha",
            etype="Organizations",
            doc_name="Report_03_Field_Incident.pdf",
            page_num=1,
            evidence_snippet="Unit Alpha was explicitly mentioned in Incident Y during northern sector redeployment."
        )
        graph_service.add_or_update_entity(
            raw_name="Unit Alpha",
            etype="Organizations",
            doc_name="Report_04_Tactical_Overhead_Scan.png",
            page_num=1,
            evidence_snippet="Unit Alpha perimeter command station identified inside Sector Alpha.",
            modality=SourceModality.IMAGE_FIGURE
        )

        # 4. Event: Incident Y
        inc_y = graph_service.add_or_update_entity(
            raw_name="Incident Y",
            etype="Events",
            doc_name="Report_03_Field_Incident.pdf",
            page_num=1,
            evidence_snippet="Debriefing regarding Incident Y (Perimeter Skirmish Event) involving forward elements.",
            attributes={"classification": "Perimeter Engagement Event", "phase": "After-Action Review"}
        )

        # 5. Location: Sector Alpha (with variant Sector-A)
        sec_alpha = graph_service.add_or_update_entity(
            raw_name="Sector Alpha",
            etype="Locations",
            doc_name="Report_01_Reconnaissance.pdf",
            page_num=1,
            evidence_snippet="Forward reconnaissance patrol identified tactical movements across Sector Alpha northern boundary.",
            coordinates={"raw_text": "GRID-A17 / Sector Alpha", "zone": "Training Sector Alpha"}
        )
        graph_service.add_or_update_entity(
            raw_name="Sector-A",
            etype="Locations",
            doc_name="Report_02_SIGINT_Intercept.pdf",
            page_num=2,
            evidence_snippet="Unit Alpha has established a tactical command node inside Sector-A."
        )

        # 6. People: Captain A. Sharma (with variants A. Sharma, Captain Sharma)
        capt_sharma = graph_service.add_or_update_entity(
            raw_name="Captain A. Sharma",
            etype="People",
            doc_name="Report_01_Reconnaissance.pdf",
            page_num=2,
            evidence_snippet="Optical reconnaissance patrol led and verified on ground by Captain A. Sharma.",
            attributes={"rank": "Captain", "unit": "Forward Reconnaissance Detachment"}
        )
        # Register variant A. Sharma
        graph_service.add_or_update_entity(
            raw_name="A. Sharma",
            etype="People",
            doc_name="Report_02_SIGINT_Intercept.pdf",
            page_num=1,
            evidence_snippet="SIGINT intercept analysis conducted by A. Sharma, Electronic Warfare Unit."
        )
        # Register variant Captain Sharma
        graph_service.add_or_update_entity(
            raw_name="Captain Sharma",
            etype="People",
            doc_name="Report_03_Field_Incident.pdf",
            page_num=1,
            evidence_snippet="Debrief conducted by Captain Sharma, Tactical Operations Liaison."
        )

        # Step 3: Triples & Relationship Links (Information Fusion)
        # Vehicle A -> EQUIPPED_WITH -> Weapon X
        graph_service.add_triple(
            subj_name="Enemy Vehicle A",
            subj_type="Equipment",
            predicate="EQUIPPED_WITH",
            obj_name="Weapon X",
            obj_type="Equipment",
            doc_name="Report_01_Reconnaissance.pdf",
            page_num=2,
            evidence_text="Enemy Vehicle A is actively equipped with Weapon X (Heavy Multi-Spectrum Targeting System)."
        )

        # Vehicle A -> LINKED_TO -> Unit Alpha
        graph_service.add_triple(
            subj_name="Enemy Vehicle A",
            subj_type="Equipment",
            predicate="LINKED_TO",
            obj_name="Unit Alpha",
            obj_type="Organizations",
            doc_name="Report_02_SIGINT_Intercept.pdf",
            page_num=1,
            evidence_text="Radio telemetry and transponder logs confirm Enemy Vehicle A is linked to Unit Alpha."
        )

        # Unit Alpha -> MENTIONED_IN -> Incident Y
        graph_service.add_triple(
            subj_name="Unit Alpha",
            subj_type="Organizations",
            predicate="MENTIONED_IN",
            obj_name="Incident Y",
            obj_type="Events",
            doc_name="Report_03_Field_Incident.pdf",
            page_num=1,
            evidence_text="Unit Alpha was explicitly mentioned in Incident Y during northern sector redeployment."
        )

        # Vehicle A -> OPERATING_IN -> Sector Alpha
        graph_service.add_triple(
            subj_name="Enemy Vehicle A",
            subj_type="Equipment",
            predicate="OPERATING_IN",
            obj_name="Sector Alpha",
            obj_type="Locations",
            doc_name="Report_01_Reconnaissance.pdf",
            page_num=1,
            evidence_text="Enemy Vehicle A observed operating within Sector Alpha northern boundary."
        )

        # Captain A. Sharma -> OBSERVED -> Enemy Vehicle A
        graph_service.add_triple(
            subj_name="Captain A. Sharma",
            subj_type="People",
            predicate="OBSERVED",
            obj_name="Enemy Vehicle A",
            obj_type="Equipment",
            doc_name="Report_01_Reconnaissance.pdf",
            page_num=1,
            evidence_text="Ground sighting of Enemy Vehicle A confirmed and catalogued by Captain A. Sharma."
        )

        # Unit Alpha -> LOCATED_IN -> Sector Alpha
        graph_service.add_triple(
            subj_name="Unit Alpha",
            subj_type="Organizations",
            predicate="LOCATED_IN",
            obj_name="Sector Alpha",
            obj_type="Locations",
            doc_name="Report_02_SIGINT_Intercept.pdf",
            page_num=2,
            evidence_text="Unit Alpha established tactical communications command post inside Sector-A / Sector Alpha."
        )

        # Step 4: Record Entity Resolutions (Section 8)
        graph_service.resolutions = [
            EntityResolutionRecord(
                canonical_name="Captain A. Sharma",
                entity_type="People",
                variants=["A. Sharma", "Captain Sharma"],
                confidence=0.89,
                supporting_sources=[
                    "Report_01_Reconnaissance.pdf",
                    "Report_02_SIGINT_Intercept.pdf",
                    "Report_03_Field_Incident.pdf"
                ],
                evidence_snippets=[
                    "Report 01 (p.2): Field reconnaissance led on ground by Captain A. Sharma.",
                    "Report 02 (p.1): SIGINT intercept analysis conducted by A. Sharma.",
                    "Report 03 (p.1): Tactical operations debrief conducted by Captain Sharma."
                ],
                status="POTENTIAL SAME ENTITY"
            ),
            EntityResolutionRecord(
                canonical_name="Sector Alpha",
                entity_type="Locations",
                variants=["Sector-A"],
                confidence=0.96,
                supporting_sources=[
                    "Report_01_Reconnaissance.pdf",
                    "Report_02_SIGINT_Intercept.pdf",
                    "Report_04_Tactical_Overhead_Scan.png"
                ],
                evidence_snippets=[
                    "Report 01 (p.1): Sector Alpha perimeter corridor surveillance.",
                    "Report 02 (p.2): Command node established inside Sector-A.",
                    "Report 04 (Scan): Sector Alpha grid-A17 perimeter boundary."
                ],
                status="RESOLVED DUPLICATE"
            )
        ]

        # Step 5: Record Conflict (Section 13)
        graph_service.add_conflict(
            entity_name="Enemy Vehicle A",
            attribute="Operational Status",
            source_a={
                "document": "Report_01_Reconnaissance.pdf",
                "page": 2,
                "value": "Status = Active",
                "extract": "Optical sensor logs verify that Enemy Vehicle A maintains full mobility and is actively operational."
            },
            source_b={
                "document": "Report_03_Field_Incident.pdf",
                "page": 1,
                "value": "Status = Inactive",
                "extract": "Follow-up damage assessment logs Enemy Vehicle A status as Inactive following electrical fire."
            },
            description="Operational status discrepancy: Report 01 logs Enemy Vehicle A as Active, whereas Report 03 reports it as Inactive."
        )
