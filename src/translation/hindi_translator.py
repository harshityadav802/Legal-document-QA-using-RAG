"""Hindi simplification module.

Translates/simplifies legal English text into plain, everyday Hindi using the
Ollama LLM (no paid API required). The output is targeted at common people
(farmers, shopkeepers, daily wage workers) — NOT formal legal Hindi.
"""

import logging
import os
from typing import Optional

from langchain_ollama import OllamaLLM as Ollama
from langchain_core.prompts import PromptTemplate


_DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:4b")
_DEFAULT_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Maximum number of words to send to the translation model to avoid exceeding
# the context window and slowing down inference on small models.
_MAX_TRANSLATION_WORDS = 400

_logger = logging.getLogger(__name__)

_HINDI_PROMPT = PromptTemplate(
    input_variables=["english_text"],
    template=(
        "Aap ek legal sahayak hain. Neeche diye gaye angrezi text ko "
        "bilkul simple Hindi mein translate karein.\n\n"
        "Rules:\n"
        "- Sirf Hindi mein likhein, koi English nahi\n"
        "- Chhote chhote sentences likhein\n"
        "- Aam insaan ki bhasha use karein\n"
        "- Koi kanoon ki bhaasha nahi\n"
        "- Seedha translation, koi explanation nahi\n\n"
        "Angrezi text:\n{english_text}\n\n"
        "Hindi mein:"
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
            try:
                self._llm = Ollama(model=self.model, base_url=self.base_url)
            except Exception:
                self._llm = None
                raise
        return self._llm

    def translate(self, english_text: str) -> str:
        """Translate English legal text to simple Hindi.

        Args:
            english_text: The English text to translate/simplify.

        Returns:
            Simple Hindi explanation string.
        """
        if not english_text.strip():
            return ""
        if len(english_text.split()) > _MAX_TRANSLATION_WORDS:
            english_text = " ".join(english_text.split()[:_MAX_TRANSLATION_WORDS])
        try:
            llm = self._get_llm()
            chain = _HINDI_PROMPT | llm
            return chain.invoke({"english_text": english_text}).strip()
        except Exception as e:
            _logger.error("Hindi translation failed: %s", e, exc_info=True)
            return "अनुवाद उपलब्ध नहीं है।"
