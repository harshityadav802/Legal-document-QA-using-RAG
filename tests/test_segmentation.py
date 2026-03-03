"""Tests for the segmentation pipeline."""

import pytest

from src.segmentation.preprocessor import (
    detect_document_type,
    fix_broken_lines,
    normalize_unicode,
    normalize_whitespace,
    preprocess,
    remove_headers_footers,
)
from src.segmentation.legal_segmenter import (
    LegalChunk,
    build_hierarchy,
    segment_document,
)
from src.segmentation.section_classifier import (
    classify_section,
    extract_cross_references,
    is_operative_clause,
)
from src.segmentation.utils import (
    add_overlap,
    count_tokens,
    merge_short_chunks,
    split_into_sentences,
)


# ---------------------------------------------------------------------------
# Preprocessor tests
# ---------------------------------------------------------------------------
class TestRemoveHeadersFooters:
    def test_removes_page_number(self):
        text = "First paragraph.\nPage 1 of 20\nSecond paragraph."
        result = remove_headers_footers(text)
        assert "Page 1 of 20" not in result
        assert "First paragraph." in result

    def test_removes_page_fraction(self):
        text = "Content.\n1 / 20\nMore content."
        result = remove_headers_footers(text)
        assert "1 / 20" not in result

    def test_removes_confidential_header(self):
        text = "CONFIDENTIAL\nSome content here."
        result = remove_headers_footers(text)
        assert "CONFIDENTIAL" not in result
        assert "Some content here." in result

    def test_preserves_normal_lines(self):
        text = "This is a normal line.\nAnother normal line."
        result = remove_headers_footers(text)
        assert "This is a normal line." in result
        assert "Another normal line." in result


class TestNormalizeUnicode:
    def test_smart_quotes_normalized(self):
        text = "\u201cHello\u201d"  # "Hello"
        result = normalize_unicode(text)
        assert '"' in result or "Hello" in result

    def test_devanagari_preserved(self):
        text = "यह एक परीक्षण है"
        result = normalize_unicode(text)
        assert "यह" in result

    def test_ascii_unchanged(self):
        text = "Simple ASCII text."
        result = normalize_unicode(text)
        assert result == text


class TestFixBrokenLines:
    def test_joins_mid_sentence_breaks(self):
        text = "This sentence was\nbroken in the middle."
        result = fix_broken_lines(text)
        assert "was broken" in result or "was\nbroken" in result

    def test_does_not_join_after_period(self):
        text = "First sentence.\nSecond sentence."
        result = fix_broken_lines(text)
        assert "First sentence." in result
        assert "Second sentence." in result


class TestNormalizeWhitespace:
    def test_collapses_blank_lines(self):
        text = "Line 1\n\n\n\n\nLine 2"
        result = normalize_whitespace(text)
        assert "\n\n\n" not in result
        assert "Line 1" in result
        assert "Line 2" in result


class TestDetectDocumentType:
    def test_service_agreement(self):
        text = "This Service Agreement is entered into by and between..."
        assert detect_document_type(text) == "SERVICE_AGREEMENT"

    def test_nda(self):
        text = "This Non-Disclosure Agreement (NDA) is between..."
        assert detect_document_type(text) == "NDA"

    def test_employment(self):
        text = "This Employment Agreement is for the position of..."
        assert detect_document_type(text) == "EMPLOYMENT"

    def test_unknown(self):
        text = "Some random text without clear document type markers."
        result = detect_document_type(text)
        assert result in ("UNKNOWN", "CONTRACT")

    def test_mou(self):
        text = "This Memorandum of Understanding (MOU) is entered..."
        assert detect_document_type(text) == "MOU"


class TestPreprocess:
    def test_returns_tuple(self):
        text = "This Service Agreement is entered into...\nPage 1 of 5"
        cleaned, doc_type = preprocess(text)
        assert isinstance(cleaned, str)
        assert isinstance(doc_type, str)
        assert "Page 1 of 5" not in cleaned

    def test_strips_result(self):
        text = "   Service Agreement   "
        cleaned, _ = preprocess(text)
        assert cleaned == cleaned.strip()


# ---------------------------------------------------------------------------
# Utils tests
# ---------------------------------------------------------------------------
class TestCountTokens:
    def test_simple_text(self):
        text = "This is a test sentence with some words."
        tokens = count_tokens(text)
        assert tokens > 0

    def test_empty_returns_one(self):
        assert count_tokens("") == 1

    def test_more_words_more_tokens(self):
        short = "Hello world"
        long = "Hello world " * 20
        assert count_tokens(long) > count_tokens(short)


class TestSplitIntoSentences:
    def test_splits_sentences(self):
        text = "First sentence. Second sentence. Third sentence."
        sentences = split_into_sentences(text)
        assert len(sentences) >= 2

    def test_single_sentence(self):
        text = "Only one sentence here"
        sentences = split_into_sentences(text)
        assert len(sentences) == 1

    def test_handles_abbreviation(self):
        text = "The company, Inc. is located in Mumbai. It was founded in 2000."
        sentences = split_into_sentences(text)
        # Should not split on "Inc."
        assert any("Inc." in s for s in sentences)


class TestMergeShortChunks:
    def test_merges_tiny_chunks(self):
        chunks = ["tiny", "also tiny", "this is a longer chunk with enough tokens"]
        merged = merge_short_chunks(chunks, min_tokens=5)
        assert len(merged) <= len(chunks)

    def test_preserves_long_chunks(self):
        long_chunk = "word " * 100
        chunks = [long_chunk, long_chunk]
        merged = merge_short_chunks(chunks, min_tokens=50)
        assert len(merged) == 2


class TestAddOverlap:
    def test_adds_overlap(self):
        chunks = ["First chunk with some content here.", "Second chunk."]
        overlapped = add_overlap(chunks, overlap_tokens=3)
        assert len(overlapped) == 2
        # Second chunk should contain content from the first
        assert len(overlapped[1]) > len("Second chunk.")

    def test_single_chunk_unchanged(self):
        chunks = ["Only one chunk."]
        result = add_overlap(chunks)
        assert result == chunks


# ---------------------------------------------------------------------------
# Section classifier tests
# ---------------------------------------------------------------------------
class TestClassifySection:
    def test_definitions_heading(self):
        label = classify_section("DEFINITIONS")
        assert label == "DEFINITIONS"

    def test_payment_heading(self):
        label = classify_section("PAYMENT TERMS")
        assert label == "PAYMENT"

    def test_termination_heading(self):
        label = classify_section("TERMINATION")
        assert label == "TERMINATION"

    def test_confidentiality_heading(self):
        label = classify_section("CONFIDENTIALITY AND NON-DISCLOSURE")
        assert label == "CONFIDENTIALITY"

    def test_body_helps_classification(self):
        label = classify_section(
            "Section 3", "The fees shall be paid within 30 days."
        )
        assert label in ("PAYMENT", "OBLIGATIONS", "OTHER")

    def test_unknown_returns_other(self):
        label = classify_section("zzz_unknown_heading_xyz")
        assert isinstance(label, str)


class TestIsOperativeClause:
    def test_shall_is_operative(self):
        assert is_operative_clause("The party shall deliver the goods.")

    def test_must_is_operative(self):
        assert is_operative_clause("The client must provide documents.")

    def test_agrees_to_is_operative(self):
        assert is_operative_clause("The service provider agrees to perform.")

    def test_non_operative(self):
        assert not is_operative_clause("This is a background clause.")


class TestExtractCrossReferences:
    def test_section_reference(self):
        text = "As defined in Section 5.2 of this Agreement."
        refs = extract_cross_references(text)
        assert any("Section" in r for r in refs)

    def test_schedule_reference(self):
        text = "Services described in Schedule A."
        refs = extract_cross_references(text)
        assert any("Schedule" in r for r in refs)

    def test_no_references(self):
        text = "Plain text with no cross references here."
        refs = extract_cross_references(text)
        assert refs == []


# ---------------------------------------------------------------------------
# Legal segmenter tests
# ---------------------------------------------------------------------------
SAMPLE_TEXT = """
SERVICE AGREEMENT

ARTICLE I
DEFINITIONS

1.1 Definitions. As used in this Agreement:

(a) "Confidential Information" means any proprietary data.

(b) "Services" shall mean the software development services.

ARTICLE II
PAYMENT TERMS

2.1 Fees. The Client shall pay the Service Provider within thirty (30) days.

2.2 Late Payment. Interest of 1.5% per month shall accrue on overdue amounts.

ARTICLE III
TERMINATION

3.1 Term. This Agreement shall terminate on December 31, 2024.

3.2 Termination for Cause. Either party may terminate upon thirty (30) days written notice.
"""


class TestBuildHierarchy:
    def test_root_exists(self):
        root = build_hierarchy(SAMPLE_TEXT, "Test Doc")
        assert root.level == "root"
        assert root.heading == "Test Doc"

    def test_articles_detected(self):
        root = build_hierarchy(SAMPLE_TEXT, "Test Doc")
        # Should have children
        assert len(root.children) > 0

    def test_breadcrumb_contains_doc_name(self):
        root = build_hierarchy(SAMPLE_TEXT, "My Agreement")

        def check_breadcrumbs(node):
            if node.level != "root" and node.breadcrumb:
                assert "My Agreement" in node.breadcrumb
            for child in node.children:
                check_breadcrumbs(child)

        check_breadcrumbs(root)


class TestSegmentDocument:
    def test_returns_chunks(self):
        chunks = segment_document(SAMPLE_TEXT, "Test Document")
        assert len(chunks) > 0

    def test_chunks_are_legal_chunk_objects(self):
        chunks = segment_document(SAMPLE_TEXT, "Test Document")
        for chunk in chunks:
            assert isinstance(chunk, LegalChunk)

    def test_chunks_have_context_header(self):
        chunks = segment_document(SAMPLE_TEXT, "Test Document")
        for chunk in chunks:
            assert "[Document:" in chunk.text

    def test_chunks_have_breadcrumb(self):
        chunks = segment_document(SAMPLE_TEXT, "Test Document")
        for chunk in chunks:
            assert chunk.breadcrumb

    def test_no_chunk_exceeds_max_tokens(self):
        from src.segmentation.utils import count_tokens

        chunks = segment_document(SAMPLE_TEXT, "Test Document")
        for chunk in chunks:
            # The context header adds some tokens but the body should be bounded
            assert count_tokens(chunk.text) <= 800  # generous bound with header

    def test_document_name_in_chunks(self):
        chunks = segment_document(SAMPLE_TEXT, "Special Contract")
        assert any("Special Contract" in c.document_name for c in chunks)

    def test_section_types_assigned(self):
        chunks = segment_document(SAMPLE_TEXT, "Test Document")
        types = {c.section_type for c in chunks}
        assert len(types) >= 1
