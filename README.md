# Legal Document QA using RAG

A bilingual (English + Hindi) Question Answering system for Indian legal documents. Built with Retrieval-Augmented Generation, using Endee as the vector database.

Ask questions about Supreme Court judgments, contracts, NDAs, and other legal documents in plain language. Get answers in both English and Hindi.

GitHub: https://github.com/harshityadav802/Legal-document-QA-using-RAG

---

## Problem Statement

India has over 55 million pending court cases. Legal documents are lengthy, complex. And, Finding specific information in a large judgment takes hours. Using Keyword search fails because it does not understand meaning but it only matches words.

This system solves that by understanding the semantic content of legal documents and answering questions accurately using only the document content, in both English and simple Hindi.

---

## How Endee is Used

Endee is the core vector database of this project. It stores dense semantic vectors and sparse BM25 vectors for every document chunk, and performs hybrid search in a single server-side call.

Creating the index:
```python
client.create_index(
    name="legal_docs",
    dimension=1024,
    space_type="cosine",
    precision=Precision.INT8,
    sparse_model="endee_bm25"
)
```

Storing document chunks with both dense and sparse vectors:
```python
index.upsert([{
    "id": "judgment_42",
    "vector": dense_embedding,
    "sparse_indices": bm25_embedding.indices,
    "sparse_values": bm25_embedding.values,
    "meta": {
        "page_content": chunk_text,
        "section": "JUDGMENT",
        "document_name": "Abdul Wahid vs State of Rajasthan"
    }
}])
```

Querying with hybrid search:
```python
results = index.query(
    vector=dense_query_vector,
    sparse_indices=bm25_query.indices,
    sparse_values=bm25_query.values,
    top_k=5
)
```

This replaces the previous setup of FAISS + in-process BM25Okapi + manual Reciprocal Rank Fusion. Endee handles all three in one server-side call.

---

## System Architecture

```
Legal Document (PDF / DOCX / TXT)
        |
        v
preprocessor.py
  - Unicode normalisation (preserves Devanagari)
  - Remove headers, footers, page numbers
  - Fix broken lines from PDF extraction
  - Detect document type (Judgment, NDA, MOU, Contract...)
        |
        v
legal_segmenter.py
  - Detect legal headings (FACTS, JUDGMENT, ORDER, WHEREAS, Article IV...)
  - Split into token-aware chunks (50-600 tokens)
  - Merge short chunks, add overlap between adjacent chunks
        |
        |---> BGE-large-en-v1.5  -->  dense vector (1024-dim)
        |---> Endee BM25 model   -->  sparse vector
                    |
                    v
             Endee index (cosine, INT8, hybrid)
                    |
                    v
            User asks a question
                    |
        |--->  BGE embed_query()   -->  dense query vector
        |--->  Endee BM25          -->  sparse query vector
                    |
                    v
        Endee hybrid search (top-5 chunks)
                    |
                    v
        LegalQAChain - Qwen 3.5:4b via Ollama
                    |
                    v
        English answer + Hindi answer + Sources
```

---

## Project Structure

```
Legal-document-QA-using-RAG/
├── app/
│   └── app.py                    Streamlit web interface
├── src/
│   ├── embeddings/
│   │   └── embedder.py           BGE-large-en-v1.5 singleton embedder
│   ├── segmentation/
│   │   ├── preprocessor.py       Text cleaning and document type detection
│   │   ├── legal_segmenter.py    Legal heading detection and chunking
│   │   ├── section_classifier.py Section type labeling
│   │   └── utils.py              Token counting, sentence splitting, overlap
│   ├── vectorstore/
│   │   └── store.py              Endee index build, load, add
│   ├── retrieval/
│   │   └── retriever.py          EndeeHybridRetriever (dense + BM25)
│   ├── llm/
│   │   └── qa_chain.py           LegalQAChain with English and Hindi prompts
│   ├── pipeline/
│   │   ├── ingestion.py          Document ingestion pipeline
│   │   └── query.py              End-to-end query pipeline
│   └── ingestion.py              Ingest single document or full dataset
├── ingest_judgments.py           Bulk ingest script for PDF folders
├── docker-compose.yml            Endee server
├── requirements.txt
└── README.md
```

---

## Setup and Installation

### Requirements

- Python 3.10+
- Docker and Docker Compose
- Ollama with Qwen 3.5:4b

```bash
ollama pull qwen3.5:4b
```

### Step 1 — Star and fork Endee

Star the official repo: https://github.com/endee-io/endee

### Step 2 — Clone this repo

```bash
git clone https://github.com/harshityadav802/Legal-document-QA-using-RAG.git
cd Legal-document-QA-using-RAG
```

### Step 3 — Start Endee server

```bash
docker compose up -d
```

Verify it is running at http://localhost:8080

### Step 4 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 5 — Ingest documents

Put your PDFs in a folder and run:

```bash
python ingest_judgments.py
```

Or ingest a single file:

```python
from src.ingestion import ingest_document
ingest_document("path/to/file.pdf", index_name="legal_docs", append=True)
```

### Step 6 — Run the app

```bash
python -m streamlit run app/app.py
```

Open http://localhost:8501

Select Query existing index to query already-ingested documents, or Upload new document to add and query a new file.

---

## Tech Stack

| Component | Tool |
|---|---|
| Vector database | Endee |
| Dense embeddings | BAAI/bge-large-en-v1.5 |
| Sparse embeddings | Endee BM25 (endee-model) |
| LLM | Qwen 3.5:4b via Ollama |
| Framework | LangChain |
| UI | Streamlit |
| PDF parsing | pypdf |
| DOCX parsing | python-docx |

---

## Supported Document Types

Judgment, NDA, MOU, Service Agreement, Employment Contract, Lease Agreement, Partnership Deed, General Contract

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| ENDEE_INDEX_NAME | legal_docs | Endee index name |
| ENDEE_BASE_URL | http://localhost:8080/api/v1 | Endee server URL |
| ENDEE_AUTH_TOKEN | (empty) | Auth token (optional) |
| OLLAMA_MODEL | qwen3.5:4b | Ollama model name |
| OLLAMA_BASE_URL | http://localhost:11434 | Ollama server URL |
| EMBEDDING_MODEL | BAAI/bge-large-en-v1.5 | Embedding model |

---

## Dataset

Supreme Court of India judgments (1950–2024) from Indian Kanoon.

Dataset: https://www.kaggle.com/datasets/adarshsingh0903/legal-dataset-sc-judgments-india-19502024
The full dataset contains judgments from 1950 to 2025.

---
## Demo

Watch the system in action — ingesting Supreme Court judgments and answering 
questions in English and Hindi using Endee hybrid search.

[![Demo Video](https://img.youtube.com/vi/uLgcHyeKy28/0.jpg)](https://www.youtube.com/watch?v=uLgcHyeKy28)
---
## License

MIT License
