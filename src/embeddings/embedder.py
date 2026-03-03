"""HuggingFace embeddings using BAAI/bge-large-en-v1.5."""

import os
from typing import List

from langchain_community.embeddings import HuggingFaceEmbeddings


_DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")

# BGE models expect a query prefix for retrieval tasks
_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


def get_embedder(model_name: str = _DEFAULT_MODEL) -> HuggingFaceEmbeddings:
    """Return a LangChain HuggingFaceEmbeddings instance.

    Uses BAAI/bge-large-en-v1.5 by default — no API key required.
    The query instruction prefix is set automatically for BGE models.
    """
    encode_kwargs = {"normalize_embeddings": True}
    model_kwargs = {"device": "cpu"}

    # BGE models benefit from the query instruction prefix
    if "bge" in model_name.lower():
        return HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
            query_instruction=_QUERY_INSTRUCTION,
        )
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs,
    )


def embed_texts(texts: List[str], model_name: str = _DEFAULT_MODEL) -> List[List[float]]:
    """Embed a list of texts and return their dense vectors."""
    embedder = get_embedder(model_name)
    return embedder.embed_documents(texts)
