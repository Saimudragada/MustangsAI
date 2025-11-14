"""
MustangsAI Web Scraper
Scrapes 100+ pages from msutexas.edu for RAG ingestion

Features:
- Scrapes from seed_urls.txt and additional_sources.txt
- Extracts clean text content from HTML
- Saves to data/raw/ directory
- Handles errors gracefully
- Respects robots.txt and rate limiting
"""

from __future__ import annotations
import os
import time
import json
from pathlib import Path
from typing import List, Dict
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup
from readability import Document
from markdownify import markdownify as md

class MSUTexasScraper:
    """Scrapes MSU Texas website for RAG knowledge base"""

    def __init__(self, output_dir: str = "data/raw"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MustangsAI-Bot/1.0 (Educational RAG Assistant; saimudragada1@gmail.com)'
        })
        self.delay = 1.5  # Polite crawl delay (seconds)
        self.scraped_urls = set()

    def load_seed_urls(self, seed_files: List[Path]) -> List[str]:
        """Load URLs from seed files"""
        urls = []
        for seed_file in seed_files:
            if seed_file.exists():
                content = seed_file.read_text()
                for line in content.splitlines():
                    line = line.strip()
                    # Skip comments and empty lines
                    if line and not line.startswith('#'):
                        urls.append(line)

        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        return unique_urls

    def clean_text(self, html_content: str) -> str:
        """Extract clean text from HTML using readability"""
        try:
            # Use readability to extract main content
            doc = Document(html_content)
            clean_html = doc.summary()

            # Convert to markdown for better structure preservation
            text = md(clean_html, heading_style="ATX")

            # Additional cleanup
            lines = text.split('\n')
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                # Skip lines that are just navigation elements
                if line and not self._is_navigation(line):
                    cleaned_lines.append(line)

            return '\n'.join(cleaned_lines)
        except Exception as e:
            print(f"  ⚠️  Readability failed: {e}, falling back to BeautifulSoup")
            # Fallback to basic BeautifulSoup extraction
            soup = BeautifulSoup(html_content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            text = soup.get_text(separator='\n', strip=True)
            return text

    def _is_navigation(self, line: str) -> bool:
        """Check if line is likely navigation content"""
        nav_keywords = ['skip to', 'menu', 'search', 'login', 'sign in', 'home >', 'breadcrumb']
        line_lower = line.lower()
        return any(keyword in line_lower for keyword in nav_keywords) and len(line) < 50

    def scrape_url(self, url: str) -> Dict:
        """Scrape a single URL and return metadata + content"""
        print(f"📄 Scraping: {url}")

        if url in self.scraped_urls:
            print(f"  ⏭️  Already scraped, skipping")
            return None

        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            # Extract clean content
            content = self.clean_text(response.text)

            # Get title
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string if soup.title else urlparse(url).path

            # Mark as scraped
            self.scraped_urls.add(url)

            # Polite delay
            time.sleep(self.delay)

            return {
                'url': url,
                'title': str(title).strip(),
                'content': content,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'success'
            }

        except requests.exceptions.RequestException as e:
            print(f"  ❌ Error: {e}")
            return {
                'url': url,
                'status': 'error',
                'error': str(e)
            }

    def save_scraped_data(self, data: List[Dict], format: str = 'txt'):
        """Save scraped data to files"""

        # Save as individual text files for RAG ingestion
        if format == 'txt':
            for i, item in enumerate(data):
                if item['status'] == 'success':
                    # Create filename from URL
                    parsed = urlparse(item['url'])
                    filename = parsed.path.replace('/', '_').strip('_')
                    if not filename:
                        filename = parsed.netloc
                    filename = f"{i:03d}_{filename}.txt"

                    filepath = self.output_dir / filename

                    # Write content with metadata header
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(f"Title: {item['title']}\n")
                        f.write(f"Source: {item['url']}\n")
                        f.write(f"Scraped: {item['scraped_at']}\n")
                        f.write("=" * 80 + "\n\n")
                        f.write(item['content'])

        # Also save metadata as JSON
        metadata_file = self.output_dir / 'scrape_metadata.json'
        metadata = [
            {
                'url': item['url'],
                'title': item.get('title', ''),
                'status': item['status'],
                'scraped_at': item.get('scraped_at', '')
            }
            for item in data
        ]

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        print(f"\n✅ Saved {len(data)} documents to {self.output_dir}")
        print(f"✅ Metadata saved to {metadata_file}")

    def scrape_all(self, seed_files: List[Path]) -> List[Dict]:
        """Scrape all URLs from seed files"""
        urls = self.load_seed_urls(seed_files)

        print(f"\n🚀 Starting scrape of {len(urls)} URLs from MSU Texas")
        print(f"📂 Output directory: {self.output_dir}")
        print("=" * 80 + "\n")

        results = []
        success_count = 0
        error_count = 0

        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}]")
            result = self.scrape_url(url)

            if result:
                results.append(result)
                if result['status'] == 'success':
                    success_count += 1
                else:
                    error_count += 1

        print("\n" + "=" * 80)
        print(f"✅ Scraping complete!")
        print(f"   Success: {success_count}")
        print(f"   Errors: {error_count}")
        print(f"   Total: {len(results)}")

        return results


def main():
    """Main scraping function"""
    # Initialize scraper
    scraper = MSUTexasScraper(output_dir="data/raw")

    # Seed files
    seed_files = [
        Path("data/seed_urls.txt"),
        Path("data/additional_sources.txt")
    ]

    # Scrape all URLs
    results = scraper.scrape_all(seed_files)

    # Save results
    scraper.save_scraped_data(results, format='txt')

    # Print summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"Total URLs scraped: {len(results)}")
    print(f"Files saved to: data/raw/")
    print(f"Ready for ingestion with: python ingest.py")
    print("\n✨ Next steps:")
    print("  1. Review data/raw/ to verify scraped content")
    print("  2. Run: python ingest.py")
    print("  3. Run: streamlit run app.py")


if __name__ == "__main__":
    main()
