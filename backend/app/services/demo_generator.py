import os
import json
import pymupdf
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image, ImageDraw, ImageFont
from app.config import DEMO_DIR, EXTRACTED_IMAGES_DIR, UPLOADS_DIR

class DemoGenerator:
    """Generates authentic tactical military reports and maps conforming to Section 9 specifications."""

    @classmethod
    def create_tactical_map_image(cls, output_path: Path, title: str, coord_str: str, conflict: bool = False) -> Dict:
        """Draws a tactical command map with grids, coordinates, sectors, and facilities."""
        width, height = 900, 600
        img = Image.new("RGB", (width, height), color=(11, 20, 29))
        draw = ImageDraw.Draw(img)

        # Draw military grid lines
        grid_color = (25, 45, 60)
        grid_highlight = (35, 65, 85)
        for x in range(0, width, 50):
            color = grid_highlight if x % 150 == 0 else grid_color
            draw.line([(x, 0), (x, height)], fill=color, width=1)
        for y in range(0, height, 50):
            color = grid_highlight if y % 150 == 0 else grid_color
            draw.line([(0, y), (width, y)], fill=color, width=1)

        # Tactical HUD border & coordinate labels on edge
        draw.rectangle([(15, 15), (width-15, height-15)], outline=(0, 229, 255), width=2)
        draw.text((25, 22), f"TRINETRA TACTICAL MAP // {title.upper()}", fill=(0, 229, 255))
        draw.text((width-220, 22), "TOP SECRET // GEOINT", fill=(255, 75, 75))

        # Compass & Grid Ref
        draw.text((25, height-40), "MGRS: 43S DU 84920 68120", fill=(140, 175, 195))
        draw.text((width-200, height-40), "NORTH ^  SCALE: 1:25,000", fill=(140, 175, 195))

        # Sector Alpha Boundary / Zone
        if not conflict:
            sector_bbox = (150, 160, 420, 400)
            draw.rectangle(sector_bbox, outline=(255, 183, 3), width=2)
            draw.text((165, 175), "ZONE: SECTOR ALPHA", fill=(255, 183, 3))
            draw.text((165, 205), f"COORD: {coord_str}", fill=(0, 255, 170))

            # Checkpoint Alpha
            draw.ellipse((200, 310, 220, 330), fill=(0, 229, 255), outline=(255, 255, 255))
            draw.text((230, 312), "Checkpoint Alpha", fill=(200, 235, 255))

            # Factory Bravo
            factory_bbox = (560, 220, 780, 380)
            draw.rectangle(factory_bbox, outline=(255, 90, 95), fill=(20, 35, 45), width=2)
            draw.text((580, 235), "FACILITY: FACTORY BRAVO", fill=(255, 90, 95))
            draw.text((580, 265), "Industrial Compound // Associated Facility", fill=(180, 200, 215))
            draw.text((580, 295), "Type: Manufacturing / Storage", fill=(140, 175, 195))

            # Route line between Sector Alpha and Factory Bravo
            draw.line([(380, 280), (560, 280)], fill=(255, 255, 0), width=3)
            draw.text((420, 255), "Route 9 [2.4 km]", fill=(255, 255, 0))

            metadata = {
                "image_type": "TACTICAL_MAP",
                "coordinates": [
                    {"raw_text": coord_str, "latitude": 34.0522, "longitude": 74.8321, "associated_label": "Sector Alpha", "bbox": [0.26, 0.16, 0.40, 0.46]}
                ],
                "labels": [
                    {"text": "Sector Alpha", "type": "SECTOR", "bbox": [0.25, 0.16, 0.35, 0.46]},
                    {"text": "Factory Bravo", "type": "FACILITY", "bbox": [0.36, 0.62, 0.63, 0.86]},
                    {"text": "Checkpoint Alpha", "type": "CHECKPOINT", "bbox": [0.51, 0.22, 0.55, 0.36]},
                    {"text": "2.4 km", "type": "DISTANCE", "bbox": [0.42, 0.46, 0.47, 0.58]}
                ],
                "relationships": [
                    {"source": "Sector Alpha", "target": "Factory Bravo", "type": "NEARBY_FACILITY", "evidence": "Direct route connecting Sector Alpha with Factory Bravo (2.4 km) on map"}
                ]
            }
        else:
            # Conflicting map for Report 2
            sector_bbox = (480, 100, 750, 320)
            draw.rectangle(sector_bbox, outline=(255, 50, 80), width=2)
            draw.text((495, 115), "ZONE: SECTOR ALPHA (SIGINT FIX)", fill=(255, 50, 80))
            draw.text((495, 145), f"COORD: {coord_str}", fill=(255, 100, 100))
            draw.text((495, 175), "[DISCREPANCY ALERT: 11.2 KM OFFSET]", fill=(255, 200, 0))

            metadata = {
                "image_type": "TACTICAL_MAP_CONFLICT",
                "coordinates": [
                    {"raw_text": coord_str, "latitude": 34.1205, "longitude": 74.9100, "associated_label": "Sector Alpha", "bbox": [0.16, 0.53, 0.35, 0.83]}
                ],
                "labels": [
                    {"text": "Sector Alpha", "type": "SECTOR", "bbox": [0.16, 0.53, 0.35, 0.83]}
                ],
                "relationships": []
            }

        img.save(output_path, quality=95)
        # Save sidecar JSON metadata
        sidecar = output_path.with_suffix(".json")
        with open(sidecar, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return metadata

    @classmethod
    def generate_all_demo_reports(cls):
        """Builds Report_01, Report_02, and Report_03 with embedded maps complying with Section 9."""
        cls.generate_report_1()
        cls.generate_report_2()
        cls.generate_report_3()

    @classmethod
    def generate_report_1(cls):
        pdf_path = UPLOADS_DIR / "Report_01_Forward_Recon.pdf"
        map_img_path = EXTRACTED_IMAGES_DIR / "map_sector_alpha_recon.png"

        cls.create_tactical_map_image(
            map_img_path,
            title="Sector Alpha Forward Tactical Map",
            coord_str="34.0522° N, 74.8321° E",
            conflict=False
        )

        doc = pymupdf.open()

        # Page 1: Overview
        page1 = doc.new_page(width=595, height=842)
        p1_text = """INTELLIGENCE REPORT: TRINETRA-IR-2026-001
CLASSIFICATION: RESTRICTED // OPERATION TRISHUL
SUBJECT: Forward Reconnaissance & Observation Briefing

1. EXECUTIVE SUMMARY
Forward surveillance units deployed across northern borders initiated tactical observation.
Observation Activity designated as Event A was registered during the 0400 hours patrol window.
Preliminary telemetry indicates ground movement and infrastructure verification.

2. MISSION OBJECTIVES
- Establish optical observation of Sector Alpha perimeter.
- Correlate known industrial compounds and supply routes.
- Verify reported coordinates against satellite and drone map feeds.
"""
        page1.insert_text((50, 60), p1_text, fontsize=11, fontname="helv")

        # Page 2: Co-referenced Text + Embedded Tactical Map (Directly implements Section 9.C & 9.D)
        page2 = doc.new_page(width=595, height=842)
        p2_text = """INTELLIGENCE REPORT: TRINETRA-IR-2026-001 (PAGE 2)

3. FIELD OBSERVATIONS & TACTICAL CO-REFERENCING

An observation was reported near Sector Alpha.

Activity was registered along the northern access corridor. The reconnaissance unit captured
the attached high-resolution tactical grid map (Figure 1.1) displaying Sector Alpha,
the primary access coordinates, and nearby facilities including Factory Bravo.
"""
        page2.insert_text((50, 60), p2_text, fontsize=11, fontname="helv")

        # Insert map image into page 2
        img_rect = pymupdf.Rect(50, 180, 545, 500)
        page2.insert_image(img_rect, filename=str(map_img_path))

        p2_footer = """Figure 1.1: Tactical Reconnaissance Map — Sector Alpha and Adjacent Infrastructure.
Note: Coordinate 34.0522° N, 74.8321° E confirmed by forward survey.
Nearby facility Factory Bravo located 2.4 km along Route 9."""
        page2.insert_text((50, 520), p2_footer, fontsize=10, fontname="helv")

        doc.save(pdf_path)
        doc.close()

    @classmethod
    def generate_report_2(cls):
        """Generates Report 2 with conflicting coordinate to demonstrate Section 9.E Conflict Flagging!"""
        pdf_path = UPLOADS_DIR / "Report_02_SIGINT_Conflict.pdf"
        map_img_path = EXTRACTED_IMAGES_DIR / "map_sector_alpha_sigint_conflict.png"

        cls.create_tactical_map_image(
            map_img_path,
            title="SIGINT Triangulation - Sector Alpha",
            coord_str="34.1205° N, 74.9100° E",
            conflict=True
        )

        doc = pymupdf.open()
        page = doc.new_page(width=595, height=842)
        text = """INTELLIGENCE REPORT: TRINETRA-IR-2026-002
CLASSIFICATION: TOP SECRET // SIGNALS INTELLIGENCE
SUBJECT: Electronic Surveillance & Sector Alpha Location Intercept

1. SIGNALS INTERCEPT SUMMARY
Direction-finding antenna array captured RF emissions originating from hostile command node.
Intercept data claims headquarters for Sector Alpha is established at coordinate:
Latitude: 34.1205° N, Longitude: 74.9100° E.

2. GEOSPATIAL CONFLICT NOTICE
This coordinate diverges by approximately 11.2 kilometers from the visual reconnaissance map
provided in Report_01_Forward_Recon.pdf (34.0522° N, 74.8321° E).
TRINETRA Conflict Management engine is required to flag this coordinate mismatch.
"""
        page.insert_text((50, 60), text, fontsize=11, fontname="helv")
        img_rect = pymupdf.Rect(50, 240, 545, 560)
        page.insert_image(img_rect, filename=str(map_img_path))

        doc.save(pdf_path)
        doc.close()

    @classmethod
    def generate_report_3(cls):
        """Generates Report 3 with satellite airfield & logistical facilities."""
        pdf_path = UPLOADS_DIR / "Report_03_Satellite_Surveillance.pdf"
        map_img_path = EXTRACTED_IMAGES_DIR / "map_satellite_airfield.png"

        # Create Satellite diagram
        width, height = 900, 600
        img = Image.new("RGB", (width, height), color=(15, 25, 20))
        draw = ImageDraw.Draw(img)

        # Draw satellite overlay elements
        for i in range(0, width, 40):
            draw.line([(i, 0), (i, height)], fill=(25, 45, 35), width=1)
        for j in range(0, height, 40):
            draw.line([(0, j), (width, j)], fill=(25, 45, 35), width=1)

        draw.rectangle([(15, 15), (width-15, height-15)], outline=(0, 255, 150), width=2)
        draw.text((25, 25), "GEO-SAT ORBITAL IMAGERY // SECTOR BRAVO", fill=(0, 255, 150))
        draw.text((width-240, 25), "RESOLUTION: 0.5M // SATELLITE", fill=(150, 220, 180))

        # Airfield runway
        draw.rectangle([(200, 250), (700, 310)], fill=(40, 55, 50), outline=(0, 255, 150), width=2)
        draw.line([(220, 280), (680, 280)], fill=(255, 255, 255), width=2)
        draw.text((380, 260), "RUNWAY 09/27 - FORWARD AIRFIELD", fill=(255, 255, 255))

        # Supply Depot 4
        draw.rectangle([(120, 120), (280, 210)], outline=(255, 180, 0), fill=(30, 45, 35), width=2)
        draw.text((130, 130), "SUPPLY DEPOT 4", fill=(255, 180, 0))

        # Radar Station Omega
        draw.ellipse([(650, 100), (750, 200)], outline=(0, 229, 255), fill=(20, 40, 45), width=2)
        draw.text((640, 210), "RADAR STATION OMEGA", fill=(0, 229, 255))

        draw.text((25, height-35), "COORD: 34.0811° N, 74.8912° E // SECTOR BRAVO", fill=(0, 255, 150))

        img.save(map_img_path, quality=95)

        meta = {
            "image_type": "SATELLITE_RECON",
            "coordinates": [
                {"raw_text": "34.0811° N, 74.8912° E", "latitude": 34.0811, "longitude": 74.8912, "associated_label": "Sector Bravo", "bbox": [0.85, 0.05, 0.95, 0.45]}
            ],
            "labels": [
                {"text": "Sector Bravo", "type": "SECTOR", "bbox": [0.85, 0.05, 0.95, 0.45]},
                {"text": "Forward Airfield", "type": "FACILITY", "bbox": [0.41, 0.22, 0.52, 0.78]},
                {"text": "Supply Depot 4", "type": "FACILITY", "bbox": [0.20, 0.13, 0.35, 0.31]},
                {"text": "Radar Station Omega", "type": "FACILITY", "bbox": [0.16, 0.72, 0.35, 0.85]}
            ],
            "relationships": [
                {"source": "Sector Bravo", "target": "Forward Airfield", "type": "LOCATED_IN", "evidence": "Forward Airfield located within Sector Bravo orbital footprint"}
            ]
        }
        with open(map_img_path.with_suffix(".json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        doc = pymupdf.open()
        page = doc.new_page(width=595, height=842)
        text = """INTELLIGENCE REPORT: TRINETRA-IR-2026-003
CLASSIFICATION: SECRET // GEO-SATELLITE SURVEILLANCE
SUBJECT: Sector Bravo Strategic Assets & Infrastructure

1. SATELLITE PASS ANALYSIS
High-resolution satellite imagery captured Sector Bravo complex at 34.0811° N, 74.8912° E.
Imagery reveals active deployment at Forward Airfield with operational Runway 09/27,
logistical storage at Supply Depot 4, and early-warning coverage from Radar Station Omega.
"""
        page.insert_text((50, 60), text, fontsize=11, fontname="helv")
        img_rect = pymupdf.Rect(50, 220, 545, 540)
        page.insert_image(img_rect, filename=str(map_img_path))

        doc.save(pdf_path)
        doc.close()
