import os
from typing import List
from langchain_community.embeddings import HuggingFaceEmbeddings


DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")

_embedder = None


def get_embedder(model_name: str = DEFAULT_MODEL) -> HuggingFaceEmbeddings:

    global _embedder

    if _embedder is None:

        _embedder = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    return _embedder


def embed_documents(texts: List[str]) -> List[List[float]]:

    embedder = get_embedder()

    return embedder.embed_documents(texts)


def embed_query(text: str) -> List[float]:

    embedder = get_embedder()

    return embedder.embed_query(text)
def embed_texts(texts: List[str], model_name: str = DEFAULT_MODEL) -> List[List[float]]:
    """Embed a list of texts and return their dense vectors."""
    embedder = get_embedder(model_name)
    return embedder.embed_documents(texts)
