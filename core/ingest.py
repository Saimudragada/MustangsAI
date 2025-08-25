import requests, time
from bs4 import BeautifulSoup
from readability import Document
from markdownify import markdownify as md
from loguru import logger
import os

HEADERS = {"User-Agent": "MustangsAI/1.0 (+https://msutexas.edu)"}
ALLOW_HOST = "msutexas.edu"  # restrict only to MSU Texas domain

def fetch_clean(url: str) -> dict:
    if ALLOW_HOST not in url:
        raise ValueError("URL outside allowed domain.")
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    html = r.text
    try:
        doc = Document(html)
        title = doc.short_title()
        content_html = doc.summary()
    except Exception:
        soup = BeautifulSoup(html, "html.parser")
        title = (soup.title.string or "").strip() if soup.title else url
        content_html = soup.body or soup
    content_md = md(str(content_html))
    logger.info(f"Fetched {url} ({len(content_md)} chars)")
    time.sleep(0.5)  # polite delay
    return {"url": url, "title": title, "markdown": content_md}
