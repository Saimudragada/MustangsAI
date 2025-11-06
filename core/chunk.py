# core/chunk.py
from typing import List, Dict
import re
import hashlib

# Chunking parameters
MAX_CHARS = 1200     # max characters per chunk
OVERLAP   = 200      # overlap between chunks to keep context


def _normalize_ws(text: str) -> str:
    """Collapse whitespace."""
    return re.sub(r"\s+", " ", text).strip()


def split_markdown(md: str, max_chars: int = MAX_CHARS, overlap: int = OVERLAP) -> List[str]:
    """
    Split markdown/plaintext into overlapping chunks, respecting paragraph breaks when possible.
    """
    # First split by paragraph-ish breaks
    blocks = re.split(r"\n\s*\n", md)
    chunks: List[str] = []
    buf = ""

    for b in blocks:
        b = b.strip()
        if not b:
            continue

        # If the block fits in the current buffer
        if len(buf) + len(b) + 2 <= max_chars:
            buf = (buf + "\n\n" + b) if buf else b
            continue

        # Flush current buffer
        if buf:
            chunks.append(buf)
            buf = ""

        # If single block is too big, hard-wrap it
        if len(b) > max_chars:
            i = 0
            while i < len(b):
                end = i + max_chars
                chunks.append(b[i:end])
                i = max(i + max_chars - overlap, i + 1)
        else:
            buf = b

    if buf:
        chunks.append(buf)

    # Tidy whitespace
    return [_normalize_ws(c) for c in chunks if _normalize_ws(c)]


def build_docs(doc: Dict, source: str = "msutexas") -> List[Dict]:
    """
    Turn a single fetched doc {title, markdown, url} into a list of chunk dicts:
    {"id", "text", "meta": {"url","title"}}
    """
    md = (doc.get("markdown") or "").strip()
    url = doc.get("url", "")
    title = doc.get("title", "")

    if not md:
        return []

    chunks = split_markdown(md)
    base = f"{source}:{hashlib.md5((url + title).encode('utf-8', errors='ignore')).hexdigest()}"

    out: List[Dict] = []
    for i, ch in enumerate(chunks):
        out.append({
            "id": f"{base}:{i}",
            "text": ch,
            "meta": {"url": url, "title": title},
        })
    return out
