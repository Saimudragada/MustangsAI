import os
from typing import List, Dict

import streamlit as st
from dotenv import load_dotenv

import chromadb
from chromadb.utils import embedding_functions
from openai import OpenAI

# ---------- Load env ----------
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHROMA_DIR = os.getenv("CHROMA_DIR", "./data/chroma")
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

# ---------- UI theming ----------
MAROON = "#7A0019"
GOLD = "#FFC72C"
DARK = "#1f1f1f"

st.set_page_config(page_title="MustangsAI", page_icon="🐎", layout="wide")
st.markdown(f"""
<style>
  .stApp {{ background: #fff; color: {DARK}; }}
  .msu-header {{ display:flex; align-items:center; gap:14px; padding:10px 0; border-bottom: 3px solid {GOLD}; }}
  .brand-title {{ color:{MAROON}; font-weight:800; font-size:28px; }}
  .badge {{ background:{GOLD}; color:{MAROON}; padding:3px 8px; border-radius:10px; font-weight:700; }}
  .source a {{ color:{MAROON}; text-decoration: underline; }}
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
c1, c2 = st.columns([1,6], vertical_alignment="center")
with c1:
    st.image("assets/logo.png", width=72)
with c2:
    st.markdown(
        f"<div class='msu-header'><div class='brand-title'>MustangsAI</div>"
        f"<div class='badge'>Hello, Mustang!</div></div>", unsafe_allow_html=True
    )
st.caption("Ask about admissions, calendars, tuition, CPT/OPT, housing, library hours, IT, Title IX, and careers. Answers are from official MSU Texas pages.")

# ---------- Sidebar settings ----------
with st.sidebar:
    st.subheader("Settings")
    debug = st.checkbox("Show retrieval debug", value=False)
    if not OPENAI_API_KEY:
        st.warning("Add OPENAI_API_KEY in your .env file.", icon="⚠️")

# ---------- Connect to Chroma ----------
client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection(
    name="msu_docs",
    metadata={"hnsw:space": "cosine"},
    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL
    ),
)

def retrieve(query: str, k: int = 8) -> List[Dict]:
    res = collection.query(
        query_texts=[query],
        n_results=k,
        include=["metadatas", "documents", "distances"]
    )
    if not res["documents"]:
        return []
    hits: List[Dict] = []
    for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        hits.append({
            "text": doc,
            "url": meta["url"],
            "title": meta.get("title", ""),
            "score": 1 - float(dist)  # cosine -> similarity
        })
    return hits

def build_prompt(question: str, ctx: List[Dict]) -> str:
    # We now tell the model NOT to add its own citations.
    snippets = "\n\n---\n\n".join([c["text"] for c in ctx])
    return f"""You are MustangsAI, an assistant for Midwestern State University (MSU Texas).
Answer using ONLY the Context below. If the answer is not in the context, respond exactly:
"Sorry, the information is not available."

Write concise bullet points when appropriate.
Do NOT include any citations or links in your answer body; citations will be appended separately.

Question: {question}

Context:
{snippets}
"""


def answer_with_llm(question: str, ctx: List[Dict]) -> str:
    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = build_prompt(question, ctx)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.2,
        messages=[
            {"role": "system", "content": "You answer strictly from provided context and abstain when unsure."},
            {"role": "user", "content": prompt}
        ]
    )
    return resp.choices[0].message.content

# ---------- Chat history (for chat UI) ----------
if "history" not in st.session_state:
    st.session_state.history = []  # list[{"role": "user"/"assistant", "content": str}]

# Render previous messages
for m in st.session_state.history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ---------- Bottom input (like ChatGPT) ----------
user_msg = st.chat_input("Type your question… (e.g., When is the last day to drop a class?)")

if user_msg:
    # Show user's message
    st.session_state.history.append({"role": "user", "content": user_msg})
    with st.chat_message("user"):
        st.markdown(user_msg)

    # Assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            ctx = retrieve(user_msg, k=8)
            best = max([c["score"] for c in ctx], default=0.0)

            if debug and ctx:
                with st.expander("Retrieval debug"):
                    for c in ctx:
                        st.write(f"{c['score']:.3f} — {c['title'] or c['url']}")

            if not ctx or best < 0.10:
                reply = "Sorry, the information is not available."
            else:
                try:
                    reply = answer_with_llm(user_msg, ctx)
                    # Append citations to the reply
                    cites = "\n".join(
                        [f"- [{c['title'] or c['url']}]({c['url']})" for c in ctx[:3]]
                    )
                    reply = reply + "\n\n**Citations:**\n" + cites
                except Exception:
                    reply = "Sorry, the information is not available."

        st.markdown(reply)
        st.session_state.history.append({"role": "assistant", "content": reply})
