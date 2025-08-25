# core/chunk.py
import re
from typing import List, Dict

def split_markdown(md: str, max_tokens: int = 350) -> List[str]:
    # Split on headings or blank-line breaks
    blocks = re.split(r"\n(?=#)|\n{2,}", md)
    chunks, cur, count = [], [], 0
    for b in blocks:
        t = b.strip()
        if not t:
            continue
        tokens = len(t.split())
        if count + tokens > max_tokens and cur:
            chunks.append("\n\n".join(cur))
            cur, count = [t], tokens
        else:
            cur.append(t)
            count += tokens
    if cur:
        chunks.append("\n\n".join(cur))
    return chunks

def build_docs(record: Dict, source: str) -> List[Dict]:
    base = {"source": source, "url": record["url"], "title": record["title"]}
    parts = split_markdown(record["markdown"])
    return [{**base, "chunk_id": f"{i:04d}", "text": p} for i, p in enumerate(parts)]
