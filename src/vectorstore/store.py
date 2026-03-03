"""FAISS vector store wrapper."""

import os
from typing import List, Optional

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from src.embeddings.embedder import get_embedder


_DEFAULT_STORE_PATH = os.getenv("VECTORSTORE_PATH", "data/vectorstore")


def build_vectorstore(
    documents: List[Document],
    model_name: Optional[str] = None,
    store_path: str = _DEFAULT_STORE_PATH,
    save: bool = True,
) -> FAISS:
    """Build a FAISS vector store from a list of LangChain Documents.

    Args:
        documents:  Documents to index.
        model_name: Embedding model name (defaults to BAAI/bge-large-en-v1.5).
        store_path: Directory to persist the index.
        save:       Whether to persist the index to disk.

    Returns:
        A FAISS vector store instance.
    """
    embedder = get_embedder(model_name) if model_name else get_embedder()
    vectorstore = FAISS.from_documents(documents, embedder)
    if save:
        os.makedirs(store_path, exist_ok=True)
        vectorstore.save_local(store_path)
    return vectorstore


def load_vectorstore(
    store_path: str = _DEFAULT_STORE_PATH,
    model_name: Optional[str] = None,
) -> FAISS:
    """Load a previously saved FAISS index from disk.

    Args:
        store_path: Directory containing the saved index.
        model_name: Embedding model used when building the index.

    Returns:
        A FAISS vector store instance.

    Raises:
        FileNotFoundError: If the store_path does not exist.
    """
    if not os.path.exists(store_path):
        raise FileNotFoundError(
            f"No vector store found at '{store_path}'. "
            "Run the ingest pipeline first."
        )
    embedder = get_embedder(model_name) if model_name else get_embedder()
    return FAISS.load_local(
        store_path, embedder, allow_dangerous_deserialization=True
    )
