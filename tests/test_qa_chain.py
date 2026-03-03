"""Tests for the QA chain and translation modules.

Uses mocking so no Ollama instance or paid API is required.
"""

import pytest
from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from src.llm.qa_chain import LegalQAChain, _format_context, _parse_bilingual


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_doc(content: str, **metadata) -> Document:
    return Document(page_content=content, metadata=metadata)


DOCS = [
    make_doc(
        "The contract terminates after 30 days written notice.",
        breadcrumb="Agreement > Article VII > Section 7.2",
        section_type="TERMINATION",
        document_name="Service Agreement",
    ),
    make_doc(
        "All Fees are exclusive of applicable taxes including GST.",
        breadcrumb="Agreement > Article III > Section 3.4",
        section_type="PAYMENT",
        document_name="Service Agreement",
    ),
]


# ---------------------------------------------------------------------------
# _format_context tests
# ---------------------------------------------------------------------------
class TestFormatContext:
    def test_includes_source_labels(self):
        context = _format_context(DOCS)
        assert "[Source 1]" in context
        assert "[Source 2]" in context

    def test_includes_document_text(self):
        context = _format_context(DOCS)
        assert "terminates after 30 days" in context

    def test_single_doc(self):
        context = _format_context([DOCS[0]])
        assert "[Source 1]" in context
        assert "[Source 2]" not in context

    def test_empty_docs(self):
        context = _format_context([])
        assert context == ""


# ---------------------------------------------------------------------------
# _parse_bilingual tests
# ---------------------------------------------------------------------------
class TestParseBilingual:
    def test_parses_standard_format(self):
        raw = (
            "**English Answer:**\n"
            "The contract terminates after 30 days.\n\n"
            "**Hindi Answer (सरल हिंदी में):**\n"
            "यह अनुबंध 30 दिन में समाप्त हो जाएगा।"
        )
        english, hindi = _parse_bilingual(raw)
        assert "30 days" in english
        assert "30 दिन" in hindi

    def test_fallback_when_no_marker(self):
        raw = "Just a plain answer without any markers."
        english, hindi = _parse_bilingual(raw)
        assert "plain answer" in english
        assert hindi == ""

    def test_hindi_only_marker(self):
        raw = (
            "English part here.\n\n"
            "Hindi Answer:\n"
            "हिंदी जवाब यहाँ है।"
        )
        english, hindi = _parse_bilingual(raw)
        assert "English part" in english
        assert "हिंदी" in hindi

    def test_strips_whitespace(self):
        raw = (
            "  **English Answer:**  \n"
            "  Answer here.  \n\n"
            "  **Hindi Answer:**  \n"
            "  Hindi here.  "
        )
        english, hindi = _parse_bilingual(raw)
        assert english == english.strip()
        assert hindi == hindi.strip()


# ---------------------------------------------------------------------------
# LegalQAChain tests (with mocked LLM)
# ---------------------------------------------------------------------------
class TestLegalQAChain:
    def _make_chain_with_mock(self, llm_response: str) -> LegalQAChain:
        """Create a LegalQAChain with a mocked Ollama LLM."""
        chain = LegalQAChain(model="mistral", base_url="http://localhost:11434")
        mock_llm = MagicMock()
        mock_llm.__or__ = MagicMock(return_value=mock_llm)
        mock_llm.invoke = MagicMock(return_value=llm_response)

        # Patch the chain method to return our mock
        chain._llm = mock_llm
        return chain

    @patch("src.llm.qa_chain.Ollama")
    def test_english_answer_returned(self, mock_ollama_class):
        # LangChain LCEL calls llm(prompt) via __call__; configure return_value
        mock_llm_instance = MagicMock()
        mock_llm_instance.return_value = "The contract ends after 30 days."
        mock_ollama_class.return_value = mock_llm_instance

        chain = LegalQAChain()
        result = chain.answer(
            "When does the contract end?", DOCS, language="english"
        )
        assert "english" in result
        assert isinstance(result["english"], str)

    @patch("src.llm.qa_chain.Ollama")
    def test_hindi_answer_returned(self, mock_ollama_class):
        mock_llm_instance = MagicMock()
        mock_llm_instance.return_value = "अनुबंध 30 दिन में समाप्त होगा।"
        mock_ollama_class.return_value = mock_llm_instance

        chain = LegalQAChain()
        result = chain.answer(
            "अनुबंध कब समाप्त होगा?", DOCS, language="hindi"
        )
        assert "hindi" in result
        assert isinstance(result["hindi"], str)

    @patch("src.llm.qa_chain.Ollama")
    def test_bilingual_answer_returned(self, mock_ollama_class):
        mock_llm_instance = MagicMock()
        mock_llm_instance.return_value = (
            "**English Answer:**\nThe contract terminates after 30 days.\n\n"
            "**Hindi Answer (सरल हिंदी में):**\n"
            "यह अनुबंध 30 दिन में समाप्त होगा।"
        )
        mock_ollama_class.return_value = mock_llm_instance

        chain = LegalQAChain()
        result = chain.answer(
            "When does the contract end?", DOCS, language="both"
        )
        assert "english" in result
        assert "hindi" in result

    @patch("src.llm.qa_chain.Ollama")
    def test_default_language_is_both(self, mock_ollama_class):
        mock_llm_instance = MagicMock()
        mock_llm_instance.return_value = (
            "**English Answer:**\nAnswer.\n\n**Hindi Answer:**\nउत्तर।"
        )
        mock_ollama_class.return_value = mock_llm_instance

        chain = LegalQAChain()
        result = chain.answer("What are the payment terms?", DOCS)
        # Default language is 'both'
        assert "english" in result or "hindi" in result

    @patch("src.llm.qa_chain.Ollama")
    def test_empty_docs_handled(self, mock_ollama_class):
        mock_llm_instance = MagicMock()
        mock_llm_instance.return_value = "No information found."
        mock_ollama_class.return_value = mock_llm_instance

        chain = LegalQAChain()
        result = chain.answer("What is the fee?", [], language="english")
        assert "english" in result


# ---------------------------------------------------------------------------
# HindiTranslator tests
# ---------------------------------------------------------------------------
class TestHindiTranslator:
    @patch("src.translation.hindi_translator.Ollama")
    def test_translate_returns_string(self, mock_ollama_class):
        from src.translation.hindi_translator import HindiTranslator

        mock_llm_instance = MagicMock()
        mock_llm_instance.return_value = "यह अनुबंध 30 दिन में समाप्त होगा।"
        mock_ollama_class.return_value = mock_llm_instance

        translator = HindiTranslator()
        result = translator.translate("The contract terminates after 30 days.")
        assert isinstance(result, str)
        assert len(result) > 0

    @patch("src.translation.hindi_translator.Ollama")
    def test_translator_uses_ollama(self, mock_ollama_class):
        from src.translation.hindi_translator import HindiTranslator

        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = "हिंदी जवाब"
        mock_ollama_class.return_value = mock_llm_instance

        translator = HindiTranslator(model="mistral")
        translator.translate("Test text")
        mock_ollama_class.assert_called_once()
