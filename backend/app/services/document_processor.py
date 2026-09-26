import os
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import pymupdf
import docx
from PIL import Image

from app.config import EXTRACTED_IMAGES_DIR, UPLOADS_DIR

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Multi-format Document Processor handling PDF, DOCX, TXT, and Imagery."""

    @classmethod
    def process_file(cls, file_path: str, doc_name: Optional[str] = None, doc_id: Optional[str] = None) -> Dict[str, Any]:
        p = Path(file_path)
        doc_name = doc_name or p.name
        doc_id = doc_id or f"doc_{uuid.uuid4().hex[:8]}"
        ext = p.suffix.lower()

        if ext == ".pdf":
            return cls.process_pdf(file_path, doc_name, doc_id)
        elif ext in [".docx", ".doc"]:
            return cls.process_docx(file_path, doc_name, doc_id)
        elif ext in [".png", ".jpg", ".jpeg"]:
            return cls.process_image_doc(file_path, doc_name, doc_id)
        else:
            return cls.process_text_file(file_path, doc_name, doc_id)

    @classmethod
    def process_pdf(cls, pdf_path: str, doc_name: str, doc_id: str) -> Dict[str, Any]:
        doc_result = {
            "document_id": doc_id,
            "document_name": doc_name,
            "file_type": "PDF",
            "file_path": str(pdf_path),
            "pages": [],
            "all_extracted_images": [],
            "full_text": ""
        }

        try:
            doc = pymupdf.open(pdf_path)
            for page_idx in range(len(doc)):
                page_num = page_idx + 1
                page = doc[page_idx]

                page_text = page.get_text("text")
                doc_result["full_text"] += f"\n--- Page {page_num} ---\n" + page_text

                text_blocks = page.get_text("blocks")
                image_list = page.get_images(full=True)
                page_images = []

                for img_idx, img_info in enumerate(image_list):
                    xref = img_info[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]

                    img_filename = f"{doc_id}_p{page_num}_img{img_idx+1}.{image_ext}"
                    img_save_path = EXTRACTED_IMAGES_DIR / img_filename

                    with open(img_save_path, "wb") as f_img:
                        f_img.write(image_bytes)

                    rects = page.get_image_rects(xref)
                    img_rect = rects[0] if rects else None

                    surrounding_snippets = []
                    overlaid_text_snippets = []

                    if img_rect and text_blocks:
                        for b in text_blocks:
                            if len(b) >= 5:
                                b_rect = pymupdf.Rect(b[0], b[1], b[2], b[3])
                                text_content = b[4].strip()
                                if not text_content:
                                    continue
                                if img_rect.intersects(b_rect):
                                    overlaid_text_snippets.append(text_content)
                                elif abs(b_rect.y0 - img_rect.y1) < 150 or abs(img_rect.y0 - b_rect.y1) < 150:
                                    surrounding_snippets.append(text_content)

                    surrounding_text = " ".join(surrounding_snippets) if surrounding_snippets else page_text[:300]
                    overlaid_text = " ".join(overlaid_text_snippets)

                    img_meta = {
                        "image_id": f"img_{doc_id}_{page_num}_{img_idx+1}",
                        "filename": img_filename,
                        "file_path": str(img_save_path),
                        "url": f"/static/extracted/{img_filename}",
                        "page_number": page_num,
                        "width": base_image["width"],
                        "height": base_image["height"],
                        "surrounding_text": surrounding_text,
                        "overlaid_text": overlaid_text,
                        "rect": [img_rect.x0, img_rect.y0, img_rect.x1, img_rect.y1] if img_rect else None
                    }
                    page_images.append(img_meta)
                    doc_result["all_extracted_images"].append(img_meta)

                doc_result["pages"].append({
                    "page_number": page_num,
                    "text": page_text,
                    "images": page_images
                })

            doc.close()
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")

        return doc_result

    @classmethod
    def process_docx(cls, docx_path: str, doc_name: str, doc_id: str) -> Dict[str, Any]:
        try:
            doc = docx.Document(docx_path)
            paras = [p.text for p in doc.paragraphs if p.text.strip()]
            full_text = "\n\n".join(paras)
        except Exception as e:
            logger.error(f"Error parsing DOCX {docx_path}: {e}")
            full_text = ""

        return {
            "document_id": doc_id,
            "document_name": doc_name,
            "file_type": "DOCX",
            "file_path": str(docx_path),
            "full_text": full_text,
            "pages": [{
                "page_number": 1,
                "text": full_text,
                "images": []
            }],
            "all_extracted_images": []
        }

    @classmethod
    def process_text_file(cls, txt_path: str, doc_name: str, doc_id: str) -> Dict[str, Any]:
        try:
            with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading text file: {e}")
            content = ""

        return {
            "document_id": doc_id,
            "document_name": doc_name,
            "file_type": "TXT",
            "file_path": str(txt_path),
            "full_text": content,
            "pages": [{
                "page_number": 1,
                "text": content,
                "images": []
            }],
            "all_extracted_images": []
        }

    @classmethod
    def process_image_doc(cls, img_path: str, doc_name: str, doc_id: str) -> Dict[str, Any]:
        filename = Path(img_path).name
        return {
            "document_id": doc_id,
            "document_name": doc_name,
            "file_type": "IMAGE",
            "file_path": str(img_path),
            "full_text": f"Visual Tactical Reconnaissance Image: {doc_name}",
            "pages": [{
                "page_number": 1,
                "text": f"Visual Reconnaissance Image: {doc_name}",
                "images": [{
                    "image_id": f"img_{doc_id}_1_1",
                    "filename": filename,
                    "file_path": str(img_path),
                    "url": f"/static/extracted/{filename}",
                    "page_number": 1,
                    "surrounding_text": doc_name,
                    "overlaid_text": ""
                }]
            }],
            "all_extracted_images": [{
                "image_id": f"img_{doc_id}_1_1",
                "filename": filename,
                "file_path": str(img_path),
                "url": f"/static/extracted/{filename}",
                "page_number": 1
            }]
        }
