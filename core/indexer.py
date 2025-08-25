# core/indexer.py
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.utils import embedding_functions
from core.ingest import fetch_clean
from core.chunk import build_docs

load_dotenv()
CHROMA_DIR = os.getenv("CHROMA_DIR", "./data/chroma")
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

def load_urls(path="data/seeds/msu_urls.txt"):
    with open(path, "r") as f:
        return [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]

def build_index():
    urls = load_urls()
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = client.get_or_create_collection(
        name="msu_docs",
        metadata={"hnsw:space": "cosine"},
        embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBED_MODEL
        ),
    )

    ids, texts, metas = [], [], []
    for url in urls:
        rec = fetch_clean(url)
        docs = build_docs(rec, source="msutexas")
        for d in docs:
            ids.append(f"{url}:::{d['chunk_id']}")
            texts.append(d["text"])
            metas.append({"url": d["url"], "title": d["title"], "chunk_id": d["chunk_id"]})

    collection.upsert(documents=texts, metadatas=metas, ids=ids)
    print(f"Indexed {len(ids)} chunks from {len(urls)} URLs into {CHROMA_DIR}")

if __name__ == "__main__":
    build_index()
