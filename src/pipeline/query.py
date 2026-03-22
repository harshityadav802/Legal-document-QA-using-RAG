import os
from typing import Dict, List, Optional

from src.llm.qa_chain import LegalQAChain
from src.retrieval.retriever import EndeeHybridRetriever
from src.vectorstore.store import load_vectorstore

VALID_LANGUAGES = {"english", "hindi", "both"}


class QueryPipeline:

    def __init__(
        self,
        index_name: Optional[str] = None,
        k: int = 5,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        effective_index = index_name or os.getenv("ENDEE_INDEX_NAME", "legal_docs")
        self.vectorstore = load_vectorstore(effective_index)
        self.k = k
        self.retriever = EndeeHybridRetriever(vectorstore=self.vectorstore, k=k)
        self.qa_chain = LegalQAChain(model=model, base_url=base_url)

    def query(
        self,
        question: str,
        language: str = "both",
        k: Optional[int] = None,
    ) -> Dict:
        if not question.strip():
            return {"error": "Empty question.", "sources": []}

        if language not in VALID_LANGUAGES:
            language = "both"

        try:
            top_k = k if k is not None else self.k
            docs = self.retriever.retrieve(question, k=top_k)
            answer = self.qa_chain.answer(question, docs, language=language)
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

        except Exception as e:
            return {"error": f"Query failed: {str(e)}", "sources": []}
