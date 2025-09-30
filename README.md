# MustangAI — MSU Texas (RAG MVP)

A lightweight RAG chatbot that answers from a curated set of MSU Housing + 2024–25 Catalog pages. Streamlit UI + LangChain + FAISS.

## 🧰 Tech
- Python 3.10+
- Streamlit (UI)
- LangChain, langchain-openai
- FAISS (local vector store)

## 🔧 Setup

```bash
# 1) Create venv
python3 -m venv .venv
source .venv/bin/activate

# 2) Install deps
pip install --upgrade pip
pip install -r requirements.txt
pip install langchain-openai   # sometimes pip misses this

# 3) Env vars
cp .env.example .env
# edit .env and set OPENAI_API_KEY=sk-...

# 4) Ingest sources (build vector DB)
python ingest.py

# 5) Run app
python -m streamlit run app.py
# if 8501 busy: python -m streamlit run app.py --server.port 8502
