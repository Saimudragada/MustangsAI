# core/ingest.py
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from readability import Document
from markdownify import markdownify as md
from loguru import logger
from pdfminer.high_level import extract_text as pdf_extract_text
from io import BytesIO

HEADERS = {"User-Agent": "Mozilla/5.0 (MustangsAI bot)"}


def _table_to_text(table):
    rows = []
    for tr in table.find_all("tr"):
        cells = [c.get_text(separator=" ", strip=True) for c in tr.find_all(["th", "td"])]
        if cells:
            rows.append(" | ".join(cells))
    return "\n".join(rows) + ("\n" if rows else "")


def _clean_html_keep_tables(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    # remove common noise
    for tag in soup(["script", "style", "noscript", "iframe", "svg", "button", "form", "nav", "footer", "aside"]):
        tag.decompose()

    # turn tables into plaintext so hours/rates survive
    for tbl in soup.find_all("table"):
        txt = _table_to_text(tbl)
        tbl.replace_with(soup.new_string("\n" + txt + "\n"))

    text_html = re.sub(r"\n{3,}", "\n\n", str(soup))
    return text_html


def _absolutize(href: str, base: str) -> str:
    return urllib.parse.urljoin(base, href)


def _same_host(url_a: str, url_b: str) -> bool:
    return urllib.parse.urlparse(url_a).netloc == urllib.parse.urlparse(url_b).netloc


def _is_pdf(href: str) -> bool:
    return href.lower().endswith(".pdf")


def fetch_html_doc(url: str) -> dict:
    """Return one doc dict: title, markdown, url (HTML only)."""
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()

    doc = Document(r.text)
    title = (doc.short_title() or "").strip()
    main_html = _clean_html_keep_tables(doc.summary(html_partial=True))
    markdown = md(main_html, heading_style="ATX", strip=["img", "a"])
    markdown = re.sub(r"[ \t]+", " ", markdown).strip()

    logger.info(f"Fetched {url} ({len(markdown)} chars)")
    return {"title": title, "markdown": markdown, "url": url}


def fetch_pdf_doc(pdf_url: str, link_text: str = "") -> dict | None:
    """Download a PDF and return as a doc dict (title, markdown, url)."""
    try:
        pr = requests.get(pdf_url, headers=HEADERS, timeout=30)
        pr.raise_for_status()
        text = pdf_extract_text(BytesIO(pr.content)) or ""
        text = re.sub(r"[ \t]+", " ", text).strip()
        if not text:
            return None
        title = link_text.strip() or pdf_url.rsplit("/", 1)[-1]
        logger.info(f"Fetched PDF {pdf_url} ({len(text)} chars)")
        return {"title": title, "markdown": text, "url": pdf_url}
    except Exception as e:
        logger.warning(f"PDF fetch failed for {pdf_url}: {e}")
        return None


def fetch_all(url: str) -> list[dict]:
    """
    Return a list of docs:
      - The cleaned HTML doc
      - Plus any same-domain PDF docs linked from the page
    """
    out = []
    html_doc = fetch_html_doc(url)
    out.append(html_doc)

    # scan for PDFs on the same host
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")
        seen = set()
        for a in soup.find_all("a", href=True):
            href = _absolutize(a["href"], url)
            if _is_pdf(href) and _same_host(href, url):
                if href in seen:
                    continue
                seen.add(href)
                pdf_doc = fetch_pdf_doc(href, link_text=a.get_text(" ", strip=True))
                if pdf_doc:
                    out.append(pdf_doc)
    except Exception as e:
        logger.warning(f"While scanning PDFs on {url}: {e}")

    return out
