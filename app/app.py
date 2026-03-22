import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

from src.ingestion import ingest_document
from src.pipeline.query import QueryPipeline


st.set_page_config(
    page_title="LegalMind RAG",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Outfit:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');
html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
.stApp { background-color: #0D0F14; color: #E8E4DC; }
section[data-testid="stSidebar"] { background-color: #0A0C10; border-right: 1px solid #1E2128; }
section[data-testid="stSidebar"] * { color: #A0A4AE; }
.logo-block { display:flex; align-items:center; gap:12px; padding:8px 0 24px; border-bottom:1px solid #1A1D24; margin-bottom:20px; }
.logo-icon { width:38px; height:38px; background:linear-gradient(135deg,#C9A84C,#E8C96A); border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:18px; }
.logo-title { font-family:'DM Serif Display',serif; font-size:20px; color:#E8E4DC; letter-spacing:0.02em; line-height:1.1; }
.logo-sub { font-size:10px; color:#3A3E4A; letter-spacing:0.1em; text-transform:uppercase; font-family:'DM Mono',monospace; }
.page-header { font-family:'DM Serif Display',serif; font-size:28px; color:#E8E4DC; letter-spacing:0.01em; margin-bottom:4px; }
.page-sub { font-size:13px; color:#3A3E4A; margin-bottom:24px; letter-spacing:0.02em; }
.status-bar { display:flex; align-items:center; gap:8px; background:#0F1A12; border:1px solid #1A3A1E; border-radius:20px; padding:6px 14px; font-size:12px; color:#4A9E5C; width:fit-content; margin-bottom:28px; font-family:'DM Mono',monospace; }
.status-dot { width:7px; height:7px; border-radius:50%; background:#4A9E5C; }
.english-answer { background:#0D1520; border-left:3px solid #2B5BA0; border-radius:0 10px 10px 0; padding:14px 18px; margin-bottom:10px; font-size:15px; color:#A8C4E0; line-height:1.8; }
.english-answer-label { font-size:10px; letter-spacing:0.12em; text-transform:uppercase; color:#4A7AB5; margin-bottom:8px; font-weight:600; font-family:'DM Mono',monospace; }
.hindi-answer { background:#1A1208; border-left:3px solid #8A6A1A; border-radius:0 10px 10px 0; padding:14px 18px; margin-bottom:10px; font-size:15px; color:#D4B86A; line-height:1.9; }
.hindi-answer-label { font-size:10px; letter-spacing:0.12em; text-transform:uppercase; color:#8A6A1A; margin-bottom:8px; font-weight:600; font-family:'DM Mono',monospace; }
.source-card { background:#0F1115; border:1px solid #1E2128; border-radius:8px; padding:10px 14px; margin:6px 0; font-size:12px; color:#5A5E6A; border-left:2px solid #C9A84C; }
.source-name { font-weight:600; color:#A0A4AE; font-size:12px; margin-bottom:4px; }
.source-section { color:#C9A84C; font-family:'DM Mono',monospace; font-size:11px; }
.empty-state { text-align:center; padding:60px 20px; opacity:0.4; }
.empty-icon { font-size:40px; margin-bottom:14px; }
.empty-text { font-size:14px; color:#5A5E6A; line-height:1.7; }
.timing-note { font-size:11px; color:#2A2D35; font-family:'DM Mono',monospace; margin-top:8px; }
.section-divider { border:none; border-top:1px solid #1A1D24; margin:16px 0; }
div[data-testid="stChatMessage"] { background:transparent !important; }
.stTextInput input, .stTextArea textarea { background:#161920 !important; border:1px solid #1E2128 !important; color:#A0A4AE !important; border-radius:8px !important; font-family:'Outfit',sans-serif !important; }
.stButton button { background:#C9A84C !important; color:#0A0C10 !important; border:none !important; border-radius:8px !important; font-weight:600 !important; font-family:'Outfit',sans-serif !important; letter-spacing:0.04em !important; }
.stButton button:hover { background:#E8C96A !important; }
.stRadio label { color:#6A6E7A !important; font-size:13px !important; }
.stExpander { background:#0F1115 !important; border:1px solid #1E2128 !important; border-radius:8px !important; }
</style>
""", unsafe_allow_html=True)


def _show_answer(answer: dict):
    if "error" in answer:
        st.error(answer["error"])
        return
    if "english" in answer and answer["english"]:
        st.markdown(
            '<div class="english-answer"><div class="english-answer-label">English</div>'
            f'{answer["english"]}</div>',
            unsafe_allow_html=True,
        )
    if "hindi" in answer and answer["hindi"]:
        st.markdown(
            '<div class="hindi-answer"><div class="hindi-answer-label">Hindi · हिंदी</div>'
            f'{answer["hindi"]}</div>',
            unsafe_allow_html=True,
        )
    if "sources" in answer and answer["sources"]:
        with st.expander(f"📎 {len(answer['sources'])} sources"):
            for src in answer["sources"]:
                st.markdown(
                    f'<div class="source-card">'
                    f'<div class="source-name">📄 {src.get("document_name","Unknown")}</div>'
                    f'<div class="source-section">{src.get("breadcrumb","")} · {src.get("section_type","")}</div>'
                    f'<div style="margin-top:6px;font-size:12px;color:#3A3E4A;line-height:1.6;">{src.get("snippet","")[:250]}…</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )


with st.sidebar:
    st.markdown(
        '<div class="logo-block"><div class="logo-icon">⚖️</div>'
        '<div><div class="logo-title">LegalMind</div>'
        '<div class="logo-sub">RAG · Powered by Endee</div></div></div>',
        unsafe_allow_html=True,
    )

    mode = st.radio(
        "Mode",
        options=["query", "ingest"],
        format_func=lambda x: {"query": "💬 Query Existing Index", "ingest": "📥 Upload New Document"}[x],
        index=0,
    )

    st.markdown('<hr class="section-divider"/>', unsafe_allow_html=True)

    if mode == "ingest":
        st.markdown("**Upload Document**")
        uploaded_file = st.file_uploader("Upload", type=["txt","pdf","docx"], label_visibility="collapsed")
        doc_name = st.text_input("Document name (optional)", placeholder="e.g. Service Agreement 2024")
        ingest_button = st.button("⚡ Ingest Document", use_container_width=True)
    else:
        uploaded_file = None
        ingest_button = False
        st.info("Querying documents already stored in Endee index.")

    st.markdown('<hr class="section-divider"/>', unsafe_allow_html=True)

    language = st.radio(
        "Answer Language",
        options=["both","english","hindi"],
        format_func=lambda x: {"both":"🌐 English + Hindi","english":"🇬🇧 English only","hindi":"🇮🇳 Hindi only"}[x],
        index=0,
    )

    st.markdown('<hr class="section-divider"/>', unsafe_allow_html=True)
    num_results = st.slider("Retrieved Chunks", 3, 10, 5)
    st.markdown('<hr class="section-divider"/>', unsafe_allow_html=True)

    with st.expander("⚙️ Settings"):
        ollama_model = st.text_input("Ollama model", value=os.getenv("OLLAMA_MODEL","mistral"))
        ollama_url = st.text_input("Ollama URL", value=os.getenv("OLLAMA_BASE_URL","http://localhost:11434"))
        index_name = st.text_input("Endee index", value=os.getenv("ENDEE_INDEX_NAME","legal_docs"))

    st.markdown('<hr class="section-divider"/>', unsafe_allow_html=True)
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state["chat_history"] = []
        st.rerun()


if "ingested" not in st.session_state:
    st.session_state["ingested"] = False
if "pipeline" not in st.session_state:
    st.session_state["pipeline"] = None
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "index_name" not in st.session_state:
    st.session_state["index_name"] = os.getenv("ENDEE_INDEX_NAME","legal_docs")


if mode == "query" and not st.session_state["ingested"]:
    st.session_state["ingested"] = True


if ingest_button:
    if uploaded_file is None:
        st.sidebar.error("Please upload a document first.")
    else:
        with st.spinner("Ingesting document into Endee..."):
            try:
                suffix = Path(uploaded_file.name).suffix
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                effective_name = doc_name.strip() if doc_name.strip() else None
                idx = index_name.strip() if index_name.strip() else "legal_docs"
                docs = ingest_document(tmp_path, document_name=effective_name, index_name=idx, append=True)
                os.unlink(tmp_path)
                st.session_state["ingested"] = True
                st.session_state["pipeline"] = None
                st.session_state["chat_history"] = []
                st.session_state["index_name"] = idx
                st.sidebar.success(f"✅ {len(docs)} chunks ingested")
            except Exception as e:
                st.sidebar.error(f"Ingestion failed: {e}")


st.markdown('<div class="page-header">Legal Document Q&A</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Ask questions about your legal documents — answers in English and Hindi</div>', unsafe_allow_html=True)

if st.session_state["ingested"]:
    idx_display = st.session_state.get("index_name", index_name)
    st.markdown(
        f'<div class="status-bar"><div class="status-dot"></div>Endee · {idx_display} · ready</div>',
        unsafe_allow_html=True,
    )

if not st.session_state["ingested"]:
    st.markdown(
        '<div class="empty-state"><div class="empty-icon">⚖️</div>'
        '<div class="empty-text">Upload a legal document from the sidebar<br>and click <strong>Ingest Document</strong> to begin.</div></div>',
        unsafe_allow_html=True,
    )
else:
    if st.session_state["pipeline"] is None:
        try:
            idx = index_name.strip() if index_name.strip() else "legal_docs"
            st.session_state["pipeline"] = QueryPipeline(
                index_name=idx,
                k=num_results,
                model=ollama_model,
                base_url=ollama_url,
            )
            st.session_state["index_name"] = idx
        except Exception as e:
            st.error(f"Pipeline initialization failed: {e}")
            st.stop()

    for entry in st.session_state["chat_history"]:
        with st.chat_message("user"):
            st.write(entry["question"])
        with st.chat_message("assistant"):
            _show_answer(entry["answer"])
            if "elapsed" in entry:
                st.markdown(f'<div class="timing-note">⏱ {entry["elapsed"]:.2f}s</div>', unsafe_allow_html=True)

    question = st.chat_input("Ask a question about your document...")

    if question:
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            with st.spinner("Searching and generating answer..."):
                try:
                    pipeline: QueryPipeline = st.session_state["pipeline"]
                    start = time.time()
                    answer = pipeline.query(question, language=language, k=num_results)
                    elapsed = time.time() - start
                    _show_answer(answer)
                    st.markdown(f'<div class="timing-note">⏱ {elapsed:.2f}s</div>', unsafe_allow_html=True)
                    st.session_state["chat_history"].append({"question": question, "answer": answer, "elapsed": elapsed})
                except Exception as e:
                    st.error(f"Error: {e}")
