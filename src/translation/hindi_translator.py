"""Hindi simplification module.

Translates/simplifies legal English text into plain, everyday Hindi using the
Ollama LLM (no paid API required). The output is targeted at common people
(farmers, shopkeepers, daily wage workers) — NOT formal legal Hindi.
"""

import os
from typing import Optional

from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate


_DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "mistral")
_DEFAULT_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

_HINDI_PROMPT = PromptTemplate(
    input_variables=["english_text"],
    template=(
        "You are a helpful assistant who explains legal information in simple, "
        "everyday Hindi that a farmer, shopkeeper, or daily wage worker can "
        "understand. Avoid legal jargon. Use short sentences.\n\n"
        "Translate and simplify the following English legal text into simple Hindi:\n\n"
        "{english_text}\n\n"
        "Simple Hindi explanation:"
    ),
)


class HindiTranslator:
    """Translates English legal text into simple Hindi using Ollama."""

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

    def translate(self, english_text: str) -> str:
        """Translate English legal text to simple Hindi.

        Args:
            english_text: The English text to translate/simplify.

        Returns:
            Simple Hindi explanation string.
        """
        llm = self._get_llm()
        chain = _HINDI_PROMPT | llm
        return chain.invoke({"english_text": english_text}).strip()
