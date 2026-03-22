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


def _show_answer(answer: dict):
    if "error" in answer:
        st.error(answer["error"])
        return

    if "english" in answer and answer["english"]:
        st.markdown("**English Answer**")
        st.markdown(
            f'<div class="english-answer">{answer["english"]}</div>',
            unsafe_allow_html=True,
        )

    if "hindi" in answer and answer["hindi"]:
        st.markdown("**Hindi Answer**")
        st.markdown(
            f'<div class="hindi-answer">{answer["hindi"]}</div>',
            unsafe_allow_html=True,
        )

    if "sources" in answer and answer["sources"]:
        with st.expander("Sources and Context"):
            for src in answer["sources"]:
                st.markdown(
                    f'<div class="source-card">'
                    f'<b>{src.get("document_name","")}</b> '
                    f'{src.get("breadcrumb","")} '
                    f'[{src.get("section_type","")}]<br/>'
                    f'<i>{src.get("snippet","")[:300]}...</i>'
                    f"</div>",
                    unsafe_allow_html=True,
                )


st.set_page_config(
    page_title="Legal Document QA",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
.hindi-answer {
    background-color: #FFF8E1;
    border-left: 4px solid #FFC107;
    padding: 12px 16px;
    border-radius: 4px;
    font-size: 16px;
    line-height: 1.8;
}
.english-answer {
    background-color: #E3F2FD;
    border-left: 4px solid #2196F3;
    padding: 12px 16px;
    border-radius: 4px;
    font-size: 16px;
    line-height: 1.8;
}
.source-card {
    background-color: #F5F5F5;
    border: 1px solid #E0E0E0;
    padding: 8px 12px;
    border-radius: 4px;
    margin: 4px 0;
    font-size: 13px;
}
</style>
""",
    unsafe_allow_html=True,
)


with st.sidebar:
    st.title("Legal Document QA")

    uploaded_file = st.file_uploader(
        "Upload a legal document",
        type=["txt", "pdf", "docx"],
    )

    doc_name = st.text_input(
        "Document name",
        placeholder="Service Agreement 2024",
    )

    ingest_button = st.button("Ingest Document", use_container_width=True)

    st.divider()

    language = st.radio(
        "Answer language",
        options=["both", "english", "hindi"],
        format_func=lambda x: {
            "both": "Both (English + Hindi)",
            "english": "English",
            "hindi": "Hindi",
        }[x],
        index=0,
    )

    num_results = st.slider("Retrieved chunks", 3, 10, 5)

    ollama_model = st.text_input(
        "Ollama model",
        value=os.getenv("OLLAMA_MODEL", "mistral"),
    )

    ollama_url = st.text_input(
        "Ollama base URL",
        value=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    )

    index_name = st.text_input(
        "Endee index name",
        value=os.getenv("ENDEE_INDEX_NAME", "legal_docs"),
    )

    st.divider()

    if st.button("Clear Chat"):
        st.session_state["chat_history"] = []
        st.rerun()


if "ingested" not in st.session_state:
    st.session_state["ingested"] = False

if "pipeline" not in st.session_state:
    st.session_state["pipeline"] = None

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []


if ingest_button:
    if uploaded_file is None:
        st.sidebar.error("Upload a document first.")
    else:
        with st.spinner("Ingesting document..."):
            try:
                suffix = Path(uploaded_file.name).suffix

                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name

                effective_name = doc_name.strip() if doc_name.strip() else None

                docs = ingest_document(
                    tmp_path,
                    document_name=effective_name,
                    index_name=index_name,
                    append=True,
                )

                os.unlink(tmp_path)

                st.session_state["ingested"] = True
                st.session_state["pipeline"] = None
                st.session_state["chat_history"] = []

                st.sidebar.success(f"Ingested {len(docs)} chunks")
                st.sidebar.write(f"Chunks: {len(docs)}")
                st.sidebar.write(f"Index: {index_name}")

            except Exception as e:
                st.sidebar.error(f"Ingestion failed: {e}")


sample_path = Path(__file__).parent.parent / "data" / "sample_contract.txt"

if sample_path.exists():
    if st.sidebar.button("Load Sample Contract", use_container_width=True):
        with st.spinner("Ingesting sample..."):
            try:
                docs = ingest_document(
                    str(sample_path),
                    document_name="Sample Service Agreement",
                    index_name=index_name,
                    append=True,
                )
                st.session_state["ingested"] = True
                st.session_state["pipeline"] = None
                st.session_state["chat_history"] = []
                st.sidebar.success(f"Loaded sample contract ({len(docs)} chunks)")
            except Exception as e:
                st.sidebar.error(f"Failed: {e}")


st.title("Legal Document QA")

if not st.session_state["ingested"]:
    st.info("Upload a document and ingest it before asking questions.")
else:
    if st.session_state["pipeline"] is None:
        try:
            st.session_state["pipeline"] = QueryPipeline(
                index_name=index_name,
                k=num_results,
                model=ollama_model,
                base_url=ollama_url,
            )
        except Exception as e:
            st.error(f"Pipeline initialization failed: {e}")
            st.stop()

    for entry in st.session_state["chat_history"]:
        with st.chat_message("user"):
            st.write(entry["question"])
        with st.chat_message("assistant"):
            _show_answer(entry["answer"])

    question = st.chat_input("Ask a question about your document")

    if question:
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Generating answer..."):
                try:
                    pipeline: QueryPipeline = st.session_state["pipeline"]
                    start = time.time()
                    answer = pipeline.query(
                        question,
                        language=language,
                        k=num_results,
                    )
                    elapsed = time.time() - start
                    _show_answer(answer)
                    st.caption(f"Answer generated in {elapsed:.2f}s")
                    st.session_state["chat_history"].append(
                        {"question": question, "answer": answer}
                    )
                except Exception as e:
                    st.error(f"Error generating answer: {e}")
