import os
from typing import Dict, List, Optional

from langchain_community.llms import Ollama
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate


_DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
_DEFAULT_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


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


_BILINGUAL_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=(
        "You are a legal assistant. Use only the context to answer the question.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Provide the response in two sections:\n\n"
        "English Answer:\n"
        "Clear legal explanation.\n\n"
        "Hindi Answer:\n"
        "Same answer in simple Hindi."
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

        else:
            chain = _ENGLISH_PROMPT | llm
            result["english"] = chain.invoke(
                {"context": context, "question": question}
            ).strip()

        return result


def _parse_bilingual(raw_text: str) -> tuple:

    raw_text = raw_text.strip()

    english = ""
    hindi = ""

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

            for eng_marker in ["**English Answer:**", "English Answer:"]:
                english_block = english_block.replace(eng_marker, "")

            english = english_block.strip().strip("*").strip()
            hindi = hindi_block.strip().lstrip(":").strip().strip("*").strip()

            return english, hindi

    return raw_text.strip(), ""
