# core/indexer.py
import os
from loguru import logger
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

from core.ingest import fetch_all
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
        docs = fetch_all(url)
        for d in docs:
            for doc in build_docs(d, source="msutexas"):
                ids.append(doc["id"])
                texts.append(doc["text"])
                metas.append(doc["meta"])

    collection.upsert(documents=texts, metadatas=metas, ids=ids)
    logger.info(f"Indexed {len(ids)} chunks from {len(urls)} seed URLs into {CHROMA_DIR}")

if __name__ == "__main__":
    build_index()
