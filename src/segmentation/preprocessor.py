"""Preprocessor for raw legal document text."""

import re
import unicodedata
from typing import Tuple


# Document type patterns
_DOC_TYPE_PATTERNS = {
    "NDA": [
        r"\bnon.?disclosure\b",
        r"\bconfidentiality\s+agreement\b",
        r"\bNDA\b",
    ],
    "MOU": [
        r"\bmemorandum\s+of\s+understanding\b",
        r"\bMOU\b",
    ],
    "SERVICE_AGREEMENT": [
        r"\bservice\s+agreement\b",
        r"\bservices\s+agreement\b",
        r"\bconsulting\s+agreement\b",
    ],
    "EMPLOYMENT": [
        r"\bemployment\s+agreement\b",
        r"\bemployment\s+contract\b",
        r"\boffer\s+letter\b",
    ],
    "LEASE": [
        r"\blease\s+agreement\b",
        r"\brental\s+agreement\b",
        r"\btenancy\s+agreement\b",
    ],
    "PARTNERSHIP": [
        r"\bpartnership\s+agreement\b",
        r"\bjoint\s+venture\b",
    ],
    "CONTRACT": [r"\bcontract\b", r"\bagreement\b"],
}


def remove_headers_footers(text: str) -> str:
    """Remove common page headers and footers from legal documents."""
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        # Page number patterns
        if re.match(r"^[Pp]age\s+\d+\s+(of\s+\d+)?$", stripped):
            continue
        if re.match(r"^\d+\s*/\s*\d+$", stripped):
            continue
        # Confidential / proprietary markers as standalone lines
        if re.match(
            r"^(CONFIDENTIAL|PROPRIETARY|DRAFT|PRIVILEGED)\s*$",
            stripped,
            re.IGNORECASE,
        ):
            continue
        cleaned.append(line)
    return "\n".join(cleaned)


def fix_broken_lines(text: str) -> str:
    """Fix lines broken mid-sentence (common in PDF extraction)."""
    lines = text.split("\n")
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        # If current line ends without terminal punctuation and next non-empty
        # line starts with a lowercase letter, join them.
        if (
            stripped
            and not stripped.endswith((".", ":", ";", "?", "!"))
            and not stripped.endswith(",")
            and i + 1 < len(lines)
        ):
            next_stripped = lines[i + 1].strip()
            if next_stripped and next_stripped[0].islower():
                result.append(line.rstrip() + " " + next_stripped)
                i += 2
                continue
        result.append(line)
        i += 1
    return "\n".join(result)


def normalize_whitespace(text: str) -> str:
    """Normalize multiple blank lines and trailing spaces."""
    # Collapse 3+ consecutive blank lines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip trailing whitespace per line
    lines = [l.rstrip() for l in text.split("\n")]
    return "\n".join(lines)


def normalize_unicode(text: str) -> str:
    """Normalize unicode characters to their closest ASCII equivalents where
    possible, while preserving Devanagari (Hindi) characters."""
    result = []
    for ch in text:
        # Preserve Devanagari block (U+0900–U+097F) and extended blocks
        cp = ord(ch)
        if 0x0900 <= cp <= 0x097F or 0x0980 <= cp <= 0x09FF:
            result.append(ch)
        else:
            normalized = unicodedata.normalize("NFKD", ch)
            ascii_equiv = normalized.encode("ascii", "ignore").decode("ascii")
            result.append(ascii_equiv if ascii_equiv else ch)
    return "".join(result)


def detect_document_type(text: str) -> str:
    """Detect the type of legal document from its text.

    Returns one of: NDA, MOU, SERVICE_AGREEMENT, EMPLOYMENT, LEASE,
    PARTNERSHIP, CONTRACT, or UNKNOWN.
    """
    text_lower = text[:3000].lower()  # Only look at the first part
    for doc_type, patterns in _DOC_TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return doc_type
    return "UNKNOWN"


def preprocess(text: str) -> Tuple[str, str]:
    """Full preprocessing pipeline.

    Returns:
        Tuple of (cleaned_text, document_type)
    """
    text = normalize_unicode(text)
    text = remove_headers_footers(text)
    text = fix_broken_lines(text)
    text = normalize_whitespace(text)
    doc_type = detect_document_type(text)
    return text.strip(), doc_type
