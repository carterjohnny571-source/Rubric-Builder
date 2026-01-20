#!/usr/bin/env python3
"""
Complete Curriculum Data Update Script
1. Scrapes Quebec Education Program website for all documents
2. Downloads PDFs to organized folders
3. Extracts curriculum data from all PDFs
4. Generates updated JavaScript curriculum file
5. Ready for integration into rubric builder
"""

import os
import sys
from pathlib import Path

# Add current directory to path to import our modules
sys.path.insert(0, str(Path(__file__).parent))

# Import our scraping and extraction modules
try:
    from scrape_quebec_education import main as scrape_main
    from extract_pfeq_data import generate_js_structure, extract_pdf_text, parse_curriculum_data
except ImportError:
    print("Error: Could not import required modules")
    sys.exit(1)

def main():
    """Main update process"""
    print("=" * 60)
    print("Quebec Education Program - Complete Curriculum Data Update")
    print("=" * 60)
    
    # Step 1: Scrape website for new documents
    print("\n[Step 1/3] Scraping Quebec Education Program website...")
    print("This may take several minutes...")
    try:
        scrape_main()
    except Exception as e:
        print(f"Warning: Scraping encountered issues: {e}")
        print("Continuing with existing PDFs...")
    
    # Step 2: Extract data from all PDFs
    print("\n[Step 2/3] Extracting curriculum data from PDFs...")
    from extract_pfeq_data import Path as PathType
    
    pfeq_folders = [
        Path(r'c:\Users\johnn\Downloads\PFEQ'),
        Path(r'c:\Users\johnn\Downloads\PFEQ_Complete\preschool'),
        Path(r'c:\Users\johnn\Downloads\PFEQ_Complete\elementary'),
        Path(r'c:\Users\johnn\Downloads\PFEQ_Complete\secondary'),
    ]
    
    all_parsed_data = []
    
    for folder in pfeq_folders:
        if folder.exists():
            print(f"\nProcessing: {folder}")
            pdf_files = list(folder.glob('*.pdf'))
            print(f"  Found {len(pdf_files)} PDF files")
            
            for i, pdf_file in enumerate(pdf_files, 1):
                if i % 10 == 0:
                    print(f"  Progress: {i}/{len(pdf_files)}")
                
                try:
                    text = extract_pdf_text(pdf_file)
                    if not text or not isinstance(text, str) or len(text.strip()) < 100:
                        continue
                    
                    parsed_items = parse_curriculum_data(text, pdf_file.name)
                    if parsed_items:
                        all_parsed_data.extend(parsed_items)
                except Exception as e:
                    continue
    
    print(f"\nTotal curriculum entries extracted: {len(all_parsed_data)}")
    
    # Step 3: Generate JavaScript file
    print("\n[Step 3/3] Generating JavaScript curriculum data file...")
    if all_parsed_data:
        js_code = generate_js_structure(all_parsed_data)
        
        output_file = Path(__file__).parent / 'pfeq_curriculum_data.js'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(js_code)
        
        print(f"✓ Curriculum data file generated: {output_file}")
        print(f"  Size: {len(js_code):,} characters")
        print(f"  Subjects: {len(set(d['subject'] for d in all_parsed_data))}")
        print(f"  Total grade/subject combinations: {len(all_parsed_data)}")
    else:
        print("✗ No data extracted. Please check PDF files.")
    
    print("\n" + "=" * 60)
    print("Update complete! The rubric builder will automatically use the new data.")
    print("=" * 60)

if __name__ == '__main__':
    main()
