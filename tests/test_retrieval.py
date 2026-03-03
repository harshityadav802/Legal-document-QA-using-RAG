"""Tests for the retrieval module (BM25, RRF, HybridRetriever).

These tests use mock/stub objects so no external services are needed.
"""

import pytest
from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from src.retrieval.retriever import (
    BM25Retriever,
    HybridRetriever,
    _rrf_score,
    reciprocal_rank_fusion,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_doc(content: str, **metadata) -> Document:
    return Document(page_content=content, metadata=metadata)


DOCS = [
    make_doc("The contract terminates after 30 days written notice.", section="termination"),
    make_doc("All fees must be paid within 30 days of invoice date.", section="payment"),
    make_doc("Confidential information shall not be disclosed to third parties.", section="confidentiality"),
    make_doc("The service provider shall deliver the software by December 31.", section="delivery"),
    make_doc("Governing law shall be the laws of India.", section="general"),
]


# ---------------------------------------------------------------------------
# RRF tests
# ---------------------------------------------------------------------------
class TestRrfScore:
    def test_positive_score(self):
        score = _rrf_score(1)
        assert score > 0

    def test_higher_rank_lower_score(self):
        assert _rrf_score(1) > _rrf_score(2) > _rrf_score(10)

    def test_custom_k(self):
        score_k60 = _rrf_score(1, k=60)
        score_k10 = _rrf_score(1, k=10)
        assert score_k10 > score_k60  # smaller k → higher score


class TestReciprocalRankFusion:
    def test_returns_sorted_list(self):
        list1 = DOCS[:3]
        list2 = DOCS[2:]
        fused = reciprocal_rank_fusion([list1, list2])
        scores = [score for _, score in fused]
        assert scores == sorted(scores, reverse=True)

    def test_document_in_both_lists_gets_higher_score(self):
        # DOCS[2] appears in both lists
        list1 = [DOCS[0], DOCS[1], DOCS[2]]
        list2 = [DOCS[2], DOCS[3], DOCS[4]]
        fused = reciprocal_rank_fusion([list1, list2])
        # The doc in both lists should appear near the top
        top_doc, top_score = fused[0]
        assert top_doc.page_content == DOCS[2].page_content

    def test_empty_lists(self):
        fused = reciprocal_rank_fusion([[], []])
        assert fused == []

    def test_single_list(self):
        fused = reciprocal_rank_fusion([DOCS])
        assert len(fused) == len(DOCS)

    def test_deduplication(self):
        list1 = [DOCS[0], DOCS[1]]
        list2 = [DOCS[0], DOCS[2]]
        fused = reciprocal_rank_fusion([list1, list2])
        contents = [doc.page_content[:100] for doc, _ in fused]
        # DOCS[0] should appear only once
        assert contents.count(DOCS[0].page_content[:100]) == 1


# ---------------------------------------------------------------------------
# BM25Retriever tests
# ---------------------------------------------------------------------------
class TestBM25Retriever:
    def setup_method(self):
        self.retriever = BM25Retriever(DOCS)

    def test_returns_documents(self):
        results = self.retriever.retrieve("termination notice", k=3)
        assert len(results) <= 3
        assert all(isinstance(d, Document) for d in results)

    def test_relevant_doc_ranked_first_for_termination(self):
        results = self.retriever.retrieve("termination contract 30 days", k=5)
        # The termination doc should rank highly
        contents = [r.page_content for r in results]
        assert any("terminat" in c.lower() for c in contents[:3])

    def test_k_limits_results(self):
        results = self.retriever.retrieve("any query", k=2)
        assert len(results) <= 2

    def test_k_larger_than_corpus(self):
        results = self.retriever.retrieve("query", k=100)
        assert len(results) <= len(DOCS)

    def test_different_queries_different_results(self):
        r1 = self.retriever.retrieve("termination", k=1)
        r2 = self.retriever.retrieve("payment fees invoice", k=1)
        # Top results should differ
        assert r1[0].page_content != r2[0].page_content


# ---------------------------------------------------------------------------
# HybridRetriever tests
# ---------------------------------------------------------------------------
class TestHybridRetriever:
    def _make_mock_vectorstore(self, return_docs=None):
        """Create a mock FAISS vectorstore."""
        mock_vs = MagicMock()
        mock_vs.similarity_search.return_value = return_docs or DOCS[:3]
        return mock_vs

    def test_returns_documents(self):
        mock_vs = self._make_mock_vectorstore(DOCS[:3])
        retriever = HybridRetriever(
            vectorstore=mock_vs, documents=DOCS, k=3
        )
        results = retriever.retrieve("termination")
        assert len(results) <= 3
        assert all(isinstance(d, Document) for d in results)

    def test_calls_vectorstore(self):
        mock_vs = self._make_mock_vectorstore()
        retriever = HybridRetriever(
            vectorstore=mock_vs, documents=DOCS, k=3
        )
        retriever.retrieve("test query")
        mock_vs.similarity_search.assert_called_once()

    def test_k_parameter_respected(self):
        mock_vs = self._make_mock_vectorstore(DOCS)
        retriever = HybridRetriever(
            vectorstore=mock_vs, documents=DOCS, k=2
        )
        results = retriever.retrieve("query", k=2)
        assert len(results) <= 2

    def test_override_k_in_retrieve(self):
        mock_vs = self._make_mock_vectorstore(DOCS)
        retriever = HybridRetriever(
            vectorstore=mock_vs, documents=DOCS, k=5
        )
        results = retriever.retrieve("query", k=1)
        assert len(results) <= 1

    def test_fuses_sparse_and_dense(self):
        """HybridRetriever should use both BM25 and dense results."""
        mock_vs = self._make_mock_vectorstore([DOCS[0], DOCS[1], DOCS[2]])
        retriever = HybridRetriever(
            vectorstore=mock_vs, documents=DOCS, k=5
        )
        # The BM25 retriever has access to all 5 docs
        # so fusion should potentially bring in more than just dense results
        results = retriever.retrieve("payment fees invoice")
        assert len(results) >= 1
