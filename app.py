from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
from datetime import datetime
import base64

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.schema import Document
from langchain.prompts import ChatPromptTemplate

from utils import truncate
from rate_limiter import (
    check_global_limit, 
    increment_usage,
    get_usage_display
)

load_dotenv()

# --- Config ---
st.set_page_config(
    page_title="MustangsAI - MSU Texas Assistant",
    page_icon="🐴",
    layout="wide",
    initial_sidebar_state="collapsed"
)

VSTORE_DIR = Path("vectorstore/faiss_index")
EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

# Load mascot image
def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

MASCOT_IMAGE = get_image_base64("assets/Mustangs_mascot.png")

# --- CSS ---
st.markdown("""
<style>
    :root {
        --msu-maroon: #660000;
        --msu-gold: #FFD700;
        --msu-dark: #4A0000;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    
    /* Welcome Screen */
    .welcome-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 70vh;
        padding: 2rem;
    }
    
    .welcome-mascot {
        width: 120px;
        height: 120px;
        margin-bottom: 2rem;
        border-radius: 50%;
        border: 4px solid var(--msu-gold);
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
    
    .welcome-card {
        background: white;
        border-radius: 20px;
        padding: 3rem;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        text-align: center;
        max-width: 600px;
        margin-bottom: 2rem;
    }
    
    .welcome-title {
        font-size: 2.5rem;
        color: #333;
        margin-bottom: 1rem;
    }
    
    .welcome-title strong {
        color: var(--msu-maroon);
    }
    
    .welcome-subtitle {
        font-size: 1.2rem;
        color: #666;
    }
    
    /* Topic Buttons */
    .stButton button {
        background: white !important;
        border: 2px solid var(--msu-maroon) !important;
        border-radius: 25px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        color: var(--msu-maroon) !important;
        transition: all 0.3s ease !important;
        white-space: nowrap !important;
    }
    
    .stButton button:hover {
        background: var(--msu-maroon) !important;
        color: white !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
    }
    
    /* Chat Interface */
    .sidebar-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .sidebar-logo {
        width: 40px;
        height: 40px;
        border-radius: 50%;
    }
    
    .sidebar-title {
        font-size: 1.25rem;
        font-weight: 700;
        color: #333;
    }
    
    .stChatMessage {
        border-radius: 15px;
        margin-bottom: 1rem;
    }
    
    .disclaimer {
        text-align: center;
        color: #999;
        font-size: 0.85rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Vector Store ---
@st.cache_resource(show_spinner=False)
def get_vectorstore():
    if not VSTORE_DIR.exists():
        raise RuntimeError("Vector store not found. Run `python ingest.py` first.")
    embeddings = OpenAIEmbeddings(model=EMBED_MODEL)
    vs = FAISS.load_local(str(VSTORE_DIR), embeddings, allow_dangerous_deserialization=True)
    return vs

def retrieve(query: str, k: int = 6) -> list[Document]:
    vs = get_vectorstore()
    docs = vs.similarity_search(query, k=k)
    return docs

SYSTEM_PROMPT = (
    "You are MustangsAI, the official AI assistant for MSU Texas (Midwestern State University)."
    " You are helpful, friendly, professional, and enthusiastic about MSU Texas."
    " Answer questions using ONLY the provided context from official MSU sources."
    " If you see names, titles, emails, or phone numbers in the context, share them clearly."
    " Be specific with dates and deadlines. Keep responses clear and student-friendly."
)

PROMPT_TMPL = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "Question: {question}\n\nContext:\n{context}\n\nAnswer:"),
])

def is_msu_related(question: str) -> bool:
    """Check if question is related to MSU Texas"""
    # Keywords that indicate MSU-related questions
    msu_keywords = [
        'msu', 'midwestern state', 'mustang', 'admissions', 'enrollment',
        'campus', 'dorm', 'housing', 'registrar', 'financial aid', 'scholarship',
        'course', 'class', 'degree', 'program', 'major', 'faculty', 'professor',
        'library', 'student', 'tuition', 'fee', 'wichita falls', 'texas',
        'graduation', 'transcript', 'gpa', 'deadline', 'semester', 'academic',
        'department', 'college', 'university', 'residence hall', 'dining',
        'parking', 'athletics', 'sports', 'event', 'organization', 'club'
    ]

    question_lower = question.lower()

    # Check if question contains any MSU-related keywords
    if any(keyword in question_lower for keyword in msu_keywords):
        return True

    # Check for generic university questions (could be MSU-related)
    generic_uni_terms = ['apply', 'application', 'enroll', 'transfer', 'graduate']
    if any(term in question_lower for term in generic_uni_terms):
        # Use LLM to classify if ambiguous
        return True

    # Reject clearly off-topic questions
    off_topic_keywords = [
        'weather', 'news', 'recipe', 'movie', 'music', 'sports score',
        'stock', 'celebrity', 'politics', 'covid', 'world cup', 'what is the capital',
        'who is the president', 'translate', 'calculate', 'solve', 'python code'
    ]

    if any(keyword in question_lower for keyword in off_topic_keywords):
        return False

    return True

def answer_with_citations(question: str, docs: list[Document]) -> tuple[str, list[dict]]:
    # Check if question is MSU-related
    if not is_msu_related(question):
        rejection_msg = ("Sorry, I can only answer questions about MSU Texas. "
                        "Please ask me about admissions, housing, academics, or campus life.")
        return rejection_msg, []

    context = "\n\n".join([d.page_content for d in docs])
    llm = ChatOpenAI(model=CHAT_MODEL, temperature=0)
    prompt = PROMPT_TMPL.format_messages(question=question, context=context)
    resp = llm.invoke(prompt)

    cites = []
    for d in docs:
        meta = d.metadata or {}
        src = meta.get("source") or meta.get("file_path") or "Unknown source"
        cites.append({
            "source": src,
            "preview": truncate(d.page_content, 220),
        })
    return resp.content.strip(), cites

# --- Session State ---
if "chat_started" not in st.session_state:
    st.session_state.chat_started = False
if "history" not in st.session_state:
    st.session_state.history = []

# --- WELCOME SCREEN ---
if not st.session_state.chat_started:
    mascot_img = f'<img src="data:image/png;base64,{MASCOT_IMAGE}" class="welcome-mascot">' if MASCOT_IMAGE else '<div style="font-size: 80px;">🐴</div>'
    
    st.markdown(f"""
    <div class="welcome-container">
        {mascot_img}
        <div class="welcome-card">
            <div class="welcome-title">Hi, I'm <strong>MustangsAI.</strong></div>
            <div class="welcome-subtitle">Ask me anything about MSU Texas!</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Topic buttons
    st.markdown("""
    <div style="text-align: center; margin: 2rem 0 1.5rem 0;">
        <p style="color: #666; font-size: 1.1rem; margin-bottom: 1.5rem;">Most Searched Topics</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Row 1: All 5 buttons
    col1, col2, col3, col4, col5 = st.columns(5)
    
    topics = [
        ("Admissions", "What are the admission requirements for MSU Texas?"),
        ("Financial Aid", "How do I apply for financial aid?"),
        ("Campus Events", "What events are happening on campus?"),
        ("Registrar", "What is the deadline for dropping classes?"),
        ("Housing", "What are the housing requirements?")
    ]
    
    cols = [col1, col2, col3, col4, col5]
    
    for i, (topic_name, question) in enumerate(topics):
        with cols[i]:
            if st.button(topic_name, key=f"topic_{i}", use_container_width=True):
                allowed, error_msg = check_global_limit()
                if not allowed:
                    st.error(error_msg)
                    st.stop()
                st.session_state.chat_started = True
                st.session_state.first_query = question
                st.rerun()
    
    # Row 2: Library (centered)
    col_left, col_center, col_right = st.columns([2, 1, 2])
    with col_center:
        if st.button("Library", key="topic_library", use_container_width=True):
            allowed, error_msg = check_global_limit()
            if not allowed:
                st.error(error_msg)
                st.stop()
            st.session_state.chat_started = True
            st.session_state.first_query = "Tell me about the MSU Texas library."
            st.rerun()
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Input
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        welcome_query = st.chat_input("Type your question...", key="welcome_input")
        
        if welcome_query:
            allowed, error_msg = check_global_limit()
            if not allowed:
                st.error(error_msg)
                st.stop()
            st.session_state.chat_started = True
            st.session_state.first_query = welcome_query
            st.rerun()
    
    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 4rem; padding: 2rem; color: #999;">
        <p style="font-size: 0.9rem;">Built by a Mustang</p>
        <p style="font-size: 1.1rem; color: var(--msu-maroon); font-weight: 600; margin: 0.5rem 0;">Sai Mudragada</p>
        <p style="font-size: 0.85rem;">Powered by AI • MSU Texas</p>
    </div>
    """, unsafe_allow_html=True)

# --- CHAT INTERFACE ---
else:
    col_sidebar, col_main = st.columns([1, 4])
    
    with col_sidebar:
        mascot_small = f'<img src="data:image/png;base64,{MASCOT_IMAGE}" class="sidebar-logo">' if MASCOT_IMAGE else '🐴'
        
        st.markdown(f"""
        <div class="sidebar-header">
            {mascot_small}
            <div class="sidebar-title">MustangsAI</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Quick Topics")
        
        if st.button("📚 Admissions", key="nav_admissions", use_container_width=True):
            st.session_state.nav_query = "Tell me about admissions to MSU Texas."
            st.rerun()
        
        if st.button("📖 Courses", key="nav_courses", use_container_width=True):
            st.session_state.nav_query = "What courses and programs are available?"
            st.rerun()
        
        if st.button("📅 Events", key="nav_events", use_container_width=True):
            st.session_state.nav_query = "What events are happening at MSU Texas?"
            st.rerun()
        
        if st.button("📝 Registrar", key="nav_registrar", use_container_width=True):
            st.session_state.nav_query = "Tell me about registration and academic records."
            st.rerun()
        
        if st.button("💰 Financial Aid", key="nav_finaid", use_container_width=True):
            st.session_state.nav_query = "How does financial aid work at MSU Texas?"
            st.rerun()
        
        if st.button("🏛️ Campus Life", key="nav_campus", use_container_width=True):
            st.session_state.nav_query = "Tell me about campus life and student organizations."
            st.rerun()
        
        st.markdown("<br>" * 10, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; padding: 1rem;">
            <small style="color: #999;">Built by<br><strong>Sai Mudragada</strong></small>
        </div>
        """, unsafe_allow_html=True)
    
    with col_main:
        # Process first query
        if hasattr(st.session_state, 'first_query') and st.session_state.first_query:
            q = st.session_state.first_query
            del st.session_state.first_query
            
            with st.spinner("Searching..."):
                docs = retrieve(q, k=6)
                ans, cites = answer_with_citations(q, docs)
                increment_usage()
            
            st.session_state.history.append((q, ans, cites))
        
        # Handle sidebar navigation
        if hasattr(st.session_state, 'nav_query') and st.session_state.nav_query:
            q = st.session_state.nav_query
            del st.session_state.nav_query
            
            allowed, error_msg = check_global_limit()
            if not allowed:
                st.warning("Query limit reached.")
                st.stop()
            
            with st.spinner("Searching..."):
                docs = retrieve(q, k=6)
                ans, cites = answer_with_citations(q, docs)
                increment_usage()
            
            st.session_state.history.append((q, ans, cites))
            st.rerun()
        
        # Welcome message
        if len(st.session_state.history) == 0:
            st.markdown("""
            <div style="background: white; border-radius: 15px; padding: 1.5rem; margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.08); max-width: 600px;">
                <p><strong>Welcome to MustangsAI!</strong> I'm here to help you with any questions 
                you have about Midwestern State University Texas. How can I assist you today?</p>
            </div>
            """, unsafe_allow_html=True)
            
            cols = st.columns(2)
            suggestions = [
                "Tell me about the admission requirements.",
                "What courses are available?",
                "When do events happen?",
                "Financial aid information"
            ]
            
            for i, suggestion in enumerate(suggestions):
                col = cols[i % 2]
                with col:
                    if st.button(suggestion, key=f"suggest_{i}"):
                        st.session_state.suggestion_clicked = suggestion
                        st.rerun()
        
        # Handle suggestions
        if hasattr(st.session_state, 'suggestion_clicked'):
            q = st.session_state.suggestion_clicked
            del st.session_state.suggestion_clicked
            
            allowed, error_msg = check_global_limit()
            if not allowed:
                st.warning("Query limit reached.")
                st.stop()
            
            with st.spinner("Searching..."):
                docs = retrieve(q, k=6)
                ans, cites = answer_with_citations(q, docs)
                increment_usage()
            
            st.session_state.history.append((q, ans, cites))
            st.rerun()
        
        # Display history
        for idx, (u, a, cites) in enumerate(st.session_state.history):
            with st.chat_message("user"):
                st.write(u)
            
            with st.chat_message("assistant"):
                st.write(a)
                
                # Feedback buttons
                col1, col2, col3 = st.columns([0.5, 0.5, 11])
                with col1:
                    if st.button("👍", key=f"up_{idx}", help="Helpful"):
                        from feedback import add_feedback
                        add_feedback(u, a, 'positive')
                        st.success("Thanks!")
                with col2:
                    if st.button("👎", key=f"down_{idx}", help="Not helpful"):
                        from feedback import add_feedback
                        add_feedback(u, a, 'negative')
                        st.info("We'll improve!")
                
                if cites:
                    with st.expander("📚 View Sources", expanded=False):
                        for i, c in enumerate(cites, 1):
                            st.markdown(f"**Source {i}:** [{c['source']}]({c['source']})")
                            st.caption(c['preview'])
                            if i < len(cites):
                                st.markdown("---")
        
        # Footer disclaimer BEFORE chat input
        st.markdown("""
        <div class="disclaimer">
            MustangsAI can make mistakes. Consider checking important information.
        </div>
        """, unsafe_allow_html=True)
        
        # Chat input
        q = st.chat_input("Ask me anything about MSU Texas...")
        
        if q:
            allowed, error_msg = check_global_limit()
            if not allowed:
                st.error(error_msg)
                st.info("Want unlimited access? Email saimudragada1@gmail.com")
                st.stop()
            
            with st.chat_message("user"):
                st.write(q)
            
            with st.spinner("Searching..."):
                docs = retrieve(q, k=6)
                ans, cites = answer_with_citations(q, docs)
                increment_usage()
            
            st.session_state.history.append((q, ans, cites))
            
            with st.chat_message("assistant"):
                st.write(ans)
                if cites:
                    with st.expander("📚 View Sources", expanded=False):
                        for i, c in enumerate(cites, 1):
                            st.markdown(f"**Source {i}:** [{c['source']}]({c['source']})")
                            st.caption(c['preview'])
                            if i < len(cites):
                                st.markdown("---")