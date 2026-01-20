#!/usr/bin/env python3
"""
Process All Curriculum PDFs
Extracts data from all PDFs in PFEQ folders and generates complete curriculum data
"""

import sys
from pathlib import Path

# Import extraction functions
sys.path.insert(0, str(Path(__file__).parent))
from extract_pfeq_data import (
    extract_pdf_text, parse_curriculum_data, generate_js_structure
)

def process_all_folders():
    """Process all PDFs in all PFEQ folders"""
    folders = [
        Path(r'c:\Users\johnn\Downloads\PFEQ'),
        Path(r'c:\Users\johnn\Downloads\PFEQ_Complete\preschool'),
        Path(r'c:\Users\johnn\Downloads\PFEQ_Complete\elementary'),
        Path(r'c:\Users\johnn\Downloads\PFEQ_Complete\secondary'),
    ]
    
    all_parsed_data = []
    total_pdfs = 0
    processed = 0
    
    for folder in folders:
        if not folder.exists():
            continue
        
        pdf_files = list(folder.glob('*.pdf'))
        total_pdfs += len(pdf_files)
        
        print(f"\nProcessing {folder.name}: {len(pdf_files)} PDFs")
        
        for pdf_file in pdf_files:
            try:
                text = extract_pdf_text(pdf_file)
                if not text or not isinstance(text, str) or len(text.strip()) < 100:
                    continue
                
                parsed_items = parse_curriculum_data(text, pdf_file.name)
                if parsed_items:
                    all_parsed_data.extend(parsed_items)
                    processed += 1
                    for item in parsed_items:
                        print(f"  [OK] {item['subject']} - {item['grade']}")
            except Exception as e:
                print(f"  [ERROR] {pdf_file.name} - {e}")
    
    print(f"\n{'='*60}")
    print(f"Processed {processed}/{total_pdfs} PDFs")
    print(f"Extracted {len(all_parsed_data)} curriculum entries")
    print(f"{'='*60}")
    
    if all_parsed_data:
        js_code = generate_js_structure(all_parsed_data)
        output_file = Path(__file__).parent / 'pfeq_curriculum_data.js'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(js_code)
        
        print(f"\n[SUCCESS] Generated: {output_file}")
        print(f"  Size: {len(js_code):,} characters")
        
        # Count unique subjects and grades
        subjects = set(d['subject'] for d in all_parsed_data)
        grades = set(d['grade'] for d in all_parsed_data)
        print(f"  Subjects: {len(subjects)}")
        print(f"  Grade levels: {len(grades)}")
        print(f"\nSubjects found: {', '.join(sorted(subjects))}")
        print(f"Grades found: {', '.join(sorted(grades))}")
    
    return len(all_parsed_data) > 0

if __name__ == '__main__':
    print("Quebec Education Program - Complete Curriculum Processing")
    print("=" * 60)
    success = process_all_folders()
    if success:
        print("\n[SUCCESS] Curriculum data ready for rubric builder!")
    else:
        print("\n[ERROR] No data extracted. Check PDF files.")
