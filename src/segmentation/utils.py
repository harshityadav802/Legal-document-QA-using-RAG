"""Utility helpers for legal segmentation."""

import re
from typing import List


def count_tokens(text: str) -> int:
    """Approximate token count using whitespace splitting (fast, no model
    needed). One token ≈ 0.75 words for English legal text."""
    words = text.split()
    return max(1, int(len(words) / 0.75))


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences without requiring spaCy.

    Uses a simple rule-based approach that handles common legal text patterns.
    """
    # Protect known abbreviations from being split
    abbreviations = [
        "Mr.", "Mrs.", "Ms.", "Dr.", "Prof.", "Sr.", "Jr.", "Ltd.", "Inc.",
        "Corp.", "Co.", "vs.", "etc.", "e.g.", "i.e.", "No.", "Sec.", "Art.",
        "para.", "cl.", "sub-cl.", "Pvt.",
    ]
    protected = text
    placeholder_map = {}
    for i, abbr in enumerate(abbreviations):
        placeholder = f"__ABBR{i}__"
        protected = protected.replace(abbr, placeholder)
        placeholder_map[placeholder] = abbr

    # Split on sentence-ending punctuation followed by whitespace + capital
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\(\[])", protected)

    sentences = []
    for part in parts:
        # Restore abbreviations
        for placeholder, original in placeholder_map.items():
            part = part.replace(placeholder, original)
        part = part.strip()
        if part:
            sentences.append(part)

    return sentences if sentences else [text]


def merge_short_chunks(
    chunks: List[str], min_tokens: int = 50
) -> List[str]:
    """Merge consecutive chunks that are below the minimum token count."""
    if not chunks:
        return chunks
    merged = [chunks[0]]
    for chunk in chunks[1:]:
        if count_tokens(merged[-1]) < min_tokens:
            merged[-1] = merged[-1] + "\n\n" + chunk
        else:
            merged.append(chunk)
    return merged


def add_overlap(
    chunks: List[str], overlap_tokens: int = 50
) -> List[str]:
    """Add token overlap between consecutive chunks from the same section."""
    if len(chunks) <= 1:
        return chunks

    result = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            result.append(chunk)
            continue
        # Take the last `overlap_tokens` words of the previous chunk
        prev_words = chunks[i - 1].split()
        overlap_word_count = max(1, int(overlap_tokens * 0.75))
        overlap_text = " ".join(prev_words[-overlap_word_count:])
        result.append(overlap_text + "\n" + chunk)

    return result
