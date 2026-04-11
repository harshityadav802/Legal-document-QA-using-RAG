"""
FastAPI backend for the Legal Document QA system.
Wraps the existing Python pipeline and exposes REST endpoints
consumed by the React frontend.
"""

import json
import os
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Make sure the project root is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Document registry – persisted as a JSON file so restarts retain the list.
# ---------------------------------------------------------------------------
_REGISTRY_PATH = Path(os.getenv("DOC_REGISTRY_PATH", "data/doc_registry.json"))
_REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_registry() -> List[Dict]:
    if _REGISTRY_PATH.exists():
        try:
            return json.loads(_REGISTRY_PATH.read_text())
        except Exception:
            return []
    return []


def _save_registry(docs: List[Dict]) -> None:
    _REGISTRY_PATH.write_text(json.dumps(docs, indent=2))


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Legal Document QA API",
    description="REST API for Legal Document QA using RAG (Endee + Qwen)",
    version="1.0.0",
)

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Lazy-loaded query pipeline (initialised on first use)
# ---------------------------------------------------------------------------
_pipeline = None


def _get_pipeline(index_name: Optional[str] = None, k: int = 5):
    global _pipeline
    if _pipeline is None:
        from src.pipeline.query import QueryPipeline

        _pipeline = QueryPipeline(
            index_name=index_name or os.getenv("ENDEE_INDEX_NAME", "legal_docs"),
            k=k,
            model=os.getenv("OLLAMA_MODEL", "qwen3.5:4b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )
    return _pipeline


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    question: str
    language: str = "both"
    k: int = 5
    index_name: Optional[str] = None


class QueryResponse(BaseModel):
    english: Optional[str] = None
    hindi: Optional[str] = None
    sources: List[Dict] = []
    error: Optional[str] = None


class DocumentMeta(BaseModel):
    id: str
    name: str
    filename: str
    index_name: str
    chunk_count: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
def health_check():
    return {"status": "ok"}


# --- Document upload --------------------------------------------------------


@app.post("/api/documents/upload", response_model=DocumentMeta)
async def upload_document(
    file: UploadFile = File(...),
    document_name: Optional[str] = Form(None),
    index_name: Optional[str] = Form(None),
):
    """Ingest a document (PDF, DOCX, TXT) into the vector store."""
    from src.pipeline.ingestion import ingest_document

    suffix = Path(file.filename).suffix if file.filename else ".txt"
    allowed = {".pdf", ".docx", ".txt"}
    if suffix.lower() not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {allowed}",
        )

    idx = (index_name or "").strip() or os.getenv("ENDEE_INDEX_NAME", "legal_docs")
    effective_name = (document_name or "").strip() or None

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        docs = ingest_document(
            tmp_path,
            document_name=effective_name,
            index_name=idx,
            append=True,
        )
    except Exception as exc:
        os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    # Invalidate cached pipeline so it reloads the updated index
    global _pipeline
    _pipeline = None

    doc_id = str(uuid.uuid4())
    display_name = effective_name or Path(file.filename or "document").stem.replace("_", " ").title()
    entry: Dict = {
        "id": doc_id,
        "name": display_name,
        "filename": file.filename or "document",
        "index_name": idx,
        "chunk_count": len(docs),
    }
    registry = _load_registry()
    registry.append(entry)
    _save_registry(registry)

    return entry


# --- List documents ---------------------------------------------------------


@app.get("/api/documents", response_model=List[DocumentMeta])
def list_documents():
    """Return all ingested documents."""
    return _load_registry()


# --- Delete document --------------------------------------------------------


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str):
    """Remove a document entry from the registry.

    Note: This only removes the metadata entry. Full re-indexing would be
    required to purge the underlying vectors (not yet supported by the
    Endee API exposed here).
    """
    registry = _load_registry()
    new_registry = [d for d in registry if d["id"] != doc_id]
    if len(new_registry) == len(registry):
        raise HTTPException(status_code=404, detail="Document not found")
    _save_registry(new_registry)

    global _pipeline
    _pipeline = None

    return {"deleted": doc_id}


# --- Query ------------------------------------------------------------------


@app.post("/api/query", response_model=QueryResponse)
def query_documents(req: QueryRequest):
    """Submit a question and receive bilingual answers with source citations."""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question must not be empty")

    try:
        pipeline = _get_pipeline(index_name=req.index_name, k=req.k)
        result = pipeline.query(req.question, language=req.language, k=req.k)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if "error" in result and result["error"]:
        raise HTTPException(status_code=500, detail=result["error"])

    return QueryResponse(
        english=result.get("english"),
        hindi=result.get("hindi"),
        sources=result.get("sources", []),
    )


# --- Suggestions ------------------------------------------------------------

_SUGGESTION_TEMPLATES = [
    "What are the key obligations under this agreement?",
    "What are the termination clauses?",
    "What are the payment terms?",
    "What are the confidentiality provisions?",
    "What is the jurisdiction for dispute resolution?",
    "What are the intellectual property rights?",
    "What are the liability limitations?",
    "What are the penalties for breach of contract?",
    "What is the duration of this agreement?",
    "What are the indemnification clauses?",
    "Who are the parties involved?",
    "What are the governing law provisions?",
]


@app.get("/api/query/suggestions")
def get_suggestions(q: Optional[str] = None) -> List[str]:
    """Return auto-complete suggestions filtered by optional prefix."""
    if not q:
        return _SUGGESTION_TEMPLATES[:6]
    q_lower = q.lower()
    matches = [s for s in _SUGGESTION_TEMPLATES if q_lower in s.lower()]
    return matches[:6] if matches else _SUGGESTION_TEMPLATES[:3]
