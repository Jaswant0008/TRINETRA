import glob
from app.services.document_processor import DocumentProcessor
from app.services.extractor import AutonomousEntityExtractor

for f in sorted(glob.glob('d:/TRINETRA/backend/data/uploads/*')):
    doc = DocumentProcessor.process_file(f)
    print("=== FILE:", doc['document_name'], f"({doc['file_type']}) ===")
    all_e = []
    all_t = []
    for p in doc['pages']:
        e, t = AutonomousEntityExtractor.extract_from_text(p['text'], doc['document_name'], p['page_number'])
        all_e.extend([item['name'] for item in e])
        all_t.extend([f"{item['subject_name']} -> {item['predicate']} -> {item['object_name']}" for item in t])
    print(f"Entities ({len(all_e)}): {all_e}")
    print(f"Triples ({len(all_t)}): {all_t}\n")
