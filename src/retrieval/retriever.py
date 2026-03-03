"""Hybrid BM25 + FAISS retriever with Reciprocal Rank Fusion (RRF)."""

from typing import Dict, List, Optional, Tuple

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi


# ---------------------------------------------------------------------------
# Reciprocal Rank Fusion
# ---------------------------------------------------------------------------
def _rrf_score(rank: int, k: int = 60) -> float:
    """Reciprocal Rank Fusion score: 1 / (k + rank)."""
    return 1.0 / (k + rank)


def reciprocal_rank_fusion(
    ranked_lists: List[List[Document]],
    k: int = 60,
) -> List[Tuple[Document, float]]:
    """Fuse multiple ranked lists using RRF.

    Args:
        ranked_lists: Each inner list is a ranked retrieval result.
        k: RRF constant (default 60).

    Returns:
        List of (Document, score) sorted by descending fused score.
    """
    scores: Dict[str, float] = {}
    docs_by_id: Dict[str, Document] = {}

    for ranked in ranked_lists:
        for rank, doc in enumerate(ranked, start=1):
            doc_id = doc.page_content[:100]  # Use content prefix as ID
            scores[doc_id] = scores.get(doc_id, 0.0) + _rrf_score(rank, k)
            docs_by_id[doc_id] = doc

    fused = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [(docs_by_id[doc_id], score) for doc_id, score in fused]


# ---------------------------------------------------------------------------
# BM25 wrapper
# ---------------------------------------------------------------------------
class BM25Retriever:
    """Simple BM25 retriever backed by rank-bm25."""

    def __init__(self, documents: List[Document]):
        self.documents = documents
        tokenized = [doc.page_content.lower().split() for doc in documents]
        self.bm25 = BM25Okapi(tokenized)

    def retrieve(self, query: str, k: int = 5) -> List[Document]:
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        top_k_indices = sorted(
            range(len(scores)), key=lambda i: scores[i], reverse=True
        )[:k]
        return [self.documents[i] for i in top_k_indices]


# ---------------------------------------------------------------------------
# Hybrid retriever
# ---------------------------------------------------------------------------
class HybridRetriever:
    """Hybrid BM25 + FAISS retriever with RRF fusion.

    Args:
        vectorstore: A FAISS vector store instance.
        documents:   The same documents used to build the vector store,
                     needed for BM25 indexing.
        k:           Number of results to return after fusion.
        bm25_k:      Number of results each retriever fetches before fusion.
    """

    def __init__(
        self,
        vectorstore: FAISS,
        documents: List[Document],
        k: int = 5,
        bm25_k: int = 10,
    ):
        self.vectorstore = vectorstore
        self.bm25_retriever = BM25Retriever(documents)
        self.k = k
        self.bm25_k = bm25_k

    def retrieve(
        self, query: str, k: Optional[int] = None
    ) -> List[Document]:
        """Retrieve documents using hybrid BM25 + FAISS with RRF.

        Args:
            query: User query string.
            k: Override the default number of results.

        Returns:
            Ranked list of Documents.
        """
        top_k = k if k is not None else self.k
        fetch_k = max(self.bm25_k, top_k * 2)

        # Dense retrieval (FAISS)
        dense_results: List[Document] = self.vectorstore.similarity_search(
            query, k=fetch_k
        )

        # Sparse retrieval (BM25)
        sparse_results: List[Document] = self.bm25_retriever.retrieve(
            query, k=fetch_k
        )

        # RRF fusion
        fused = reciprocal_rank_fusion([dense_results, sparse_results])
        return [doc for doc, _ in fused[:top_k]]
