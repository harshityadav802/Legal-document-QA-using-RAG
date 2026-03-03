"""Legal document segmenter — 5-stage pipeline.

Stage 1: Structure Detection  — identify headings/hierarchy
Stage 2: Hierarchy Building   — build breadcrumb paths
Stage 3: Semantic Boundaries  — sentence-aware, definition-aware splitting
Stage 4: Smart Chunk Sizing   — 256-token target, 512 max, 50 min
Stage 5: Context Header       — prepend metadata header to every chunk
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

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
# Heading patterns (Stage 1)
# ---------------------------------------------------------------------------
HEADING_PATTERNS = [
    (r"^(ARTICLE|Article)\s+[IVX\d]+", "article"),
    (r"^\d+\.\s+[A-Z]", "section"),
    (r"^\d+\.\d+\s+[A-Za-z]", "subsection"),
    (r"^\d+\.\d+\.\d+\s+[A-Za-z]", "subsubsection"),
    (r"^[A-Z][A-Z\s]{3,}:", "labeled_section"),
    (r"^WHEREAS\b", "recital"),
    (r"^NOW,\s+THEREFORE\b", "transition"),
    (r"^IN WITNESS WHEREOF\b", "signature"),
    (r"^SCHEDULE\s+[A-Z\d]+", "schedule"),
    (r"^EXHIBIT\s+[A-Z\d]+", "exhibit"),
    (r"^ANNEX\s+[A-Z\d]+", "annex"),
    (r"^\([a-z]\)\s+", "sub_item"),
    (r"^\([ivx]+\)\s+", "sub_sub_item"),
]

# Chunk sizing constants
TARGET_TOKENS = 256
MAX_TOKENS = 512
MIN_TOKENS = 50
OVERLAP_TOKENS = 50


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class LegalNode:
    """A node in the document hierarchy."""

    level: str  # article / section / subsection / paragraph / etc.
    heading: str
    text: str = ""
    children: List["LegalNode"] = field(default_factory=list)
    parent: Optional["LegalNode"] = field(default=None, repr=False)
    breadcrumb: str = ""
    section_type: str = "OTHER"


@dataclass
class LegalChunk:
    """A processed chunk ready for embedding."""

    text: str
    breadcrumb: str
    section_type: str
    document_name: str
    cross_references: List[str] = field(default_factory=list)
    is_operative: bool = False
    chunk_index: int = 0


# ---------------------------------------------------------------------------
# Stage 1: Structure Detection
# ---------------------------------------------------------------------------
def detect_heading(line: str):
    """Return (pattern_name, match) if line matches a heading, else None."""
    stripped = line.strip()
    for pattern, label in HEADING_PATTERNS:
        m = re.match(pattern, stripped)
        if m:
            return label, stripped
    return None


_LEVEL_ORDER = {
    "article": 1,
    "labeled_section": 1,
    "recital": 1,
    "transition": 1,
    "signature": 1,
    "schedule": 1,
    "exhibit": 1,
    "annex": 1,
    "section": 2,
    "subsection": 3,
    "subsubsection": 4,
    "sub_item": 5,
    "sub_sub_item": 6,
    "paragraph": 7,
}


# ---------------------------------------------------------------------------
# Stage 2: Hierarchy Building
# ---------------------------------------------------------------------------
def build_hierarchy(text: str, document_name: str = "Document") -> LegalNode:
    """Parse document text into a tree of LegalNodes."""
    root = LegalNode(
        level="root", heading=document_name, breadcrumb=document_name
    )
    current_path: List[LegalNode] = [root]

    lines = text.split("\n")
    current_body_lines: List[str] = []
    current_node: LegalNode = root

    def flush_body():
        body = "\n".join(current_body_lines).strip()
        if body:
            current_node.text += ("\n" if current_node.text else "") + body
        current_body_lines.clear()

    for raw_line in lines:
        result = detect_heading(raw_line)
        if result:
            flush_body()
            label, heading_text = result
            level_num = _LEVEL_ORDER.get(label, 7)

            # Pop the stack until we find a parent with a lower level number
            while len(current_path) > 1:
                parent_level = _LEVEL_ORDER.get(current_path[-1].level, 7)
                if parent_level < level_num:
                    break
                current_path.pop()

            parent_node = current_path[-1]
            breadcrumb = (
                parent_node.breadcrumb + " > " + heading_text
                if parent_node.breadcrumb
                else heading_text
            )
            new_node = LegalNode(
                level=label,
                heading=heading_text,
                parent=parent_node,
                breadcrumb=breadcrumb,
                section_type=classify_section(heading_text),
            )
            parent_node.children.append(new_node)
            current_path.append(new_node)
            current_node = new_node
        else:
            current_body_lines.append(raw_line)

    flush_body()
    return root


# ---------------------------------------------------------------------------
# Stage 3 + 4: Semantic Splitting & Smart Chunk Sizing
# ---------------------------------------------------------------------------
def _is_definition_sentence(sentence: str) -> bool:
    """Return True if the sentence introduces a definition."""
    patterns = [
        r"\bmeans\b",
        r"\bshall\s+mean\b",
        r"\brefers\s+to\b",
        r"\bis\s+defined\s+as\b",
        r'["\']\w[\w\s]+["\']\s+means',
    ]
    for p in patterns:
        if re.search(p, sentence, re.IGNORECASE):
            return True
    return False


def _split_node_into_chunks(
    node: LegalNode, document_name: str
) -> List[LegalChunk]:
    """Split a single LegalNode's text into properly-sized chunks."""
    full_text = node.text.strip()
    if not full_text:
        return []

    sentences = split_into_sentences(full_text)

    # Group sentences into chunks respecting MAX_TOKENS
    raw_chunks: List[str] = []
    current: List[str] = []
    current_tokens = 0
    i = 0
    while i < len(sentences):
        sentence = sentences[i]
        sent_tokens = count_tokens(sentence)

        # Keep definition sentences with the following sentence (the definition body)
        if _is_definition_sentence(sentence) and i + 1 < len(sentences):
            combined = sentence + " " + sentences[i + 1]
            combined_tokens = count_tokens(combined)
            if current_tokens + combined_tokens <= MAX_TOKENS:
                current.append(combined)
                current_tokens += combined_tokens
                i += 2
                continue
            else:
                if current:
                    raw_chunks.append("\n".join(current))
                current = [combined]
                current_tokens = combined_tokens
                i += 2
                continue

        if current_tokens + sent_tokens > MAX_TOKENS and current:
            raw_chunks.append("\n".join(current))
            current = [sentence]
            current_tokens = sent_tokens
        else:
            current.append(sentence)
            current_tokens += sent_tokens
        i += 1

    if current:
        raw_chunks.append("\n".join(current))

    # Stage 4: merge tiny chunks
    raw_chunks = merge_short_chunks(raw_chunks, min_tokens=MIN_TOKENS)

    # Add overlap
    raw_chunks = add_overlap(raw_chunks, overlap_tokens=OVERLAP_TOKENS)

    # Build LegalChunk objects
    chunks = []
    for idx, chunk_text in enumerate(raw_chunks):
        cross_refs = extract_cross_references(chunk_text)
        operative = is_operative_clause(chunk_text)
        chunks.append(
            LegalChunk(
                text=chunk_text,
                breadcrumb=node.breadcrumb,
                section_type=node.section_type,
                document_name=document_name,
                cross_references=cross_refs,
                is_operative=operative,
                chunk_index=idx,
            )
        )
    return chunks


def _collect_node_chunks(
    node: LegalNode, document_name: str
) -> List[LegalChunk]:
    """Recursively collect chunks from a node and all its children."""
    chunks = []
    if node.level != "root":
        chunks.extend(_split_node_into_chunks(node, document_name))
    for child in node.children:
        chunks.extend(_collect_node_chunks(child, document_name))
    return chunks


# ---------------------------------------------------------------------------
# Stage 5: Context Header
# ---------------------------------------------------------------------------
def _add_context_header(chunk: LegalChunk) -> str:
    """Prepend a metadata context header to a chunk's text."""
    header = (
        f"[Document: {chunk.document_name} | "
        f"Section: {chunk.breadcrumb} | "
        f"Type: {chunk.section_type}]"
    )
    return header + "\n\n" + chunk.text


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def segment_document(
    text: str, document_name: str = "Document"
) -> List[LegalChunk]:
    """Run the 5-stage segmentation pipeline on cleaned document text.

    Args:
        text: Pre-processed legal document text.
        document_name: Human-readable name for the document.

    Returns:
        List of LegalChunk objects ready for embedding.
    """
    # Stage 1 + 2: build hierarchy
    root = build_hierarchy(text, document_name)

    # Stage 3 + 4: semantic splitting + smart sizing
    chunks = _collect_node_chunks(root, document_name)

    # Stage 5: add context headers and update chunk text
    for chunk in chunks:
        chunk.text = _add_context_header(chunk)

    return chunks


def get_document_structure(text: str, document_name: str = "Document") -> Dict:
    """Return a dictionary summarising the document's heading structure."""
    root = build_hierarchy(text, document_name)

    def node_to_dict(node: LegalNode) -> Dict:
        return {
            "heading": node.heading,
            "level": node.level,
            "section_type": node.section_type,
            "breadcrumb": node.breadcrumb,
            "children": [node_to_dict(c) for c in node.children],
        }

    return node_to_dict(root)
