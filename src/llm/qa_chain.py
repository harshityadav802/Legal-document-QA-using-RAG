"""Ollama-based bilingual QA chain (English + Hindi).

Generates answers in English and optionally in simple Hindi for every query.
No paid API is used — requires a locally running Ollama instance.
"""

import os
from typing import Dict, List, Optional

from langchain_community.llms import Ollama
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate


_DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
_DEFAULT_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
_ENGLISH_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "You are an expert legal assistant. Use ONLY the context below to "
        "answer the question. If the answer is not in the context, say "
        "'I could not find this information in the provided document.'\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Answer (in clear English):"
    ),
)

_HINDI_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "Aap ek sahayak hain jo kanooni dastavejon ko samajhne mein madad karte hain. "
        "Neeche diye gaye context ka upyog karke prashn ka saral Hindi mein uttar dijiye. "
        "Kanooni shabdon ka upyog mat karen. Aam log jaise kisan, dukandaar ya mazdoor "
        "ko samajh aaye aisa jawab dijiye.\n\n"
        "Context:\n{context}\n\n"
        "Prashn: {question}\n\n"
        "Saral Hindi mein Uttar:"
    ),
)

_BILINGUAL_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "You are an expert legal assistant AND a Hindi translator. "
        "Use ONLY the provided context to answer the question.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Provide your answer in TWO parts:\n\n"
        "**English Answer:**\n"
        "[Give a clear, accurate legal answer in English]\n\n"
        "**Hindi Answer (सरल हिंदी में):**\n"
        "[Give the same answer in simple, everyday Hindi that a farmer or "
        "shopkeeper can understand. Avoid legal jargon.]\n"
    ),
)


def _format_context(docs: List[Document]) -> str:
    """Format retrieved documents into a single context string."""
    parts = []
    for i, doc in enumerate(docs, 1):
        parts.append(f"[Source {i}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


# ---------------------------------------------------------------------------
# QA Chain
# ---------------------------------------------------------------------------
class LegalQAChain:
    """Bilingual Legal QA chain using Ollama (free, local LLM).

    Args:
        model:    Ollama model name (default: mistral).
        base_url: Ollama server URL.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self.model = model or _DEFAULT_MODEL
        self.base_url = base_url or _DEFAULT_BASE_URL
        self._llm: Optional[Ollama] = None

    def _get_llm(self) -> Ollama:
        if self._llm is None:
            self._llm = Ollama(model=self.model, base_url=self.base_url)
        return self._llm

    def answer(
        self,
        question: str,
        retrieved_docs: List[Document],
        language: str = "both",
    ) -> Dict[str, str]:
        """Generate an answer from retrieved documents.

        Args:
            question:       The user's question.
            retrieved_docs: Documents retrieved by the retriever.
            language:       One of 'english', 'hindi', or 'both'.

        Returns:
            Dictionary with keys 'english' and/or 'hindi'.
        """
        llm = self._get_llm()
        context = _format_context(retrieved_docs)
        result: Dict[str, str] = {}

        if language == "both":
            chain = _BILINGUAL_PROMPT | llm
            raw = chain.invoke({"context": context, "question": question})
            english_part, hindi_part = _parse_bilingual(raw)
            result["english"] = english_part
            result["hindi"] = hindi_part

        elif language == "hindi":
            chain = _HINDI_PROMPT | llm
            result["hindi"] = chain.invoke(
                {"context": context, "question": question}
            ).strip()

        else:  # english
            chain = _ENGLISH_PROMPT | llm
            result["english"] = chain.invoke(
                {"context": context, "question": question}
            ).strip()

        return result


def _parse_bilingual(raw_text: str) -> tuple:
    """Parse the bilingual response into (english, hindi) parts."""
    raw_text = raw_text.strip()

    english = ""
    hindi = ""

    # Try to split on the Hindi Answer marker
    hindi_markers = [
        "**Hindi Answer",
        "Hindi Answer (सरल हिंदी में):",
        "Hindi Answer:",
        "सरल हिंदी में",
        "**Hindi",
    ]

    for marker in hindi_markers:
        if marker in raw_text:
            parts = raw_text.split(marker, 1)
            english_block = parts[0]
            hindi_block = parts[1] if len(parts) > 1 else ""

            # Clean english block
            for eng_marker in ["**English Answer:**", "English Answer:"]:
                english_block = english_block.replace(eng_marker, "")
            english = english_block.strip().strip("*").strip()

            # Clean hindi block
            hindi = hindi_block.strip().lstrip(":").strip().strip("*").strip()
            return english, hindi

    # Fallback: return the whole text as English
    return raw_text.strip(), ""
