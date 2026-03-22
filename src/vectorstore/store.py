import os
from typing import List, Optional

from endee import Endee, Precision
from langchain_core.documents import Document

from src.embeddings.embedder import embed_documents, embed_query

_INDEX_NAME: str = os.getenv("ENDEE_INDEX_NAME", "legal_docs")
_BASE_URL: str = os.getenv("ENDEE_BASE_URL", "http://localhost:8080/api/v1")
_AUTH_TOKEN: str = os.getenv("ENDEE_AUTH_TOKEN", "")
_EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", "1024"))


def _make_client() -> Endee:
    client = Endee(_AUTH_TOKEN)
    client.set_base_url(_BASE_URL)
    return client


def _doc_to_vector_item(doc: Document, uid: str) -> dict:
    meta = {**doc.metadata, "page_content": doc.page_content}
    return {"id": uid, "vector": None, "meta": meta}


def _results_to_documents(results: list) -> List[Document]:
    docs = []
    for item in results:
        meta: dict = dict(item.get("meta") or {})
        page_content = meta.pop("page_content", "")
        docs.append(Document(page_content=page_content, metadata=meta))
    return docs


class EndeeVectorStore:

    def __init__(self, index_name: str = _INDEX_NAME) -> None:
        self.index_name = index_name
        self._client: Optional[Endee] = None
        self._index = None

    def _get_client(self) -> Endee:
        if self._client is None:
            self._client = _make_client()
        return self._client

    def _get_index(self):
        if self._index is None:
            self._index = self._get_client().get_index(name=self.index_name)
        return self._index

    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        vector = embed_query(query)
        results = self._get_index().query(vector=vector, top_k=k, ef=128)
        return _results_to_documents(results)

    def add_documents(self, documents: List[Document], offset: int = 0) -> None:
        if not documents:
            return
        texts = [doc.page_content for doc in documents]
        vectors = embed_documents(texts)
        items = []
        for i, (doc, vec) in enumerate(zip(documents, vectors)):
            uid = f"{doc.metadata.get('document_name', 'doc')}_{doc.metadata.get('chunk_index', offset + i)}"
            item = _doc_to_vector_item(doc, uid)
            item["vector"] = vec
            items.append(item)
        self._get_index().upsert(items)

    def describe(self) -> dict:
        return self._get_index().describe()


def build_vectorstore(
    documents: List[Document],
    index_name: str = _INDEX_NAME,
    dimension: int = _EMBEDDING_DIM,
    recreate: bool = False,
) -> EndeeVectorStore:
    if not documents:
        raise ValueError("Cannot build vectorstore from an empty document list.")

    client = _make_client()

    if recreate:
        try:
            client.delete_index(index_name)
            print(f"[store] Deleted existing index '{index_name}'")
        except Exception:
            pass

    try:
        client.create_index(
            name=index_name,
            dimension=dimension,
            space_type="cosine",
            precision=Precision.INT8,
            sparse_model="endee_bm25",
        )
        print(f"[store] Created Endee index '{index_name}' (dim={dimension})")
    except Exception as exc:
        print(f"[store] Index '{index_name}' already exists ({exc}); reusing.")

    store = EndeeVectorStore(index_name=index_name)
    store.add_documents(documents)
    print(f"[store] Upserted {len(documents)} documents into '{index_name}'")
    return store


def load_vectorstore(index_name: str = _INDEX_NAME) -> EndeeVectorStore:
    client = _make_client()
    try:
        index = client.get_index(name=index_name)
        info = index.describe()
        print(f"[store] Connected to index '{index_name}': {info}")
    except Exception as exc:
        raise FileNotFoundError(
            f"Endee index '{index_name}' not found. "
            "Run the ingest pipeline first.\n"
            f"Detail: {exc}"
        ) from exc
    return EndeeVectorStore(index_name=index_name)


def add_to_vectorstore(
    new_documents: List[Document],
    index_name: str = _INDEX_NAME,
) -> EndeeVectorStore:
    if not new_documents:
        raise ValueError("Cannot add an empty document list to the vectorstore.")
    store = load_vectorstore(index_name)
    store.add_documents(new_documents)
    print(f"[store] Added {len(new_documents)} documents to '{index_name}'")
    return store
