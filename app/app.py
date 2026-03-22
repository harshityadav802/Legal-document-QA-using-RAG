import os
import sys
import tempfile
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

from src.pipeline.ingestion import ingest_document
from src.pipeline.query import QueryPipeline

st.set_page_config(
    page_title="Legal Document QA",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: sans-serif;
    background-color: #000000;
    color: #FFFFFF;
}
.stApp { background-color: #000000; }
section[data-testid="stSidebar"] {
    background-color: #0A0A0A;
    border-right: 1px solid #222222;
}
section[data-testid="stSidebar"] * { color: #AAAAAA; }
.app-title { font-size: 16px; font-weight: 600; color: #FFFFFF; margin-bottom: 2px; font-family: sans-serif; }
.app-sub { font-size: 11px; color: #444444; padding-bottom: 14px; border-bottom: 1px solid #222222; margin-bottom: 4px; font-family: sans-serif; }
.page-title { font-size: 24px; font-weight: 600; color: #FFFFFF; margin-bottom: 4px; font-family: sans-serif; }
.page-sub { font-size: 13px; color: #555555; margin-bottom: 20px; font-family: sans-serif; }
.status-bar { display: inline-flex; align-items: center; gap: 7px; background: #0A0A0A; border: 1px solid #222222; border-radius: 20px; padding: 5px 14px; font-size: 12px; color: #AAAAAA; margin-bottom: 24px; font-family: sans-serif; }
.status-dot { width: 7px; height: 7px; border-radius: 50%; background: #FFFFFF; display: inline-block; }
.en-answer { background: #0A0A0A; border-left: 3px solid #FFFFFF; border-radius: 0 6px 6px 0; padding: 14px 18px; margin-bottom: 10px; font-size: 14px; color: #DDDDDD; line-height: 1.8; font-family: sans-serif; }
.en-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: #666666; margin-bottom: 8px; font-weight: 600; font-family: sans-serif; }
.hi-answer { background: #0A0A0A; border-left: 3px solid #888888; border-radius: 0 6px 6px 0; padding: 14px 18px; margin-bottom: 10px; font-size: 14px; color: #CCCCCC; line-height: 1.9; font-family: sans-serif; }
.hi-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.08em; color: #555555; margin-bottom: 8px; font-weight: 600; font-family: sans-serif; }
.src-card { background: #0A0A0A; border: 1px solid #222222; border-radius: 6px; padding: 10px 14px; margin: 5px 0; font-size: 12px; color: #666666; font-family: sans-serif; }
.src-name { font-weight: 600; color: #AAAAAA; margin-bottom: 3px; font-size: 12px; font-family: sans-serif; }
.src-section { color: #444444; font-size: 11px; font-family: sans-serif; }
.timing { font-size: 11px; color: #333333; margin-top: 6px; font-family: sans-serif; }
.empty-state { text-align: center; padding: 80px 20px; color: #333333; font-family: sans-serif; }
.empty-text { font-size: 14px; line-height: 1.7; font-family: sans-serif; }
.divider { border: none; border-top: 1px solid #1A1A1A; margin: 14px 0; }
.stTextInput input, .stTextArea textarea { background: #111111 !important; border: 1px solid #333333 !important; color: #FFFFFF !important; border-radius: 6px !important; font-family: sans-serif !important; font-size: 13px !important; }
.stButton button { background: #FFFFFF !important; color: #000000 !important; border: none !important; border-radius: 6px !important; font-weight: 600 !important; font-family: sans-serif !important; font-size: 13px !important; }
.stButton button:hover { background: #DDDDDD !important; }
.stRadio label { color: #AAAAAA !important; font-size: 13px !important; font-family: sans-serif !important; }
.stSlider { color: #FFFFFF !important; }
.stExpander { background: #0A0A0A !important; border: 1px solid #222222 !important; border-radius: 6px !important; }
div[data-testid="stChatMessage"] { background: transparent !important; }
</style>
""", unsafe_allow_html=True)


def _show_answer(answer: dict):
    if "error" in answer:
        st.error(answer["error"])
        return
    if "english" in answer and answer["english"]:
        st.markdown(
            '<div class="en-answer"><div class="en-label">English</div>'
            f'{answer["english"]}</div>',
            unsafe_allow_html=True,
        )
    if "hindi" in answer and answer["hindi"]:
        st.markdown(
            '<div class="hi-answer"><div class="hi-label">Hindi</div>'
            f'{answer["hindi"]}</div>',
            unsafe_allow_html=True,
        )
    if "sources" in answer and answer["sources"]:
        with st.expander(f"Sources ({len(answer['sources'])})"):
            for src in answer["sources"]:
                st.markdown(
                    f'<div class="src-card">'
                    f'<div class="src-name">{src.get("document_name","Unknown")}</div>'
                    f'<div class="src-section">{src.get("section","")} · chunk {src.get("chunk_index","")}</div>'
                    f'<div style="margin-top:5px;font-size:12px;color:#444444;line-height:1.6;">{src.get("snippet","")[:200]}...</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )


with st.sidebar:
    st.markdown('<div class="app-title">Legal Document QA</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-sub">powered by Endee</div>', unsafe_allow_html=True)

    mode = st.radio(
        "Mode",
        options=["query", "ingest"],
        format_func=lambda x: {"query": "Query existing index", "ingest": "Upload new document"}[x],
        index=0,
    )

    st.markdown('<hr class="divider"/>', unsafe_allow_html=True)

    if mode == "ingest":
        uploaded_file = st.file_uploader("Document", type=["txt","pdf","docx"])
        doc_name = st.text_input("Document name (optional)", placeholder="e.g. name of the case ")
        ingest_button = st.button("Ingest Document", use_container_width=True)
    else:
        uploaded_file = None
        ingest_button = False

    st.markdown('<hr class="divider"/>', unsafe_allow_html=True)

    language = st.radio(
        "Answer Language",
        options=["both","english","hindi"],
        format_func=lambda x: {"both":"English + Hindi","english":"English only","hindi":"Hindi only"}[x],
        index=0,
    )

    st.markdown('<hr class="divider"/>', unsafe_allow_html=True)
    num_results = st.slider("Retrieved Chunks", 3, 10, 5)
    st.markdown('<hr class="divider"/>', unsafe_allow_html=True)

    with st.expander("Settings"):
        ollama_model = st.text_input("Ollama model", value=os.getenv("OLLAMA_MODEL","mistral"))
        ollama_url = st.text_input("Ollama URL", value=os.getenv("OLLAMA_BASE_URL","http://localhost:11434"))
        index_name = st.text_input("Endee index", value=os.getenv("ENDEE_INDEX_NAME","legal_docs"))

    st.markdown('<hr class="divider"/>', unsafe_allow_html=True)

    if st.button("Clear Chat", use_container_width=True):
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
        with st.spinner("Ingesting..."):
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
                st.sidebar.success(f"{len(docs)} chunks ingested")
            except Exception as e:
                st.sidebar.error(f"Ingestion failed: {e}")


st.markdown('<div class="page-title">Legal Document QA</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Ask questions about legal documents. Answers in English and Hindi.</div>', unsafe_allow_html=True)

if st.session_state["ingested"]:
    idx_display = st.session_state.get("index_name", "legal_docs")
    st.markdown(
        f'<div class="status-bar"><div class="status-dot"></div>{idx_display} · ready</div>',
        unsafe_allow_html=True,
    )

if not st.session_state["ingested"]:
    st.markdown(
        '<div class="empty-state"><div class="empty-text">Select a mode from the sidebar to get started.</div></div>',
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
                st.markdown(f'<div class="timing">{entry["elapsed"]:.2f}s</div>', unsafe_allow_html=True)

    question = st.chat_input("Ask a question about your documents...")

    if question:
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            with st.spinner("Searching..."):
                try:
                    pipeline: QueryPipeline = st.session_state["pipeline"]
                    start = time.time()
                    answer = pipeline.query(question, language=language, k=num_results)
                    elapsed = time.time() - start
                    _show_answer(answer)
                    st.markdown(f'<div class="timing">{elapsed:.2f}s</div>', unsafe_allow_html=True)
                    st.session_state["chat_history"].append({"question": question, "answer": answer, "elapsed": elapsed})
                except Exception as e:
                    st.error(f"Error: {e}")
