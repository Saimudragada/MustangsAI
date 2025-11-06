"""
Enhanced faculty/staff scraper for MSU Texas
Extracts faculty names, titles, emails, departments
"""
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import json
import time

def scrape_faculty_page(url: str) -> dict:
    """Scrape a faculty directory page"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        faculty_data = {
            'url': url,
            'faculty': []
        }
        
        # Common patterns for faculty listings
        # Adjust selectors based on actual MSU Texas HTML structure
        faculty_sections = soup.find_all(['div', 'section'], class_=['faculty', 'staff', 'directory'])
        
        for section in faculty_sections:
            # Try to extract faculty info
            name_elem = section.find(['h3', 'h4', 'strong'])
            title_elem = section.find(['p', 'span'], class_=['title', 'position'])
            email_elem = section.find('a', href=lambda h: h and 'mailto:' in h)
            
            if name_elem:
                faculty_info = {
                    'name': name_elem.get_text(strip=True),
                    'title': title_elem.get_text(strip=True) if title_elem else '',
                    'email': email_elem.get_text(strip=True) if email_elem else '',
                    'department': extract_department_from_url(url)
                }
                faculty_data['faculty'].append(faculty_info)
        
        # Also extract all text for RAG purposes
        text_content = soup.get_text(separator='\n', strip=True)
        faculty_data['full_text'] = text_content
        
        return faculty_data
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return {'url': url, 'error': str(e)}

def extract_department_from_url(url: str) -> str:
    """Extract department name from URL"""
    parts = url.split('/')
    for part in parts:
        if part in ['business', 'education', 'nursing', 'computer-science', 
                    'psychology', 'biology', 'mathematics', 'english', 'history']:
            return part.replace('-', ' ').title()
    return 'Unknown'

def save_faculty_data(data: list, output_dir: Path):
    """Save scraped faculty data"""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save as JSON
    json_path = output_dir / 'faculty_data.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    # Save as text for easy ingestion
    txt_path = output_dir / 'faculty_directory.txt'
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("MSU TEXAS FACULTY DIRECTORY\n")
        f.write("=" * 80 + "\n\n")
        
        for page_data in data:
            if 'error' in page_data:
                continue
            
            f.write(f"\nSource: {page_data['url']}\n")
            f.write("-" * 80 + "\n")
            
            for faculty in page_data.get('faculty', []):
                f.write(f"\nName: {faculty['name']}\n")
                f.write(f"Title: {faculty['title']}\n")
                f.write(f"Department: {faculty['department']}\n")
                f.write(f"Email: {faculty['email']}\n")
                f.write("\n")
            
            # Include full text
            if page_data.get('full_text'):
                f.write("\nFull Page Content:\n")
                f.write(page_data['full_text'][:2000])  # Truncate if too long
                f.write("\n" + "=" * 80 + "\n")
    
    print(f"✅ Saved faculty data to {output_dir}")

if __name__ == "__main__":
    # Faculty pages to scrape - UPDATED with working URLs
    faculty_urls = [
        # Main faculty page
        "https://msutexas.edu/academics/business/faculty/",
        
        # Individual department contacts (these have actual faculty names!)
        "https://msutexas.edu/academics/business/management/contact.php",
        "https://msutexas.edu/academics/business/finance/contact.php",
        "https://msutexas.edu/academics/business/accounting/contact.php",
        "https://msutexas.edu/academics/business/marketing/contact.php",
        
        # Directory listing
        "https://directory.msutexas.edu/departments/college-of-business-administration-dillard",
        
        # General business pages with faculty info
        "https://msutexas.edu/academics/business/",
        "https://msutexas.edu/academics/business/meet-our-faculty.php",
    ]
    
    all_data = []
    for url in faculty_urls:
        print(f"Scraping: {url}")
        data = scrape_faculty_page(url)
        all_data.append(data)
        time.sleep(2)  # Be polite to the server
    
    output_dir = Path("data/raw")
    save_faculty_data(all_data, output_dir)
    print("✅ Faculty scraping complete!")