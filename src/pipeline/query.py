"""Query pipeline — retrieves relevant chunks and generates bilingual answers."""

import os
from typing import Dict, List, Optional

from langchain_core.documents import Document

from src.llm.qa_chain import LegalQAChain
from src.retrieval.retriever import HybridRetriever
from src.vectorstore.store import load_vectorstore


class QueryPipeline:
    """End-to-end query pipeline: retrieval → LLM → bilingual answer.

    Args:
        store_path:  Path to the persisted FAISS index.
        all_docs:    All documents (needed for BM25 initialization).
                     If None, BM25 is not used (dense-only retrieval).
        k:           Number of chunks to retrieve.
        model:       Ollama model name.
        base_url:    Ollama server URL.
    """

    def __init__(
        self,
        store_path: Optional[str] = None,
        all_docs: Optional[List[Document]] = None,
        k: int = 5,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        effective_store_path = store_path or os.getenv(
            "VECTORSTORE_PATH", "data/vectorstore"
        )
        self.vectorstore = load_vectorstore(effective_store_path)
        self.k = k

        if all_docs:
            self.retriever = HybridRetriever(
                vectorstore=self.vectorstore,
                documents=all_docs,
                k=k,
            )
        else:
            self.retriever = None  # type: ignore[assignment]

        self.qa_chain = LegalQAChain(model=model, base_url=base_url)

    def query(
        self,
        question: str,
        language: str = "both",
        k: Optional[int] = None,
    ) -> Dict:
        """Answer a question from the ingested documents.

        Args:
            question: The user's question.
            language: 'english', 'hindi', or 'both'.
            k:        Override the default number of retrieved chunks.

        Returns:
            Dictionary with keys:
              - 'english': English answer (if requested)
              - 'hindi':   Hindi answer (if requested)
              - 'sources': List of source metadata dicts
        """
        top_k = k if k is not None else self.k

        # Retrieve
        if self.retriever is not None:
            docs = self.retriever.retrieve(question, k=top_k)
        else:
            docs = self.vectorstore.similarity_search(question, k=top_k)

        # Generate answer
        answer = self.qa_chain.answer(question, docs, language=language)

        # Attach sources
        answer["sources"] = [
            {
                "breadcrumb": doc.metadata.get("breadcrumb", ""),
                "section_type": doc.metadata.get("section_type", ""),
                "document_name": doc.metadata.get("document_name", ""),
                "snippet": doc.page_content[:200],
            }
            for doc in docs
        ]
        return answer
