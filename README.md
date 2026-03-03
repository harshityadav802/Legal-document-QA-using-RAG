# ⚖️ Legal Document QA using RAG

A **production-ready, bilingual (Hindi + English) Legal Document Question & Answer** system built with Retrieval-Augmented Generation (RAG).  
**No paid API required** — uses [Ollama](https://ollama.com/) (Mistral / LLaMA3) for the LLM and HuggingFace `BAAI/bge-large-en-v1.5` for embeddings.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| 🆓 **100% Free** | Ollama (local LLM) + HuggingFace embeddings — zero API costs |
| 🌐 **Bilingual** | Every answer in **English** + **simple Hindi** (everyday language for common people) |
| 📄 **Smart Segmentation** | 5-stage legal segmentation pipeline with hierarchy-aware chunking |
| 🔍 **Hybrid Retrieval** | BM25 + FAISS with Reciprocal Rank Fusion for best-of-both retrieval |
| 🏗️ **Production-ready** | Clean pipeline architecture, Streamlit UI, tests |

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.10+**
2. **Ollama** installed and running:
   ```bash
   # Install Ollama: https://ollama.com/download
   ollama pull mistral   # or: ollama pull llama3
   ```

### Installation

```bash
# Clone the repo
git clone https://github.com/harshityadav802/Legal-document-QA-using-RAG.git
cd Legal-document-QA-using-RAG

# Install dependencies
pip install -r requirements.txt

# Copy env file
cp .env.example .env
```

### Run the Streamlit App

```bash
streamlit run app/app.py
```

Then open `http://localhost:8501` in your browser.

1. Click **"Load Sample Contract"** in the sidebar to try the demo
2. Or upload your own `.txt` / `.pdf` / `.docx` legal document
3. Ask any question in English or Hindi
4. Get answers in both languages

---

## 🏗️ Architecture

```
Legal-document-QA-using-RAG/
├── src/
│   ├── segmentation/          ← 5-stage legal document segmentation
│   │   ├── preprocessor.py    ← Clean raw text (headers/footers, unicode, etc.)
│   │   ├── legal_segmenter.py ← Core 5-stage pipeline (MOST IMPORTANT)
│   │   ├── section_classifier.py ← Label section types
│   │   └── utils.py           ← Token counting, sentence splitting, overlap
│   ├── embeddings/
│   │   └── embedder.py        ← BAAI/bge-large-en-v1.5 (free)
│   ├── vectorstore/
│   │   └── store.py           ← FAISS build/load
│   ├── retrieval/
│   │   └── retriever.py       ← Hybrid BM25 + FAISS with RRF fusion
│   ├── llm/
│   │   └── qa_chain.py        ← Ollama-based bilingual QA
│   ├── translation/
│   │   └── hindi_translator.py ← Hindi simplification
│   └── pipeline/
│       ├── ingest.py          ← Document ingestion pipeline
│       └── query.py           ← Query pipeline
├── app/
│   └── app.py                 ← Streamlit UI
├── data/
│   └── sample_contract.txt    ← Sample service agreement
├── notebooks/
│   └── demo.ipynb             ← Step-by-step demo
└── tests/
    ├── test_segmentation.py
    ├── test_retrieval.py
    └── test_qa_chain.py
```

---

## 📋 5-Stage Segmentation Pipeline

The core of the system is the `legal_segmenter.py` which processes legal documents in 5 stages:

### Stage 1 — Structure Detection
Identifies all legal heading patterns (Article, Section, Sub-section, WHEREAS, Schedules, etc.) using regex.

### Stage 2 — Hierarchy Building
Builds a tree: `Document → Article → Section → Sub-section → Paragraph`  
Every chunk carries a full breadcrumb: `"Agreement > Article III > Section 3.2"`

### Stage 3 — Semantic Boundary Detection
- Never splits mid-sentence
- Keeps definition sentences together (`"X means..."`)
- Preserves cross-references (`"as defined in Section 5.2"`)
- Marks operative clauses (`shall`, `must`, `agrees to`)

### Stage 4 — Smart Chunk Sizing
- Target: **256 tokens** | Maximum: **512 tokens** | Minimum: **50 tokens**
- **50-token overlap** between consecutive chunks
- Merges tiny chunks, splits oversized chunks at sentence boundaries

### Stage 5 — Context Header
Every chunk gets a metadata header:
```
[Document: Service Agreement | Section: 3.2 Termination | Type: TERMINATION]
```

---

## 🌐 Bilingual Answering

Every answer is provided in **both English and simple Hindi**:

> **English**: "The contract terminates after 30 days' written notice."
>
> **हिंदी**: "यह अनुबंध 30 दिन पहले लिखित सूचना देने पर समाप्त हो जाएगा। मतलब, अगर कोई भी पक्ष अनुबंध खत्म करना चाहे, तो उसे 30 दिन पहले लिखकर बताना होगा।"

Hindi is in **everyday language** — not legal Hindi — so it's understandable for farmers, shopkeepers, and daily wage workers.

---

## 🔧 Configuration

Copy `.env.example` to `.env` and adjust as needed:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral          # or llama3
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
VECTORSTORE_PATH=data/vectorstore
```

---

## 🧪 Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=src --cov-report=term-missing
```

Tests do **not** require Ollama or internet access — all LLM calls are mocked.

---

## 📓 Demo Notebook

Open `notebooks/demo.ipynb` for a step-by-step walkthrough of the entire pipeline.

```bash
jupyter notebook notebooks/demo.ipynb
```

---

## 🛠️ Programmatic Usage

### Ingest a document

```python
from src.pipeline.ingest import ingest_document

docs = ingest_document(
    "path/to/contract.pdf",
    document_name="Service Agreement 2024",
)
```

### Query

```python
from src.pipeline.query import QueryPipeline

pipeline = QueryPipeline(all_docs=docs)

answer = pipeline.query(
    "What are the termination conditions?",
    language="both",   # 'english', 'hindi', or 'both'
)
print(answer["english"])
print(answer["hindi"])
```

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `langchain-community` | LangChain integrations (Ollama, HuggingFace, FAISS) |
| `sentence-transformers` | BAAI/bge-large-en-v1.5 embeddings |
| `faiss-cpu` | Dense vector search |
| `rank-bm25` | Sparse BM25 retrieval |
| `ollama` | Local LLM inference |
| `streamlit` | Web UI |
| `pypdf` | PDF parsing |
| `python-docx` | Word document parsing |

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.
