"""
Generates 3 synthetic PDF reports and 1 multimodal image conforming exactly to the user prompt:
- Report 01: Enemy Vehicle A equipped with Weapon X, Status Active, Captain A. Sharma
- Report 02: Enemy Vehicle A linked to Unit Alpha, A. Sharma
- Report 03: Unit Alpha mentioned in Incident Y, Enemy Vehicle A Status Inactive (Conflict!), Captain Sharma
- Multimodal Report 04: Scanned tactical diagram
"""
import os
from pathlib import Path
import pymupdf
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEMO_DIR = BASE_DIR / "data" / "demo" / "dummy_reports"
EXTRACTED_DIR = BASE_DIR / "data" / "extracted_images"
DEMO_DIR.mkdir(parents=True, exist_ok=True)
EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

def generate_pdf(filename: str, title: str, pages_data: list):
    pdf_path = DEMO_DIR / filename
    doc = pymupdf.open()
    
    for page_idx, page_info in enumerate(pages_data):
        page = doc.new_page(width=595, height=842) # A4
        # Draw header banner
        rect_header = pymupdf.Rect(40, 35, 555, 75)
        page.draw_rect(rect_header, color=(0.1, 0.15, 0.12), fill=(0.06, 0.09, 0.08))
        
        # Header text
        page.insert_text((55, 55), "TRINETRA // DEFENCE INTELLIGENCE FUSION (PS-05)", fontsize=10, color=(0.5, 0.7, 0.5))
        page.insert_text((55, 68), "SYNTHETIC DEMONSTRATION DATASET — FICTIONAL MILITARY SCENARIO", fontsize=8, color=(0.8, 0.6, 0.2))
        
        # Document title
        page.insert_text((40, 110), title, fontsize=15, color=(0.1, 0.15, 0.2))
        page.insert_text((40, 126), f"DOCUMENT ID: {filename.replace('.pdf','')} | PAGE {page_idx + 1} OF {len(pages_data)}", fontsize=9, color=(0.4, 0.4, 0.4))
        
        # Draw divider
        page.draw_line((40, 135), (555, 135), color=(0.7, 0.75, 0.7), width=1)
        
        # Sections
        curr_y = 160
        for section in page_info.get("sections", []):
            sec_title = section.get("title", "")
            sec_text = section.get("text", "")
            
            page.insert_text((40, curr_y), sec_title.upper(), fontsize=11, color=(0.15, 0.3, 0.2))
            curr_y += 18
            
            # Draw paragraph lines
            for line in sec_text.strip().split("\n"):
                page.insert_text((45, curr_y), line.strip(), fontsize=10, color=(0.2, 0.2, 0.2))
                curr_y += 15
            curr_y += 15
            
        # Footer
        page.draw_line((40, 800), (555, 800), color=(0.8, 0.8, 0.8), width=0.5)
        page.insert_text((40, 815), "STRICTLY FICTIONAL / SYNTHETIC DATA FOR ALGORITHMIC EVALUATION", fontsize=8, color=(0.6, 0.6, 0.6))
        page.insert_text((480, 815), f"Page {page_idx + 1}", fontsize=8, color=(0.6, 0.6, 0.6))

    doc.save(str(pdf_path))
    doc.close()
    print(f"Created: {pdf_path}")

def generate_multimodal_image(filename: str):
    img_path = DEMO_DIR / filename
    ext_path = EXTRACTED_DIR / filename
    
    img = Image.new("RGB", (800, 600), color=(14, 20, 18))
    draw = ImageDraw.Draw(img)
    
    # Draw grid
    for x in range(0, 800, 40):
        draw.line([(x, 0), (x, 600)], fill=(22, 32, 28), width=1)
    for y in range(0, 600, 40):
        draw.line([(0, y), (800, y)], fill=(22, 32, 28), width=1)
        
    # Header
    draw.rectangle([(20, 20), (780, 70)], fill=(20, 30, 25), outline=(50, 80, 60))
    draw.text((35, 30), "TRINETRA MULTIMODAL OVERHEAD SCAN // SECTOR ALPHA", fill=(220, 230, 220))
    draw.text((35, 50), "FIGURE 1: SENSOR RECONNAISSANCE & TARGET TELEMETRY", fill=(210, 160, 40))
    
    # Sector Alpha perimeter
    draw.rectangle([(100, 120), (700, 520)], outline=(40, 140, 70), width=2)
    draw.text((110, 130), "ZONE BOUNDARY: Sector Alpha [GRID-A17]", fill=(40, 180, 90))
    
    # Enemy Vehicle A box
    draw.rectangle([(200, 220), (380, 340)], fill=(30, 40, 45), outline=(56, 189, 248), width=2)
    draw.text((215, 235), "OBJECT: Enemy Vehicle A", fill=(255, 255, 255))
    draw.text((215, 260), "TYPE: Armoured Equipment", fill=(180, 200, 220))
    draw.text((215, 285), "STATUS: Active Recon", fill=(74, 222, 128))
    draw.text((215, 310), "BEARING: 042 deg North", fill=(210, 160, 40))
    
    # Weapon X box
    draw.rectangle([(480, 220), (660, 340)], fill=(35, 45, 40), outline=(234, 88, 12), width=2)
    draw.text((495, 235), "SYSTEM: Weapon X", fill=(255, 255, 255))
    draw.text((495, 260), "TYPE: Targeting Armament", fill=(180, 200, 220))
    draw.text((495, 285), "MOUNT: Vehicle A Interlink", fill=(234, 88, 12))
    draw.text((495, 310), "CALIBER: Advanced Tactical", fill=(210, 160, 40))
    
    # Connecting Link
    draw.line([(380, 280), (480, 280)], fill=(234, 88, 12), width=3)
    draw.text((395, 260), "EQUIPPED", fill=(250, 200, 80))
    
    # Unit Alpha box
    draw.rectangle([(320, 390), (520, 480)], fill=(30, 45, 35), outline=(34, 197, 94), width=2)
    draw.text((335, 405), "CONTINGENT: Unit Alpha", fill=(255, 255, 255))
    draw.text((335, 430), "ECHELON: Command Battalion", fill=(180, 200, 220))
    draw.text((335, 455), "LOCATION: Sector Alpha", fill=(74, 222, 128))
    
    draw.line([(290, 340), (350, 390)], fill=(56, 189, 248), width=2)
    draw.text((285, 370), "LINKED", fill=(56, 189, 248))

    img.save(str(img_path))
    img.save(str(ext_path))
    print(f"Created: {img_path}")

def build_all():
    # 1. Report 01
    generate_pdf(
        "Report_01_Reconnaissance.pdf",
        "REPORT 01 — FORWARD RECONNAISSANCE OBSERVATION",
        [
            {
                "sections": [
                    {
                        "title": "1. Operational Context & Sighting Details",
                        "text": "During primary perimeter sweep across Sector Alpha, field elements identified tactical movements along the northern boundary.\nObserver: Captain A. Sharma, Forward Reconnaissance Patrol.\nDate of observation: 26 September 2026.\nLocation recorded: Sector Alpha perimeter perimeter corridor."
                    },
                    {
                        "title": "2. Equipment & Armament Identification",
                        "text": "The primary detected platform is designated Enemy Vehicle A.\nSurveillance telemetry confirms that Enemy Vehicle A is actively equipped with Weapon X (Heavy Multi-Spectrum Targeting System).\nOperating Status: Active and operational."
                    }
                ]
            },
            {
                "sections": [
                    {
                        "title": "3. Source Evidence Excerpt (Page 2)",
                        "text": "Optical sensor logs verify that Enemy Vehicle A maintains full mobility.\nWeapon X mount calibration was verified during static repositioning.\nSigned by: Captain A. Sharma\nUnit: Forward Recon Detachment"
                    }
                ]
            }
        ]
    )

    # 2. Report 02
    generate_pdf(
        "Report_02_SIGINT_Intercept.pdf",
        "REPORT 02 — ELECTRONIC EMISSION & SIGINT INTERCEPT",
        [
            {
                "sections": [
                    {
                        "title": "1. Signal Triangulation & Command Affiliation",
                        "text": "Electronic Warfare sensors captured encrypted telemetry packets within Sector-A.\nAnalysis conducted by: A. Sharma, SIGINT Directorate.\nSignals analysis indicates Enemy Vehicle A is linked to Unit Alpha.\nTactical encrypted link confirmed between vehicle data transponder and Unit Alpha command post."
                    },
                    {
                        "title": "2. Area Operations",
                        "text": "Unit Alpha has established a tactical command node inside Sector-A.\nMultiple voice communications identify Enemy Vehicle A as attached to Unit Alpha operational control."
                    }
                ]
            }
        ]
    )

    # 3. Report 03
    generate_pdf(
        "Report_03_Field_Incident.pdf",
        "REPORT 03 — AFTER-ACTION TACTICAL INCIDENT REPORT",
        [
            {
                "sections": [
                    {
                        "title": "1. Tactical Incident Summary",
                        "text": "Debriefing regarding Incident Y (Perimeter Skirmish Event).\nDebrief officer: Captain Sharma, Field Liaison Officer.\nUnit Alpha was explicitly mentioned in Incident Y during northern sector redeployment."
                    },
                    {
                        "title": "2. Equipment Status Conflict (Page 1)",
                        "text": "Follow-up damage assessment indicates Enemy Vehicle A status: Inactive following electrical fire.\nNotice: This directly conflicts with earlier Report 01 observation which logged Enemy Vehicle A as Active.\nTRINETRA conflict flag recorded for analyst review."
                    }
                ]
            }
        ]
    )

    # 4. Multimodal Scan
    generate_multimodal_image("Report_04_Tactical_Overhead_Scan.png")

if __name__ == "__main__":
    build_all()
