from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv

from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from langchain_community.document_loaders import (
    WebBaseLoader,
    DirectoryLoader,
    PyPDFLoader,
    TextLoader,
)

from utils import basic_clean

load_dotenv()

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
SEED_FILE = DATA_DIR / "seed_urls.txt"
VSTORE_DIR = Path("vectorstore/faiss_index")

EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

def load_web_docs(seed_file: Path) -> list[Document]:
    urls = []
    
    # Load from main seed file
    if seed_file.exists():
        urls = [u.strip() for u in seed_file.read_text().splitlines() 
                if u.strip() and not u.strip().startswith("#")]
    
    # Load from additional sources file if exists
    additional_file = DATA_DIR / "additional_sources.txt"
    if additional_file.exists():
        additional_urls = [u.strip() for u in additional_file.read_text().splitlines() 
                          if u.strip() and not u.strip().startswith("#")]
        urls.extend(additional_urls)
    
    if not urls:
        print("[ingest] No URLs in seed files – skipping web load.")
        return []
    
    # Remove duplicates
    urls = list(set(urls))
    print(f"[ingest] Loading {len(urls)} unique URLs...")
    
    loader = WebBaseLoader(urls)
    docs = loader.load()
    
    # Clean content
    for d in docs:
        d.page_content = basic_clean(d.page_content)
    
    print(f"[ingest] Successfully loaded {len(docs)} web docs.")
    return docs

def load_local_docs(raw_dir: Path):
    docs = []
    if not raw_dir.exists():
        return docs
    pdf_loader = DirectoryLoader(str(raw_dir), glob="**/*.pdf", loader_cls=PyPDFLoader)
    docs.extend(pdf_loader.load())
    txt_loader = DirectoryLoader(str(raw_dir), glob="**/*.txt", loader_cls=TextLoader)
    docs.extend(txt_loader.load())
    for d in docs:
        d.page_content = basic_clean(d.page_content)
    if docs:
        print(f"[ingest] Loaded {len(docs)} local docs from {raw_dir}.")
    return docs

def chunk_docs(docs, chunk_size=1200, chunk_overlap=200):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = splitter.split_documents(docs)
    print(f"[ingest] Chunked into {len(chunks)} passages.")
    return chunks

def build_faiss(chunks):
    embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
    vs = FAISS.from_documents(chunks, embeddings)
    VSTORE_DIR.mkdir(parents=True, exist_ok=True)
    vs.save_local(str(VSTORE_DIR))
    print(f"[ingest] Saved FAISS index to {VSTORE_DIR}.")

if __name__ == "__main__":
    web_docs = load_web_docs(SEED_FILE)
    local_docs = load_local_docs(RAW_DIR)
    all_docs = web_docs + local_docs
    if not all_docs:
        print("[ingest] No documents found. Add URLs to data/seed_urls.txt or files under data/raw/")
        raise SystemExit(0)
    chunks = chunk_docs(all_docs)
    build_faiss(chunks)
    print("[ingest] Done.")
