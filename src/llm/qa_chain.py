import logging
import os
from typing import Dict, List, Optional

from langchain_ollama import OllamaLLM as Ollama
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate

from src.translation.hindi_translator import HindiTranslator


_DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:4b")
_DEFAULT_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

_logger = logging.getLogger(__name__)


_ENGLISH_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "You are an expert legal assistant. Use only the context below to "
        "answer the question. If the answer is not present in the context, "
        "say that the information is not found in the document.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Answer in clear English:"
    ),
)


_HINDI_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "Aap ek sahayak hain jo kanooni dastavejon ko samajhne mein madad karte hain. "
        "Neeche diye gaye context ka upyog karke prashn ka saral Hindi mein uttar dijiye. "
        "Kathin kanooni shabdon ka upyog mat kariye.\n\n"
        "Context:\n{context}\n\n"
        "Prashn: {question}\n\n"
        "Saral Hindi mein uttar:"
    ),
)


def _format_context(docs: List[Document]) -> str:
    parts = []
    for i, doc in enumerate(docs, 1):
        parts.append(f"[Source {i}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


class LegalQAChain:

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.model = model or _DEFAULT_MODEL
        self.base_url = base_url or _DEFAULT_BASE_URL
        self._llm: Optional[Ollama] = None
        self._translator: Optional[HindiTranslator] = None

    def _get_llm(self) -> Ollama:
        if self._llm is None:
            try:
                self._llm = Ollama(model=self.model, base_url=self.base_url)
            except Exception:
                self._llm = None
                raise
        return self._llm

    def _get_translator(self) -> HindiTranslator:
        if self._translator is None:
            self._translator = HindiTranslator(model=self.model, base_url=self.base_url)
        return self._translator

    def answer(
        self,
        question: str,
        retrieved_docs: List[Document],
        language: str = "both",
    ) -> Dict[str, str]:

        if not question.strip():
            return {"error": "Empty question."}

        if not retrieved_docs:
            return {
                "english": "No relevant documents found.",
                "hindi": "कोई दस्तावेज़ नहीं मिला।",
                "sources": [],
            }

        try:
            llm = self._get_llm()
            context = _format_context(retrieved_docs)
            result: Dict[str, str] = {}

            if language == "both":
                english_chain = _ENGLISH_PROMPT | llm
                english_answer = english_chain.invoke(
                    {"context": context, "question": question}
                ).strip()
                result["english"] = english_answer
                hindi_answer = self._get_translator().translate(english_answer)
                if not hindi_answer or hindi_answer == "अनुवाद उपलब्ध नहीं है।":
                    _logger.warning("Hindi translation returned empty or fallback for question: %s", question)
                result["hindi"] = hindi_answer

            elif language == "hindi":
                chain = _HINDI_PROMPT | llm
                result["hindi"] = chain.invoke(
                    {"context": context, "question": question}
                ).strip()

            else:
                chain = _ENGLISH_PROMPT | llm
                result["english"] = chain.invoke(
                    {"context": context, "question": question}
                ).strip()

            result["sources"] = [
                doc.metadata.get("document", "Unknown")
                for doc in retrieved_docs
            ]

            return result

        except Exception as e:
            return {"error": f"Could not generate answer: {str(e)}"}
