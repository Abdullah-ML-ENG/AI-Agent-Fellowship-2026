import streamlit as st
import os
import json
from datetime import datetime
import pandas as pd

# Set page configurations first
st.set_page_config(
    page_title="Enterprise Document Intelligence Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Imports
from auth import show_login_sidebar, is_authenticated, get_current_user, check_permission
from document_processor import process_document
from vector_store import VectorStoreManager
from chat_engine import ChatEngine
from utils import generate_summary, generate_suggested_questions, estimate_tokens

# ----------------------------------------------------
# Session State Initialization
# ----------------------------------------------------
if "documents" not in st.session_state:
    st.session_state.documents = []  # Metadata & summary
if "processed_chunks" not in st.session_state:
    st.session_state.processed_chunks = []  # Raw chunks database cache
if "messages" not in st.session_state:
    st.session_state.messages = []  # Chat history
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0
if "total_cost" not in st.session_state:
    st.session_state.total_cost = 0.0
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Light"

def change_theme():
    st.session_state.theme_mode = st.session_state.temp_theme_mode

# Initialize default keys
if "openai_key" not in st.session_state:
    st.session_state.openai_key = ""
if "gemini_key" not in st.session_state:
    st.session_state.gemini_key = ""
if "groq_key" not in st.session_state:
    st.session_state.groq_key = ""

# Load environment variables if available
from dotenv import load_dotenv
load_dotenv()

default_openai = os.getenv("OPENAI_API_KEY", "")
default_gemini = os.getenv("GOOGLE_API_KEY", "")
default_groq = os.getenv("GROQ_API_KEY", "")

# ----------------------------------------------------
# Premium Styling (Custom CSS based on theme selection)
# ----------------------------------------------------
theme_style = ""
current_theme = st.session_state.get("theme_mode", "Light")

if current_theme == "Dark":
    theme_style = """
    <style>
        /* Redefine Streamlit's Core Design Tokens globally for Dark Mode */
        :root, .stApp, [data-testid="stAppViewContainer"] {
            --primary-color: #00f0ff !important;
            --background-color: #0d0f14 !important;
            --secondary-background-color: #1a1f2c !important;
            --text-color: #ffffff !important;
        }
        
        /* Force styling using variables */
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
            background-color: var(--background-color) !important;
            color: var(--text-color) !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: var(--secondary-background-color) !important;
        }
        
        /* Header bar */
        [data-testid="stHeader"] {
            background-color: transparent !important;
        }
        
        /* High contrast headers, labels, and text */
        h1, h2, h3, h4, h5, h6, p, li, label, .stMarkdown {
            color: #ffffff !important;
        }
        [data-testid="stWidgetLabel"] p {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        
        /* Style the chat input box for Dark Mode */
        div[data-testid="stChatInput"] {
            background-color: transparent !important;
        }
        div[data-testid="stChatInput"] textarea {
            background-color: #1a1f2c !important;
            color: #ffffff !important;
            border: 1px solid #374151 !important;
        }
        
        /* High contrast buttons in Dark Mode */
        button[data-testid^="stBaseButton"], div.stButton > button {
            background-color: #1a1f2c !important;
            color: #00f0ff !important;
            border: 2px solid #00f0ff !important;
            font-weight: 700 !important;
            border-radius: 6px !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
            transition: all 0.2s ease-in-out !important;
        }
        button[data-testid^="stBaseButton"]:hover, div.stButton > button:hover {
            background-color: #00f0ff !important;
            color: #0d0f14 !important;
            border-color: #00f0ff !important;
            box-shadow: 0 0 10px rgba(0, 240, 255, 0.5) !important;
        }
        /* Make button labels inherit colors */
        button[data-testid^="stBaseButton"] p, button[data-testid^="stBaseButton"] span, div.stButton > button p, div.stButton > button span {
            color: inherit !important;
            font-weight: 700 !important;
        }
        
        /* Metric cards */
        .metric-card {
            background-color: var(--secondary-background-color);
            border: 1px solid #374151;
            padding: 1.5rem;
            border-radius: 0.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            text-align: center;
            margin-bottom: 1rem;
        }
        .metric-title {
            color: #9ca3af !important;
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }
        .metric-value {
            color: var(--primary-color) !important;
            font-size: 1.875rem;
            font-weight: 700;
        }
        
        /* Chat bubble styles */
        .chat-bubble {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: flex-start;
        }
        .user-bubble {
            background-color: #2e3e56;
            border: 1px solid #4a5c78;
            color: #ffffff !important;
        }
        .assistant-bubble {
            background-color: var(--secondary-background-color);
            border: 1px solid #374151;
            color: #ffffff !important;
        }
        .chat-avatar {
            font-size: 1.5rem;
            margin-right: 0.8rem;
        }
        
        /* Citations card */
        .citation-container {
            margin-top: 0.5rem;
            padding: 0.5rem;
            background-color: #111827;
            border-left: 3px solid var(--primary-color);
            font-size: 0.85rem;
            border-radius: 0.25rem;
            color: #ffffff !important;
        }
        
        /* Top app banner */
        .app-banner {
            background: linear-gradient(135deg, #1e3a8a 0%, #0d0f14 100%);
            padding: 2rem;
            border-radius: 0.75rem;
            border: 2px solid #00f0ff;
            margin-bottom: 2rem;
            text-align: center;
            box-shadow: 0 0 15px rgba(0, 240, 255, 0.2);
        }
        .app-banner h1 {
            margin: 0;
            color: var(--primary-color) !important;
            font-size: 2.25rem;
            font-weight: 800;
        }
        .app-banner p {
            margin-top: 0.5rem;
            color: #e5e7eb !important;
            font-size: 1.125rem;
        }
    </style>
    """
else:
    theme_style = """
    <style>
        /* Redefine Streamlit's Core Design Tokens globally for Light Mode */
        :root, .stApp, [data-testid="stAppViewContainer"] {
            --primary-color: #1e3a8a !important;
            --background-color: #ffffff !important;
            --secondary-background-color: #f3f4f6 !important;
            --text-color: #1f2937 !important;
        }
        
        /* Force styling using variables */
        .stApp, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
            background-color: var(--background-color) !important;
            color: var(--text-color) !important;
        }
        
        [data-testid="stSidebar"] {
            background-color: var(--secondary-background-color) !important;
        }
        
        /* Header bar */
        [data-testid="stHeader"] {
            background-color: transparent !important;
        }
        
        /* High contrast headers, labels, and text */
        h1, h2, h3, h4, h5, h6, p, li, label, .stMarkdown {
            color: #1f2937 !important;
        }
        [data-testid="stWidgetLabel"] p {
            color: #1f2937 !important;
            font-weight: 600 !important;
        }
        
        /* Style the chat input box for Light Mode */
        div[data-testid="stChatInput"] textarea {
            background-color: #ffffff !important;
            color: #1f2937 !important;
            border: 1px solid #cbd5e1 !important;
        }
        
        /* High contrast buttons in Light Mode */
        button[data-testid^="stBaseButton"], div.stButton > button {
            background-color: #ffffff !important;
            color: #1e3a8a !important;
            border: 2px solid #1e3a8a !important;
            font-weight: 700 !important;
            border-radius: 6px !important;
            transition: all 0.2s ease-in-out !important;
        }
        button[data-testid^="stBaseButton"]:hover, div.stButton > button:hover {
            background-color: #1e3a8a !important;
            color: #ffffff !important;
            border-color: #1e3a8a !important;
        }
        /* Make button labels inherit colors */
        button[data-testid^="stBaseButton"] p, button[data-testid^="stBaseButton"] span, div.stButton > button p, div.stButton > button span {
            color: inherit !important;
            font-weight: 700 !important;
        }
        
        /* Metric cards */
        .metric-card {
            background-color: #f9fafb;
            border: 1px solid #e5e7eb;
            padding: 1.5rem;
            border-radius: 0.5rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            text-align: center;
            margin-bottom: 1rem;
        }
        .metric-title {
            color: #4b5563 !important;
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
        }
        .metric-value {
            color: var(--primary-color) !important;
            font-size: 1.875rem;
            font-weight: 700;
        }
        
        /* Chat bubble styles */
        .chat-bubble {
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            display: flex;
            align-items: flex-start;
        }
        .user-bubble {
            background-color: #eff6ff;
            border: 1px solid #bfdbfe;
            color: #1e293b !important;
        }
        .assistant-bubble {
            background-color: var(--secondary-background-color);
            border: 1px solid #e5e7eb;
            color: #1e293b !important;
        }
        .chat-avatar {
            font-size: 1.5rem;
            margin-right: 0.8rem;
        }
        
        /* Citations card */
        .citation-container {
            margin-top: 0.5rem;
            padding: 0.5rem;
            background-color: #f9fafb;
            border-left: 3px solid var(--primary-color);
            font-size: 0.85rem;
            border-radius: 0.25rem;
            color: #374151 !important;
        }
        
        /* Top app banner */
        .app-banner {
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
            padding: 2rem;
            border-radius: 0.75rem;
            border: 1px solid #2563eb;
            margin-bottom: 2rem;
            text-align: center;
        }
        .app-banner h1 {
            margin: 0;
            color: #ffffff !important;
            font-size: 2.25rem;
            font-weight: 800;
        }
        .app-banner p {
            margin-top: 0.5rem;
            color: #e0f2fe !important;
            font-size: 1.125rem;
        }
    </style>
    """

st.markdown(theme_style, unsafe_allow_html=True)

# ----------------------------------------------------
# Main Layout Banner
# ----------------------------------------------------
st.markdown("""
<div class="app-banner">
    <h1>Enterprise Document Intelligence Platform</h1>
    <p>Context-aware cognitive intelligence platform for corporate documents & knowledge bases</p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# Sidebar Authentication & Configurations
# ----------------------------------------------------
# 1. User Authenticator
show_login_sidebar()

# Check authentication to restrict access to core interface
if not is_authenticated():
    st.warning("⚠️ Access Denied. Please sign in using the sidebar credentials to access the platform.")
    st.stop()

current_user = get_current_user()

# Theme Mode Selector in Sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("🌓 Theme Settings")
theme_mode = st.sidebar.radio(
    "Interface Mode",
    options=["Light", "Dark"],
    key="temp_theme_mode",
    index=0 if st.session_state.theme_mode == "Light" else 1,
    horizontal=True,
    on_change=change_theme,
    help="Toggle between Light and Dark interface styles."
)

# 2. API Key Inputs in Sidebar (collapsible)
with st.sidebar.expander("⚙️ API Configuration", expanded=False):
    openai_key = st.text_input(
        "OpenAI API Key", 
        value=st.session_state.openai_key or default_openai, 
        type="password",
        placeholder="sk-..."
    )
    gemini_key = st.text_input(
        "Google API Key", 
        value=st.session_state.gemini_key or default_gemini, 
        type="password",
        placeholder="AIzaSy..."
    )
    groq_key = st.text_input(
        "Groq API Key", 
        value=st.session_state.groq_key or default_groq, 
        type="password",
        placeholder="gsk_..."
    )
    
    st.session_state.openai_key = openai_key
    st.session_state.gemini_key = gemini_key
    st.session_state.groq_key = groq_key

# 3. Vector Database Selection
st.sidebar.subheader("🗄️ Storage & Model Config")

db_selection = st.sidebar.radio(
    "Vector Database",
    options=["FAISS", "ChromaDB"],
    index=0,
    help="Select the vector store engine to index documents."
)
db_type = "faiss" if db_selection == "FAISS" else "chroma"

embed_selection = st.sidebar.selectbox(
    "Embedding Provider",
    options=["Local (SentenceTransformers)", "OpenAI", "Google Gemini"],
    index=0,
    help="Select embedding engine. Local runs completely offline."
)

embed_provider_map = {
    "Local (SentenceTransformers)": "local",
    "OpenAI": "openai",
    "Google Gemini": "gemini"
}
embed_provider = embed_provider_map[embed_selection]

# Determine active API Key
active_api_key = None
if embed_provider == "openai":
    active_api_key = st.session_state.openai_key
    if not active_api_key:
        st.sidebar.error("⚠️ OpenAI API Key required for OpenAI embeddings.")
elif embed_provider == "gemini":
    active_api_key = st.session_state.gemini_key
    if not active_api_key:
        st.sidebar.error("⚠️ Google Gemini API Key required for Gemini embeddings.")

# LLM Model Provider
llm_provider = st.sidebar.selectbox(
    "LLM Provider",
    options=["Demo Mode (Simulated)", "Google Gemini", "OpenAI", "Groq"],
    index=0,
    help="Select the chat model provider. Demo mode is free and offline."
)

llm_provider_map = {
    "Demo Mode (Simulated)": "mock",
    "Google Gemini": "gemini",
    "OpenAI": "openai",
    "Groq": "groq"
}
llm_provider_type = llm_provider_map[llm_provider]

active_llm_key = None
model_name = None
if llm_provider_type == "openai":
    active_llm_key = st.session_state.openai_key
    model_name = st.sidebar.selectbox("OpenAI Model", ["gpt-4o-mini", "gpt-4o"])
    if not active_llm_key:
        st.sidebar.error("⚠️ OpenAI API Key required for Chat.")
elif llm_provider_type == "gemini":
    active_llm_key = st.session_state.gemini_key
    model_name = st.sidebar.selectbox("Gemini Model", ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash"])
    if not active_llm_key:
        st.sidebar.error("⚠️ Google Gemini API Key required for Chat.")
elif llm_provider_type == "groq":
    active_llm_key = st.session_state.groq_key
    model_name = st.sidebar.selectbox("Groq Model", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama3-8b-8192", "mixtral-8x7b-32768"])
    if not active_llm_key:
        st.sidebar.error("⚠️ Groq API Key required for Chat.")

# ----------------------------------------------------
# Vector Store Manager Synchronization
# ----------------------------------------------------
db_changed = False
if "db_type_current" not in st.session_state or st.session_state.db_type_current != db_type:
    st.session_state.db_type_current = db_type
    db_changed = True
if "embed_current" not in st.session_state or st.session_state.embed_current != embed_provider:
    st.session_state.embed_current = embed_provider
    db_changed = True
if "active_key_current" not in st.session_state or st.session_state.active_key_current != active_api_key:
    st.session_state.active_key_current = active_api_key
    db_changed = True

# Recreate manager if config changed or not initialized
if db_changed or "vector_manager" not in st.session_state:
    with st.spinner("Initializing Vector Store Engine..."):
        st.session_state.vector_manager = VectorStoreManager(
            db_type=st.session_state.db_type_current,
            embedding_provider=st.session_state.embed_current,
            api_key=st.session_state.active_key_current
        )
        # Re-index any cached chunks
        if st.session_state.processed_chunks:
            st.session_state.vector_manager.add_chunks(st.session_state.processed_chunks)

# Initialize Chat Engine
chat_engine = ChatEngine(
    provider=llm_provider_type,
    api_key=active_llm_key,
    model_name=model_name
)

# ----------------------------------------------------
# Document Upload Panel (Sidebar bottom)
# ----------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("📤 Document Upload")

# Restrict upload permission to Editor or Admin
upload_allowed = check_permission("Editor")
uploaded_files = st.sidebar.file_uploader(
    "Upload Files", 
    type=["pdf", "docx", "txt", "md"], 
    accept_multiple_files=True,
    disabled=not upload_allowed,
    help="Allowed formats: PDF, DOCX, TXT, Markdown"
)

if not upload_allowed:
    st.sidebar.warning("🔒 Upload requires Editor/Admin role.")

if upload_allowed and uploaded_files:
    new_uploads = []
    for f in uploaded_files:
        # Check if already processed to avoid duplicates
        if not any(d["name"] == f.name for d in st.session_state.documents):
            new_uploads.append(f)
            
    if new_uploads:
        with st.sidebar:
            for f in new_uploads:
                with st.spinner(f"Processing {f.name}..."):
                    file_bytes = f.read()
                    res = process_document(f.name, file_bytes)
                    
                    if res["success"]:
                        # Generate summary excerpt (use text from first few chunks)
                        full_text = "\n\n".join([c["text"] for c in res["chunks"]])
                        
                        summary = generate_summary(
                            full_text, 
                            f.name, 
                            provider=llm_provider_type, 
                            api_key=active_llm_key
                        )
                        
                        suggested_qs = generate_suggested_questions(
                            full_text,
                            f.name,
                            provider=llm_provider_type,
                            api_key=active_llm_key
                        )
                        
                        # Save metadata
                        st.session_state.documents.append({
                            "name": f.name,
                            "pages": res["pages"],
                            "chunks_count": res["chunk_count"],
                            "char_count": res["char_count"],
                            "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "summary": summary,
                            "suggested_questions": suggested_qs,
                            "full_text": full_text
                        })
                        
                        # Index chunks in vector DB
                        st.session_state.processed_chunks.extend(res["chunks"])
                        st.session_state.vector_manager.add_chunks(res["chunks"])
                        st.toast(f"Successfully processed {f.name}!", icon="✅")
                    else:
                        st.error(f"Error {f.name}: {res['error']}")
        st.rerun()

# ----------------------------------------------------
# Reset DB System Action
# ----------------------------------------------------
if st.sidebar.button("🧹 Clear All Database", use_container_width=True, disabled=not check_permission("Admin")):
    st.session_state.documents = []
    st.session_state.processed_chunks = []
    st.session_state.messages = []
    st.session_state.total_tokens = 0
    st.session_state.total_cost = 0.0
    st.session_state.vector_manager.clear_all()
    st.toast("Database and cache cleared!", icon="🧹")
    st.rerun()

# ----------------------------------------------------
# Main Workspace Navigation Tabs
# ----------------------------------------------------
tabs = st.tabs([
    "📊 Dashboard & Analytics", 
    "📁 Document Library", 
    "💬 Conversational Assistant", 
    "⚖️ Compare Documents"
])

# ====================================================
# TAB 1: DASHBOARD & ANALYTICS
# ====================================================
with tabs[0]:
    st.subheader("📈 System Control Room & Analytics")
    
    # 4 Column KPI Indicators
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    
    total_docs = len(st.session_state.documents)
    total_chunks = len(st.session_state.processed_chunks)
    total_chars = sum(d["char_count"] for d in st.session_state.documents)
    est_total_tokens = sum(estimate_tokens(d["full_text"]) for d in st.session_state.documents)
    
    with kpi1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">TOTAL UPLOADED DOCUMENTS</div>
            <div class="metric-value">{total_docs}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">TOTAL PARSED TEXT CHUNKS</div>
            <div class="metric-value">{total_chunks}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">ESTIMATED TOTAL TOKENS</div>
            <div class="metric-value">{est_total_tokens:,}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">SESSION LLM COST</div>
            <div class="metric-value">${st.session_state.total_cost:.5f}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    
    # Graphs Row
    col_graph1, col_graph2 = st.columns(2)
    
    with col_graph1:
        st.markdown("##### 📁 Document Size Comparison (Character Count)")
        if st.session_state.documents:
            df_docs = pd.DataFrame([{
                "Document": doc["name"], 
                "Characters": doc["char_count"]
            } for doc in st.session_state.documents])
            st.bar_chart(df_docs.set_index("Document"), color="#00f0ff")
        else:
            st.info("No documents uploaded yet to generate analytics.")
            
    with col_graph2:
        st.markdown("##### 🧩 Chunks Breakdown per Document")
        if st.session_state.documents:
            df_chunks = pd.DataFrame([{
                "Document": doc["name"], 
                "Chunks": doc["chunks_count"]
            } for doc in st.session_state.documents])
            st.bar_chart(df_chunks.set_index("Document"), color="#1d4ed8")
        else:
            st.info("No documents uploaded yet to generate analytics.")

    st.markdown("---")
    
    # Token usage history log
    st.markdown("##### 🪙 API Usage & Cost Analytics")
    kpi_usage_col1, kpi_usage_col2 = st.columns(2)
    with kpi_usage_col1:
        st.metric("Total Tokens Transacted", f"{st.session_state.total_tokens:,}")
    with kpi_usage_col2:
        st.metric("API Provider", llm_provider)

# ====================================================
# TAB 2: DOCUMENT LIBRARY
# ====================================================
with tabs[1]:
    st.subheader("📂 Document Management Center")
    
    if not st.session_state.documents:
        st.info("No files in library yet. Use the sidebar to upload files.")
    else:
        # Create library table
        for idx, doc in enumerate(st.session_state.documents):
            with st.container():
                st.markdown(f"#### 📄 {doc['name']}")
                
                col_info1, col_info2, col_info3 = st.columns(3)
                col_info1.write(f"📅 **Upload Date:** {doc['uploaded_at']}")
                col_info2.write(f"📄 **Pages:** {doc['pages']} | 🧩 **Chunks:** {doc['chunks_count']}")
                col_info3.write(f"📏 **Character Length:** {doc['char_count']:,}")
                
                # Expandable summary
                with st.expander("📝 Document Executive Summary"):
                    st.markdown(doc["summary"])
                    
                # Action Buttons
                c1, c2, c3, _ = st.columns([1, 1.2, 1, 5])
                
                # View text content
                with c1:
                    if st.button("👁️ View Text", key=f"view_txt_{idx}", use_container_width=True):
                        st.session_state[f"show_text_{idx}"] = not st.session_state.get(f"show_text_{idx}", False)
                        
                # Refresh embeddings
                with c2:
                    refresh_allowed = check_permission("Editor")
                    if st.button("🔄 Refresh Vectors", key=f"ref_emb_{idx}", use_container_width=True, disabled=not refresh_allowed):
                        with st.spinner("Re-indexing document vectors..."):
                            # Remove existing and re-add
                            st.session_state.vector_manager.delete_document(doc["name"])
                            
                            # Filter chunks for this doc
                            doc_chunks = [c for c in st.session_state.processed_chunks if c["metadata"]["source"] == doc["name"]]
                            st.session_state.vector_manager.add_chunks(doc_chunks)
                            st.toast(f"Successfully refreshed embeddings for {doc['name']}!", icon="🔄")
                            
                # Delete document
                with c3:
                    delete_allowed = check_permission("Admin")
                    if st.button("🗑️ Delete", key=f"del_doc_{idx}", use_container_width=True, disabled=not delete_allowed):
                        # Remove from cache and Vector DB
                        st.session_state.vector_manager.delete_document(doc["name"])
                        st.session_state.processed_chunks = [c for c in st.session_state.processed_chunks if c["metadata"]["source"] != doc["name"]]
                        st.session_state.documents.pop(idx)
                        st.toast(f"Successfully deleted {doc['name']}!", icon="🗑️")
                        st.rerun()
                
                # Handle text toggle state
                if st.session_state.get(f"show_text_{idx}", False):
                    st.text_area(
                        "Raw Document Text (First 3000 Chars)", 
                        value=doc["full_text"][:3000] + ("..." if len(doc["full_text"]) > 3000 else ""),
                        height=250,
                        disabled=True
                    )
                st.markdown("<hr style='margin: 1.5rem 0; border-color: #374151;' />", unsafe_allow_html=True)

# ====================================================
# TAB 3: CONVERSATIONAL ASSISTANT
# ====================================================
with tabs[2]:
    st.subheader("💬 Cognitive AI Chat Assistant")
    
    # Check if vector DB is loaded
    if not st.session_state.processed_chunks:
        st.info("Please upload one or more documents in the sidebar to load the vector store before querying the assistant.")
    else:
        # Search parameters container
        with st.expander("🔍 Advanced Retrieval Settings", expanded=False):
            sc1, sc2, sc3 = st.columns(3)
            
            with sc1:
                search_mode = st.radio(
                    "Search Mode",
                    options=["Semantic (Vector)", "Hybrid (Vector + Keyword)"],
                    index=1,
                    help="Hybrid uses keyword match alongside semantic vector similarity for high precision."
                )
                
            with sc2:
                top_k = st.slider(
                    "Retrieve Top-K Chunks",
                    min_value=2,
                    max_value=10,
                    value=4,
                    help="Number of document chunks to retrieve and inject as context."
                )
                
            with sc3:
                # Metadata filter (query specific documents)
                doc_list = ["All Documents"] + [d["name"] for d in st.session_state.documents]
                selected_filter_doc = st.selectbox(
                    "Metadata Filter (Search specific doc)",
                    options=doc_list,
                    index=0,
                    help="Restrict semantic queries to this document only."
                )
                filter_doc_name = None if selected_filter_doc == "All Documents" else selected_filter_doc
        
        # Display suggested questions chips
        st.markdown("💡 **Suggested Queries:**")
        # Gather suggestions from all documents (first 4 questions)
        suggestions = []
        for d in st.session_state.documents:
            suggestions.extend(d["suggested_questions"])
            
        suggestions = list(set(suggestions))[:4] # Deduplicate and limit to 4
        
        cols_sug = st.columns(len(suggestions) if suggestions else 1)
        clicked_question = None
        for i, q in enumerate(suggestions):
            if cols_sug[i].button(q, key=f"sug_{i}", use_container_width=True):
                clicked_question = q
                
        st.markdown("---")
        
        # Render Chat History
        for msg in st.session_state.messages:
            avatar = "👤" if msg["role"] == "user" else "🤖"
            bubble_class = "user-bubble" if msg["role"] == "user" else "assistant-bubble"
            
            st.markdown(f"""
            <div class="chat-bubble {bubble_class}">
                <div class="chat-avatar">{avatar}</div>
                <div>
                    <div>{msg['content']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Display source citations if present
            if msg["role"] == "assistant" and "sources" in msg:
                with st.expander("📚 Retrieved Source References"):
                    for idx, src in enumerate(msg["sources"]):
                        meta = src.metadata
                        page_str = f"Page {meta.get('page')}" if meta.get('page') else "Reference"
                        st.markdown(f"""
                        <div class="citation-container">
                            <strong>[{idx+1}] {meta.get('source')} ({page_str})</strong><br/>
                            {src.page_content}
                        </div>
                        """, unsafe_allow_html=True)
                        
        # Chat input handling
        user_query = st.chat_input("Ask a question about the uploaded documents...")
        
        # If suggested question clicked, override input
        if clicked_question:
            user_query = clicked_question
            
        if user_query:
            # 1. User Message
            st.session_state.messages.append({"role": "user", "content": user_query})
            st.markdown(f"""
            <div class="chat-bubble user-bubble">
                <div class="chat-avatar">👤</div>
                <div>{user_query}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 2. Retrieval Phase
            with st.spinner("Retrieving relevant document chunks..."):
                if search_mode == "Semantic (Vector)":
                    retrieved_chunks = st.session_state.vector_manager.similarity_search(
                        user_query, 
                        k=top_k, 
                        doc_filter=filter_doc_name
                    )
                else:
                    retrieved_chunks = st.session_state.vector_manager.hybrid_search(
                        user_query, 
                        k=top_k, 
                        doc_filter=filter_doc_name
                    )
                    
            # 3. Generation Phase
            with st.spinner("Formulating intelligent response..."):
                res = chat_engine.ask(
                    user_query, 
                    retrieved_chunks, 
                    st.session_state.messages[:-1] # Exclude current query
                )
                
                answer = res["answer"]
                tokens = res["tokens"]
                cost = res["cost"]
                sources = res["sources"]
                
                # Update tokens and cost
                st.session_state.total_tokens += tokens
                st.session_state.total_cost += cost
                
            # 4. Save response to session state
            st.session_state.messages.append({
                "role": "assistant", 
                "content": answer,
                "sources": sources
            })
            st.rerun()
            
        # Export Option
        if st.session_state.messages:
            st.markdown("---")
            ec1, ec2, _ = st.columns([1.5, 1.5, 7])
            
            # Export Text
            chat_text = ""
            for msg in st.session_state.messages:
                role = "USER" if msg["role"] == "user" else "ASSISTANT"
                chat_text += f"{role}:\n{msg['content']}\n\n"
                
            with ec1:
                st.download_button(
                    "📥 Export Chat (TXT)",
                    data=chat_text,
                    file_name="doc_intel_conversation.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                
            # Export JSON
            with ec2:
                chat_json = json.dumps(st.session_state.messages, default=str, indent=2)
                st.download_button(
                    "📥 Export Chat (JSON)",
                    data=chat_json,
                    file_name="doc_intel_conversation.json",
                    mime="application/json",
                    use_container_width=True
                )

# ====================================================
# TAB 4: COMPARE DOCUMENTS
# ====================================================
with tabs[3]:
    st.subheader("⚖️ Document Side-by-Side Comparison")
    
    if len(st.session_state.documents) < 2:
        st.info("Please upload at least 2 documents to perform side-by-side comparative analysis.")
    else:
        # Select two documents
        doc_names = [d["name"] for d in st.session_state.documents]
        
        comp_col1, comp_col2 = st.columns(2)
        
        with comp_col1:
            doc1_name = st.selectbox("Select First Document (Left)", doc_names, index=0)
            doc1 = next(d for d in st.session_state.documents if d["name"] == doc1_name)
            
        with comp_col2:
            doc2_name = st.selectbox("Select Second Document (Right)", doc_names, index=1 if len(doc_names) > 1 else 0)
            doc2 = next(d for d in st.session_state.documents if d["name"] == doc2_name)
            
        st.markdown("---")
        
        # Display side-by-side info
        col_side1, col_side2 = st.columns(2)
        
        with col_side1:
            st.markdown(f"#### 📄 {doc1['name']}")
            st.write(f"📅 **Uploaded:** {doc1['uploaded_at']}")
            st.write(f"📏 **Length:** {doc1['char_count']:,} chars | 🧩 **Chunks:** {doc1['chunks_count']}")
            st.markdown("##### Summary")
            st.info(doc1["summary"])
            
            with st.expander("🔬 View Excerpt"):
                st.text(doc1["full_text"][:2000] + "...")
                
        with col_side2:
            st.markdown(f"#### 📄 {doc2['name']}")
            st.write(f"📅 **Uploaded:** {doc2['uploaded_at']}")
            st.write(f"📏 **Length:** {doc2['char_count']:,} chars | 🧩 **Chunks:** {doc2['chunks_count']}")
            st.markdown("##### Summary")
            st.success(doc2["summary"])
            
            with st.expander("🔬 View Excerpt"):
                st.text(doc2["full_text"][:2000] + "...")
                
        # Comparison Query Option
        st.markdown("---")
        st.markdown("##### 🤖 Compare using Natural Language")
        comp_query = st.text_input(
            "Ask a comparison question (e.g. 'Compare the revenue margins between these two documents'):",
            placeholder="Enter comparison question..."
        )
        
        if comp_query:
            with st.spinner("Analyzing comparison queries..."):
                # Retrieve from doc 1
                chunks1 = st.session_state.vector_manager.hybrid_search(comp_query, k=2, doc_filter=doc1_name)
                # Retrieve from doc 2
                chunks2 = st.session_state.vector_manager.hybrid_search(comp_query, k=2, doc_filter=doc2_name)
                
                combined_chunks = chunks1 + chunks2
                
                # Ask chat engine
                comparison_chat_engine = ChatEngine(
                    provider=llm_provider_type,
                    api_key=active_llm_key,
                    model_name=model_name
                )
                
                # Perform query
                comp_res = comparison_chat_engine.ask(
                    f"Compare the information in these two documents regarding the question: {comp_query}",
                    combined_chunks,
                    []
                )
                
                st.markdown("##### 📝 Comparative Analysis:")
                st.write(comp_res["answer"])
                
                with st.expander("📚 Retrieved Comparison Sources"):
                    for idx, src in enumerate(combined_chunks):
                        meta = src.metadata
                        page_str = f"Page {meta.get('page')}" if meta.get('page') else "Reference"
                        st.markdown(f"""
                        <div class="citation-container">
                            <strong>[{idx+1}] {meta.get('source')} ({page_str})</strong><br/>
                            {src.page_content}
                        </div>
                        """, unsafe_allow_html=True)
