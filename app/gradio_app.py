import os
import sys
import tempfile
import time
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

from src.pipeline.ingestion import ingest_document
from src.pipeline.query import QueryPipeline

# ---------------------------------------------------------------------------
# Custom CSS – professional dark theme
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
/* ── Global reset ────────────────────────────────────────────────────── */
* { box-sizing: border-box; }

body, .gradio-container {
    background: #0a0a0a !important;
    color: #e0e0e0 !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* ── Header ──────────────────────────────────────────────────────────── */
#app-header {
    background: #111111;
    border-bottom: 1px solid #222222;
    padding: 18px 28px;
    margin-bottom: 0;
}
#app-title {
    font-size: 22px;
    font-weight: 700;
    color: #ffffff;
    margin: 0;
    display: inline-flex;
    align-items: center;
    gap: 10px;
}
#app-subtitle {
    font-size: 12px;
    color: #555555;
    margin-top: 3px;
}

/* ── Tabs ────────────────────────────────────────────────────────────── */
.tab-nav button {
    background: transparent !important;
    color: #777777 !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 10px 18px !important;
    transition: color 0.2s, border-color 0.2s !important;
}
.tab-nav button.selected, .tab-nav button:hover {
    color: #ffffff !important;
    border-bottom-color: #ffffff !important;
    background: transparent !important;
}

/* ── Panels / cards ──────────────────────────────────────────────────── */
.panel-card {
    background: #111111;
    border: 1px solid #222222;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 16px;
}

/* ── Inputs ──────────────────────────────────────────────────────────── */
input[type="text"], textarea, .gr-input, .gr-textarea {
    background: #111111 !important;
    border: 1px solid #333333 !important;
    color: #ffffff !important;
    border-radius: 6px !important;
    font-size: 13px !important;
}
input[type="text"]:focus, textarea:focus {
    border-color: #555555 !important;
    outline: none !important;
    box-shadow: 0 0 0 2px rgba(255,255,255,0.06) !important;
}

/* ── Buttons ─────────────────────────────────────────────────────────── */
.btn-primary {
    background: #ffffff !important;
    color: #000000 !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 10px 20px !important;
    cursor: pointer !important;
    transition: background 0.2s !important;
}
.btn-primary:hover { background: #dddddd !important; }

.btn-secondary {
    background: #1a1a1a !important;
    color: #aaaaaa !important;
    border: 1px solid #333333 !important;
    border-radius: 6px !important;
    font-size: 13px !important;
    padding: 8px 16px !important;
    cursor: pointer !important;
    transition: background 0.2s, color 0.2s !important;
}
.btn-secondary:hover { background: #222222 !important; color: #ffffff !important; }

button.lg { font-size: 13px !important; }

/* ── Chat messages ───────────────────────────────────────────────────── */
#chatbox { background: #0a0a0a !important; border: 1px solid #222222 !important; border-radius: 8px !important; }
.message.user { background: #1a1a1a !important; border-radius: 8px !important; color: #e0e0e0 !important; }
.message.bot  { background: #111111  !important; border-radius: 8px !important; color: #e0e0e0 !important; }

/* ── Answer cards ────────────────────────────────────────────────────── */
.en-answer {
    background: #0d0d0d;
    border-left: 3px solid #ffffff;
    border-radius: 0 6px 6px 0;
    padding: 14px 18px;
    margin-bottom: 12px;
    font-size: 14px;
    color: #dddddd;
    line-height: 1.8;
}
.hi-answer {
    background: #0d0d0d;
    border-left: 3px solid #888888;
    border-radius: 0 6px 6px 0;
    padding: 14px 18px;
    margin-bottom: 12px;
    font-size: 14px;
    color: #cccccc;
    line-height: 1.9;
}
.answer-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #555555;
    margin-bottom: 8px;
    font-weight: 600;
}
.src-card {
    background: #0d0d0d;
    border: 1px solid #222222;
    border-radius: 6px;
    padding: 10px 14px;
    margin: 5px 0;
    font-size: 12px;
    color: #666666;
}
.src-name  { font-weight: 600; color: #aaaaaa; margin-bottom: 3px; }
.src-meta  { color: #444444; font-size: 11px; }
.src-snip  { margin-top: 5px; font-size: 12px; color: #444444; line-height: 1.6; }
.timing    { font-size: 11px; color: #444444; margin-top: 4px; }

/* ── Status badge ────────────────────────────────────────────────────── */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #111111;
    border: 1px solid #222222;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 12px;
    color: #aaaaaa;
    margin-top: 8px;
}
.dot-green  { width: 7px; height: 7px; border-radius: 50%; background: #22c55e; display: inline-block; }
.dot-gray   { width: 7px; height: 7px; border-radius: 50%; background: #555555; display: inline-block; }

/* ── Slider ──────────────────────────────────────────────────────────── */
.gr-slider input[type=range] { accent-color: #ffffff; }

/* ── Radio / dropdown ────────────────────────────────────────────────── */
.gr-radio label, .gr-dropdown label { color: #aaaaaa !important; font-size: 13px !important; }

/* ── File upload ─────────────────────────────────────────────────────── */
.gr-file-upload { background: #111111 !important; border: 1px dashed #333333 !important; border-radius: 8px !important; color: #777777 !important; }

/* ── Accordion ───────────────────────────────────────────────────────── */
.gr-accordion { background: #111111 !important; border: 1px solid #222222 !important; border-radius: 6px !important; }
.gr-accordion summary { color: #aaaaaa !important; font-size: 13px !important; }

/* ── Scrollbar ───────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0a0a0a; }
::-webkit-scrollbar-thumb { background: #333333; border-radius: 3px; }
"""

# ---------------------------------------------------------------------------
# Session state (module-level dicts keyed by session; Gradio uses gr.State)
# ---------------------------------------------------------------------------

def _format_answer_html(answer: dict) -> str:
    """Convert a QueryPipeline answer dict to styled HTML."""
    if not answer:
        return ""
    if "error" in answer:
        return f'<div style="color:#ef4444;padding:12px;border-left:3px solid #ef4444;background:#0d0d0d;">{answer["error"]}</div>'

    parts = []
    if answer.get("english"):
        parts.append(
            f'<div class="en-answer"><div class="answer-label">English</div>{answer["english"]}</div>'
        )
    if answer.get("hindi"):
        parts.append(
            f'<div class="hi-answer"><div class="answer-label">Hindi</div>{answer["hindi"]}</div>'
        )
    if answer.get("sources"):
        src_html = '<div style="margin-top:10px;">'
        for src in answer["sources"]:
            name = src.get("document_name", "Unknown")
            section = src.get("section_type", src.get("breadcrumb", ""))
            snippet = src.get("snippet", "")[:200]
            src_html += (
                f'<div class="src-card">'
                f'<div class="src-name">{name}</div>'
                f'<div class="src-meta">{section}</div>'
                f'<div class="src-snip">{snippet}…</div>'
                f'</div>'
            )
        src_html += "</div>"
        parts.append(src_html)
    return "\n".join(parts)


def _history_to_messages(history: list) -> list:
    """Convert internal chat history to Gradio chatbot format."""
    messages = []
    for entry in history:
        messages.append({"role": "user", "content": entry["question"]})
        bot_html = _format_answer_html(entry["answer"])
        if "elapsed" in entry:
            bot_html += f'<div class="timing">⏱ {entry["elapsed"]:.2f}s</div>'
        messages.append({"role": "assistant", "content": bot_html})
    return messages


# ---------------------------------------------------------------------------
# Backend helpers
# ---------------------------------------------------------------------------

def _get_pipeline(pipeline_state: dict, index_name: str, k: int, model: str, base_url: str):
    """Return a QueryPipeline, (re)creating it if settings changed."""
    key = (index_name, k, model, base_url)
    if pipeline_state.get("key") != key or pipeline_state.get("instance") is None:
        pipeline_state["instance"] = QueryPipeline(
            index_name=index_name, k=k, model=model, base_url=base_url
        )
        pipeline_state["key"] = key
    return pipeline_state["instance"]


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

def handle_query(
    question: str,
    chat_history: list,
    pipeline_state: dict,
    language: str,
    num_results: int,
    index_name: str,
    ollama_model: str,
    ollama_url: str,
    ingested: bool,
):
    """Process a user question; return (chatbot_messages, cleared_input, answer_html, new_history)."""
    if not question or not question.strip():
        return _history_to_messages(chat_history), "", "", chat_history

    if not ingested:
        err = {"error": "No documents ingested yet. Please ingest a document first (Ingest tab)."}
        new_history = chat_history + [{"question": question, "answer": err}]
        return _history_to_messages(new_history), "", _format_answer_html(err), new_history

    try:
        pipeline = _get_pipeline(
            pipeline_state,
            index_name.strip() or "legal_docs",
            num_results,
            ollama_model.strip(),
            ollama_url.strip(),
        )
    except Exception as e:
        err = {"error": f"Pipeline init failed: {e}"}
        return _history_to_messages(chat_history), "", _format_answer_html(err), chat_history

    start = time.time()
    try:
        answer = pipeline.query(question, language=language, k=num_results)
    except Exception as e:
        answer = {"error": f"Query failed: {e}"}
    elapsed = time.time() - start

    entry = {"question": question, "answer": answer, "elapsed": elapsed}
    new_history = chat_history + [entry]
    answer_html = _format_answer_html(answer)
    if "error" not in answer:
        answer_html += f'<div class="timing">⏱ {elapsed:.2f}s</div>'

    return _history_to_messages(new_history), "", answer_html, new_history


def handle_ingest(
    file_obj,
    doc_name: str,
    index_name: str,
    pipeline_state: dict,
):
    """Ingest an uploaded document."""
    if file_obj is None:
        return gr.update(value="⚠️ Please upload a document first."), False

    try:
        file_path = file_obj.name if hasattr(file_obj, "name") else str(file_obj)
        effective_name = doc_name.strip() if doc_name.strip() else None
        idx = index_name.strip() if index_name.strip() else "legal_docs"
        docs = ingest_document(file_path, document_name=effective_name, index_name=idx, append=True)
        # invalidate cached pipeline so it reloads the updated index
        pipeline_state.clear()
        msg = (
            f'<div style="color:#22c55e;padding:12px;border-left:3px solid #22c55e;'
            f'background:#0d0d0d;border-radius:0 6px 6px 0;">'
            f'✅ <strong>{len(docs)}</strong> chunks ingested into <em>{idx}</em>.</div>'
        )
        return gr.update(value=msg), True
    except Exception as e:
        msg = (
            f'<div style="color:#ef4444;padding:12px;border-left:3px solid #ef4444;'
            f'background:#0d0d0d;border-radius:0 6px 6px 0;">'
            f'❌ Ingestion failed: {e}</div>'
        )
        return gr.update(value=msg), False


def update_status(ingested: bool, index_name: str):
    idx = index_name.strip() or "legal_docs"
    if ingested:
        return (
            f'<div class="status-badge"><span class="dot-green"></span>{idx} · ready</div>'
        )
    return '<div class="status-badge"><span class="dot-gray"></span>no index loaded</div>'


# ---------------------------------------------------------------------------
# Build the Gradio interface
# ---------------------------------------------------------------------------

def build_app() -> gr.Blocks:
    with gr.Blocks(
        css=CUSTOM_CSS,
        title="Legal Document QA",
        theme=gr.themes.Base(
            primary_hue="neutral",
            secondary_hue="neutral",
            neutral_hue="neutral",
            font=[gr.themes.GoogleFont("Inter"), "sans-serif"],
        ),
    ) as demo:

        # ── Shared state ──────────────────────────────────────────────
        pipeline_state = gr.State({})   # mutable dict holding QueryPipeline instance
        chat_history   = gr.State([])   # list of {question, answer, elapsed}
        ingested       = gr.State(True) # assume an index may already exist

        # ── Header ────────────────────────────────────────────────────
        gr.HTML("""
        <div id="app-header">
          <div id="app-title">⚖️ Legal Document QA</div>
          <div id="app-subtitle">Bilingual (English + Hindi) · Powered by Endee hybrid search &amp; Mistral</div>
        </div>
        """)

        # ── Tabs ──────────────────────────────────────────────────────
        with gr.Tabs(elem_classes="tab-nav"):

            # ════════════════════════════════════════════════════════
            # TAB 1 – Query
            # ════════════════════════════════════════════════════════
            with gr.Tab("🔍 Query"):
                with gr.Row():
                    # Left column – controls
                    with gr.Column(scale=1, min_width=220):
                        gr.HTML('<div class="panel-card">')
                        gr.Markdown("**Query Settings**")

                        language = gr.Radio(
                            choices=["both", "english", "hindi"],
                            value="both",
                            label="Answer Language",
                            info="English + Hindi, English only, or Hindi only",
                        )
                        num_results = gr.Slider(
                            minimum=3, maximum=10, value=5, step=1,
                            label="Retrieved Chunks",
                        )
                        status_html = gr.HTML(
                            '<div class="status-badge"><span class="dot-gray"></span>no index loaded</div>'
                        )
                        clear_btn = gr.Button("🗑 Clear Chat", elem_classes="btn-secondary", size="sm")
                        gr.HTML("</div>")

                    # Right column – chat
                    with gr.Column(scale=3):
                        chatbot = gr.Chatbot(
                            elem_id="chatbox",
                            label="Conversation",
                            height=420,
                            type="messages",
                            bubble_full_width=False,
                            render_markdown=False,
                        )
                        with gr.Row():
                            question_input = gr.Textbox(
                                placeholder="Ask a question about your legal documents…",
                                show_label=False,
                                lines=1,
                                scale=5,
                            )
                            ask_btn = gr.Button("Ask", elem_classes="btn-primary", scale=1, size="lg")

                        answer_display = gr.HTML(label="Answer")

                # Settings row (collapsible) reused across tab
                with gr.Accordion("⚙️ Connection Settings", open=False, elem_classes="gr-accordion"):
                    with gr.Row():
                        q_ollama_model = gr.Textbox(
                            label="Ollama Model",
                            value=os.getenv("OLLAMA_MODEL", "mistral"),
                            interactive=True,
                        )
                        q_ollama_url = gr.Textbox(
                            label="Ollama URL",
                            value=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                            interactive=True,
                        )
                        q_index_name = gr.Textbox(
                            label="Endee Index",
                            value=os.getenv("ENDEE_INDEX_NAME", "legal_docs"),
                            interactive=True,
                        )

            # ════════════════════════════════════════════════════════
            # TAB 2 – Ingest
            # ════════════════════════════════════════════════════════
            with gr.Tab("📄 Ingest"):
                with gr.Row():
                    with gr.Column(scale=2):
                        gr.HTML('<div class="panel-card">')
                        gr.Markdown("### Upload Legal Document")
                        gr.Markdown(
                            "Supported formats: **PDF**, **DOCX**, **TXT**  \n"
                            "The document will be chunked, embedded, and stored in Endee."
                        )
                        upload_file = gr.File(
                            label="Drop file here or click to upload",
                            file_types=[".pdf", ".docx", ".txt"],
                            elem_classes="gr-file-upload",
                        )
                        ingest_doc_name = gr.Textbox(
                            label="Document Name (optional)",
                            placeholder="e.g. Abdul Wahid vs State of Rajasthan",
                        )
                        ingest_index = gr.Textbox(
                            label="Endee Index",
                            value=os.getenv("ENDEE_INDEX_NAME", "legal_docs"),
                        )
                        ingest_btn = gr.Button("⬆ Ingest Document", elem_classes="btn-primary", size="lg")
                        gr.HTML("</div>")

                    with gr.Column(scale=1):
                        gr.HTML('<div class="panel-card">')
                        gr.Markdown("### Ingestion Status")
                        ingest_status = gr.HTML(
                            '<div style="color:#555555;font-size:13px;">Upload a document and click Ingest.</div>'
                        )
                        gr.HTML("</div>")

                        gr.HTML('<div class="panel-card">')
                        gr.Markdown("### Tips")
                        gr.Markdown(
                            "- Name your document clearly for better source citations  \n"
                            "- Use `append=True` to add to an existing index  \n"
                            "- Larger PDFs take longer to embed  \n"
                            "- Supported document types: Judgment, NDA, MOU, Contract…"
                        )
                        gr.HTML("</div>")

            # ════════════════════════════════════════════════════════
            # TAB 3 – Settings
            # ════════════════════════════════════════════════════════
            with gr.Tab("⚙️ Settings"):
                with gr.Row():
                    with gr.Column():
                        gr.HTML('<div class="panel-card">')
                        gr.Markdown("### Ollama Configuration")
                        s_ollama_model = gr.Textbox(
                            label="Model Name",
                            value=os.getenv("OLLAMA_MODEL", "mistral"),
                            info="Ollama model to use for question answering",
                        )
                        s_ollama_url = gr.Textbox(
                            label="Ollama Base URL",
                            value=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                            info="URL where Ollama is running",
                        )
                        gr.HTML("</div>")

                    with gr.Column():
                        gr.HTML('<div class="panel-card">')
                        gr.Markdown("### Endee Configuration")
                        s_index_name = gr.Textbox(
                            label="Index Name",
                            value=os.getenv("ENDEE_INDEX_NAME", "legal_docs"),
                            info="Name of the Endee vector index",
                        )
                        s_endee_url = gr.Textbox(
                            label="Endee Base URL",
                            value=os.getenv("ENDEE_BASE_URL", "http://localhost:8080/api/v1"),
                            info="URL of the Endee server",
                        )
                        gr.HTML("</div>")

                with gr.Row():
                    with gr.Column():
                        gr.HTML('<div class="panel-card">')
                        gr.Markdown("### Advanced")
                        s_embedding = gr.Textbox(
                            label="Embedding Model",
                            value=os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5"),
                            info="HuggingFace model used for dense embeddings",
                            interactive=False,
                        )
                        apply_btn = gr.Button("Apply Settings", elem_classes="btn-primary", size="lg")
                        settings_status = gr.HTML("")
                        gr.HTML("</div>")

        # ── Footer ────────────────────────────────────────────────────
        gr.HTML("""
        <div style="border-top:1px solid #1a1a1a;margin-top:24px;padding:14px 24px;
                    display:flex;justify-content:space-between;align-items:center;
                    font-size:11px;color:#333333;">
          <span>Legal Document QA · v2.0 · Gradio UI</span>
          <span>Endee · BGE-large-en-v1.5 · Mistral</span>
        </div>
        """)

        # ── Wire-up events ────────────────────────────────────────────

        _ask_inputs = [
            question_input, chat_history, pipeline_state, language, num_results,
            q_index_name, q_ollama_model, q_ollama_url, ingested,
        ]
        _ask_outputs = [chatbot, question_input, answer_display, chat_history]

        # Ask button / Enter key
        ask_btn.click(fn=handle_query, inputs=_ask_inputs, outputs=_ask_outputs)
        question_input.submit(fn=handle_query, inputs=_ask_inputs, outputs=_ask_outputs)

        # Clear chat
        clear_btn.click(
            fn=lambda: ([], [], "", ""),
            inputs=[],
            outputs=[chatbot, chat_history, question_input, answer_display],
        )

        # Status badge update whenever ingested or index name changes
        for trigger_component in [ingested, q_index_name]:
            trigger_component.change(
                fn=update_status,
                inputs=[ingested, q_index_name],
                outputs=[status_html],
            )

        # Ingest
        ingest_btn.click(
            fn=handle_ingest,
            inputs=[upload_file, ingest_doc_name, ingest_index, pipeline_state],
            outputs=[ingest_status, ingested],
        )

        # Apply settings: copy Settings tab values → Query tab fields + reset pipeline
        def apply_settings(model, url, idx, p_state):
            p_state.clear()
            return (
                gr.update(value=model),
                gr.update(value=url),
                gr.update(value=idx),
                gr.update(value=idx),
                '<div style="color:#22c55e;font-size:13px;">✅ Settings applied.</div>',
            )

        apply_btn.click(
            fn=apply_settings,
            inputs=[s_ollama_model, s_ollama_url, s_index_name, pipeline_state],
            outputs=[q_ollama_model, q_ollama_url, q_index_name, ingest_index, settings_status],
        )

    return demo


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app = build_app()
    app.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("GRADIO_PORT", "7860")),
        share=False,
    )
