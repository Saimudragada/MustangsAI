# app/main.py
import os
import re
from typing import List, Dict, Tuple

import streamlit as st
from dotenv import load_dotenv
import requests

import chromadb
from chromadb.utils import embedding_functions

# ---------- Load env ----------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
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
c1, c2 = st.columns([1, 6], vertical_alignment="center")
with c1:
    st.image("assets/logo.png", width=72)
with c2:
    st.markdown(
        f"<div class='msu-header'><div class='brand-title'>MustangsAI</div>"
        f"<div class='badge'>Hello, Mustang!</div></div>",
        unsafe_allow_html=True,
    )
st.caption(
    "Ask about admissions, calendars, tuition, CPT/OPT, housing, library hours, IT, Title IX, and careers. "
    "Answers are from official MSU Texas pages."
)

# ---------- Sidebar ----------
with st.sidebar:
    st.subheader("Settings")
    debug = st.checkbox("Show retrieval debug", value=False)
    if not GEMINI_API_KEY:
        st.warning("Add GEMINI_API_KEY in your .env file.", icon="⚠️")

# ---------- Connect to Chroma ----------
client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection(
    name="msu_docs",
    metadata={"hnsw:space": "cosine"},
    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL
    ),
)

# ---------- Retrieval ----------
def retrieve(query: str, k: int = 8) -> Tuple[List[Dict], str]:
    """Query Chroma. Returns (hits, error_message_or_empty)."""
    try:
        res = collection.query(
            query_texts=[query],
            n_results=k,
            include=["metadatas", "documents", "distances"],
        )
        if not res["documents"]:
            return [], ""
        hits: List[Dict] = []
        for doc, meta, dist in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
            hits.append({
                "text": doc,
                "url": meta["url"],
                "title": meta.get("title", ""),
                "score": 1 - float(dist),
            })
        return hits, ""
    except Exception as e:
        return [], f"Retrieval error: {e}"

# ---------- Helpers ----------
def looks_like_hours_without_times(ctx: List[Dict]) -> bool:
    """
    Library Hours page often loads times via JS, so our HTML may lack actual times.
    If content mentions library/hours but no 'am/pm' times, we link out instead of saying 'Sorry'.
    """
    blob = " ".join((c.get("title","") + " " + c.get("text","")) for c in ctx).lower()
    mentions_hours = ("library" in blob and "hour" in blob)
    has_time = any(re.search(r"\b\d{1,2}(:\d{2})?\s*(am|pm)\b", c.get("text",""), re.I) for c in ctx)
    return mentions_hours and not has_time


def build_prompt(question: str, ctx: List[Dict]) -> str:
    # Do not include citations in the LLM output; we append them ourselves.
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

# ---------- Gemini API Answer ----------
def answer_with_llm(question: str, ctx: List[Dict]) -> str:
    """Calls Google Gemini API for the answer."""
    if not GEMINI_API_KEY:
        return "Sorry, Gemini API key is missing."
    prompt = build_prompt(question, ctx)
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    try:
        resp = requests.post(endpoint, headers=headers, json=data)
        resp.raise_for_status()
        response_json = resp.json()
        # Parse Gemini's response
        answer = response_json['candidates'][0]['content']['parts'][0]['text']
        return answer
    except Exception as e:
        return f"Gemini API error: {e}"

# ---------- Chat history ----------
if "history" not in st.session_state:
    st.session_state.history = []

for m in st.session_state.history:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ---------- Bottom input (single instance with a unique key) ----------
user_msg = st.chat_input(
    "Type your question… (e.g., When is the last day to drop a class?)",
    key="main_input"
)

if user_msg:
    # show user message
    st.session_state.history.append({"role": "user", "content": user_msg})
    with st.chat_message("user"):
        st.markdown(user_msg)

    # assistant message
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # 1) retrieve (ctx + rerr MUST be defined in this scope)
            ctx, rerr = retrieve(user_msg, k=8)
            # optional debug
            if debug:
                with st.expander("Retrieval debug"):
                    if rerr:
                        st.error(rerr)
                    for c in ctx:
                        st.write(f"{c['score']:.3f} — {c['title'] or c['url']}")
            # 2) choose reply
            reply = "Sorry, the information is not available."
            if rerr:
                # Retrieval error occurred; keep default reply but show error in debug expander.
                pass
            elif not ctx:
                # No matches; keep default reply.
                pass
            elif looks_like_hours_without_times(ctx):
                # Friendly fallback when we have the Library Hours page but no literal times.
                cites = "\n".join(f"- [{c.get('title') or c['url']}]({c['url']})" for c in ctx[:3])
                reply = (
                    "Library hours vary by date. Please check the Moffett Library Hours page below.\n\n"
                    "**Citations:**\n" + cites
                )
            elif not GEMINI_API_KEY:
                # Missing API key; keep default reply.
                pass
            else:
                # Try LLM answer with citations
                try:
                    body = answer_with_llm(user_msg, ctx)
                    cites = "\n".join(f"- [{c.get('title') or c['url']}]({c['url']})" for c in ctx[:3])
                    reply = f"{body}\n\n**Citations:**\n{cites}"
                except Exception as e:
                    if debug:
                        st.error(f"LLM error: {e}")
                    # keep default reply
            st.markdown(reply)
            st.session_state.history.append({"role": "assistant", "content": reply})
