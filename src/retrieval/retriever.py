from typing import List, Optional

from langchain_core.documents import Document

from src.embeddings.embedder import embed_query
from src.vectorstore.store import EndeeVectorStore

try:
    from endee_model import SparseModel as _SparseModel
    _sparse_model: Optional[_SparseModel] = _SparseModel(model_name="endee/bm25")
    _HYBRID_AVAILABLE = True
except ImportError:
    _sparse_model = None
    _HYBRID_AVAILABLE = False


def _get_query_sparse(query: str):
    if _sparse_model is None:
        return None, None
    embedding = next(_sparse_model.query_embed(query))
    return embedding.indices.tolist(), embedding.values.tolist()


class EndeeHybridRetriever:

    def __init__(
        self,
        vectorstore: EndeeVectorStore,
        k: int = 5,
        ef: int = 128,
    ) -> None:
        self.vectorstore = vectorstore
        self.k = k
        self.ef = ef

        if not _HYBRID_AVAILABLE:
            print(
                "[retriever] WARNING: endee-model not installed. "
                "Falling back to dense-only search.\n"
                "Install with: pip install endee-model"
            )

    def retrieve(self, query: str, k: Optional[int] = None) -> List[Document]:
        if not query.strip():
            return []

        top_k = k if k is not None else self.k
        dense_vector = embed_query(query)
        sparse_indices, sparse_values = _get_query_sparse(query)

        index = self.vectorstore._get_index()

        try:
            if sparse_indices is not None:
                results = index.query(
                    vector=dense_vector,
                    sparse_indices=sparse_indices,
                    sparse_values=sparse_values,
                    top_k=top_k,
                    ef=self.ef,
                )
            else:
                results = index.query(
                    vector=dense_vector,
                    top_k=top_k,
                    ef=self.ef,
                )
        except Exception as exc:
            raise RuntimeError(f"Endee retrieval failed: {exc}") from exc

        docs = []
        for item in results:
            meta = dict(item.get("meta") or {})
            page_content = meta.pop("page_content", "")
            docs.append(Document(page_content=page_content, metadata=meta))
        return docs


class EndeeDenseRetriever:

    def __init__(self, vectorstore: EndeeVectorStore, k: int = 5) -> None:
        self.vectorstore = vectorstore
        self.k = k

    def retrieve(self, query: str, k: Optional[int] = None) -> List[Document]:
        if not query.strip():
            return []
        return self.vectorstore.similarity_search(query, k=k or self.k)


HybridRetriever = EndeeHybridRetriever
