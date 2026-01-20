#!/usr/bin/env python3
"""
Quebec Education Program Website Scraper
Downloads all curriculum documents from the official QEP website
"""

import os
import re
import requests
from pathlib import Path
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import time

# Base URL for Quebec Education Program
BASE_URL = "https://www.quebec.ca/en/education/preschool-elementary-and-secondary-schools/programs-training-evaluation/quebec-education-program"

# Output directory
OUTPUT_DIR = Path(r"c:\Users\johnn\Downloads\PFEQ_Complete")

def create_output_dirs():
    """Create output directory structure"""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "preschool").mkdir(exist_ok=True)
    (OUTPUT_DIR / "elementary").mkdir(exist_ok=True)
    (OUTPUT_DIR / "secondary").mkdir(exist_ok=True)

def get_page_content(url):
    """Fetch page content with retries"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def find_pdf_links(html_content, base_url):
    """Find all PDF links on a page"""
    soup = BeautifulSoup(html_content, 'html.parser')
    pdf_links = set()
    
    # Find all links
    for link in soup.find_all('a', href=True):
        href = link['href']
        full_url = urljoin(base_url, href)
        
        # Check if it's a PDF
        if href.lower().endswith('.pdf') or '.pdf' in full_url.lower():
            pdf_links.add(full_url)
        
        # Check for Quebec CDN PDF links
        if 'cdn-contenu.quebec.ca' in href and '.pdf' in href:
            pdf_links.add(full_url)
    
    # Also look for direct PDF references in text and script tags
    pdf_pattern = r'https?://[^\s<>"\'\)]+\.pdf'
    found_pdfs = re.findall(pdf_pattern, html_content)
    for pdf_url in found_pdfs:
        pdf_links.add(pdf_url)
    
    # Look in data attributes and script content
    for script in soup.find_all('script'):
        if script.string:
            found_pdfs = re.findall(pdf_pattern, script.string)
            for pdf_url in found_pdfs:
                pdf_links.add(pdf_url)
    
    return list(pdf_links)

def download_pdf(url, output_path):
    """Download a PDF file"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=60, stream=True)
        response.raise_for_status()
        
        # Check if it's actually a PDF
        content_type = response.headers.get('content-type', '').lower()
        if 'pdf' not in content_type and not url.lower().endswith('.pdf'):
            print(f"  Warning: {url} doesn't appear to be a PDF (content-type: {content_type})")
            return False
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = output_path.stat().st_size
        if file_size < 1000:  # Less than 1KB is probably not a real PDF
            output_path.unlink()
            print(f"  Warning: Downloaded file too small, deleted")
            return False
        
        return True
    except Exception as e:
        print(f"  Error downloading {url}: {e}")
        return False

def scrape_section(section_url, section_name):
    """Scrape a section of the website (preschool, elementary, secondary)"""
    print(f"\n=== Scraping {section_name} ===")
    section_dir = OUTPUT_DIR / section_name.lower()
    section_dir.mkdir(exist_ok=True)
    
    # Get main page
    html = get_page_content(section_url)
    if not html:
        print(f"Could not fetch {section_name} page")
        return []
    
    pdf_links = find_pdf_links(html, section_url)
    print(f"Found {len(pdf_links)} PDF links on main page")
    
    # Also parse the page to find sub-pages
    soup = BeautifulSoup(html, 'html.parser')
    sub_pages = []
    
    # Look for links to subject pages - Quebec site uses specific patterns
    for link in soup.find_all('a', href=True):
        href = link['href']
        text = link.get_text(strip=True)
        
        # Look for links that might lead to more documents
        # Quebec site often has links to subject-specific pages
        if any(keyword in href.lower() for keyword in ['program', 'subject', 'curriculum', 'competence', 'evaluation', 'matiere', 'domaine']):
            full_url = urljoin(section_url, href)
            # Avoid duplicates and anchors
            if full_url not in sub_pages and full_url != section_url and '#' not in full_url:
                sub_pages.append(full_url)
        
        # Also check for direct links to PDF directories
        if 'cdn-contenu.quebec.ca' in href and '/pfeq/' in href:
            # This might be a directory listing, try to get it
            if href not in sub_pages:
                sub_pages.append(full_url)
    
    print(f"Found {len(sub_pages)} potential sub-pages to check")
    
    # Visit sub-pages to find more PDFs - FAST MODE: only check if it looks like a PDF link
    all_pdfs = set(pdf_links)
    checked_urls = set()  # Track checked URLs to avoid duplicates
    
    # Skip non-PDF sub-pages for speed - only check direct PDF links
    for sub_url in sub_pages[:50]:  # Increased limit but skip HTML pages
        if sub_url in checked_urls:
            continue
        checked_urls.add(sub_url)
        
        # Skip if it's already a PDF
        if sub_url.lower().endswith('.pdf') or '.pdf' in sub_url.lower():
            all_pdfs.add(sub_url)
            continue
        
        # Skip HTML pages - only check if URL suggests PDFs
        if 'cdn-contenu.quebec.ca' in sub_url and '/pfeq/' in sub_url:
            # This might be a PDF directory, check it quickly
            print(f"  Checking: {sub_url[:60]}...")
            sub_html = get_page_content(sub_url)
            if sub_html:
                sub_pdfs = find_pdf_links(sub_html, sub_url)
                all_pdfs.update(sub_pdfs)
            time.sleep(0.1)  # Minimal delay for speed
        # Skip other HTML pages to save time
    
    print(f"Total PDFs found for {section_name}: {len(all_pdfs)}")
    
    # Download PDFs
    downloaded = []
    for i, pdf_url in enumerate(all_pdfs, 1):
        # Extract filename from URL
        parsed = urlparse(pdf_url)
        filename = os.path.basename(parsed.path)
        if not filename or not filename.endswith('.pdf'):
            # Generate filename from URL
            filename = f"document_{i}.pdf"
        
        # Clean filename
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        output_path = section_dir / filename
        
        # Skip if already downloaded
        if output_path.exists():
            print(f"  [{i}/{len(all_pdfs)}] Skipping (exists): {filename}")
            downloaded.append(str(output_path))
            continue
        
        print(f"  [{i}/{len(all_pdfs)}] Downloading: {filename}")
        if download_pdf(pdf_url, output_path):
            downloaded.append(str(output_path))
            file_size_kb = output_path.stat().st_size / 1024
            print(f"    [OK] Downloaded ({file_size_kb:.1f} KB)")
        else:
            print(f"    [FAILED]")
        
        time.sleep(0.1)  # Minimal delay for speed
    
    return downloaded

def main():
    """Main scraping function"""
    print("Quebec Education Program Website Scraper")
    print("=" * 50)
    
    create_output_dirs()
    
    # Scrape each section
    # For now we only scrape Secondary to keep the run time reasonable
    sections = [
        ("https://www.quebec.ca/en/education/preschool-elementary-and-secondary-schools/programs-training-evaluation/quebec-education-program/secondary", "Secondary"),
    ]
    
    all_downloaded = []
    for url, name in sections:
        downloaded = scrape_section(url, name)
        all_downloaded.extend(downloaded)
        time.sleep(2)  # Pause between sections
    
    print(f"\n=== Summary ===")
    print(f"Total documents downloaded: {len(all_downloaded)}")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Now process all downloaded PDFs with the extraction script
    print(f"\n=== Next Steps ===")
    print("Run the extraction script to process all downloaded PDFs:")
    print(f"python extract_pfeq_data.py")

if __name__ == '__main__':
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("Installing required packages...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'requests', 'beautifulsoup4'])
        import requests
        from bs4 import BeautifulSoup
    
    main()
