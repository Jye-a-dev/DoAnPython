"""
text_cleaner.py — Preprocessing & Chunking module for the Flan-T5 flashcard pipeline.

Public API:
    load_document(file_path)          -> str
    clean_text(text)                  -> str
    chunk_text(text, max_words, overlap) -> list[str]
"""

from __future__ import annotations

import logging
import re
import unicodedata
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Document loading
# ---------------------------------------------------------------------------


def load_document(file_path: str) -> str:
    """Load raw text from a PDF or TXT file.

    Args:
        file_path: Absolute or relative path to the source file.

    Returns:
        Extracted text as a single string, or empty string on failure.

    Raises:
        ValueError: If the file extension is not supported (.pdf / .txt).
    """
    path = Path(file_path)

    if not path.exists():
        logger.error("File not found: %s", file_path)
        raise FileNotFoundError(f"File không tồn tại: {file_path}")

    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _load_pdf(path)
    elif suffix == ".txt":
        return _load_txt(path)
    else:
        raise ValueError(
            f"Định dạng không hỗ trợ: '{suffix}'. Chỉ chấp nhận .pdf hoặc .txt."
        )


def _load_pdf(path: Path) -> str:
    """Extract text from every page of a PDF using pypdf."""
    try:
        import pypdf  # lazy import — only required for PDF paths
    except ImportError as exc:
        raise ImportError("Thiếu thư viện pypdf. Cài bằng: pip install pypdf") from exc

    pages: list[str] = []
    try:
        reader = pypdf.PdfReader(str(path))
        for page_num, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
                pages.append(text)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Bỏ qua trang %d (lỗi trích xuất): %s", page_num, exc)
    except Exception as exc:  # noqa: BLE001
        logger.error("Không thể đọc PDF '%s': %s", path, exc)
        raise RuntimeError(f"File PDF bị hỏng hoặc không đọc được: {path}") from exc

    return "\n".join(pages)


def _load_txt(path: Path) -> str:
    """Read a plain-text file with UTF-8 encoding."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Fallback: latin-1 never fails on arbitrary byte sequences
        logger.warning("UTF-8 decode failed for '%s', retrying with latin-1.", path)
        return path.read_text(encoding="latin-1")
    except OSError as exc:
        logger.error("Không thể đọc file '%s': %s", path, exc)
        raise


# ---------------------------------------------------------------------------
# Text cleaning
# ---------------------------------------------------------------------------

# Control characters except tab (\x09) and newline (\x0a)
_CTRL_RE = re.compile(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]")

# Non-breaking space (\xa0), zero-width chars, soft hyphen, BOM, etc.
_INVISIBLE_RE = re.compile(r"[\xa0\u00ad\u200b-\u200f\u202a-\u202e\u2060\ufeff]")

# Two or more consecutive blank lines → single blank line
_MULTI_BLANK_RE = re.compile(r"\n{3,}")

# Two or more spaces/tabs inside a line → single space
_MULTI_SPACE_RE = re.compile(r"[ \t]{2,}")


def clean_text(text: str) -> str:
    """Advanced text normalisation.

    Steps applied in order:
    1. Normalise line endings  (\\r\\n / \\r → \\n).
    2. Strip Unicode control characters and invisible characters.
    3. Apply Unicode NFC normalisation.
    4. Collapse multiple blank lines to at most one blank line.
    5. Collapse intra-line whitespace while preserving sentence terminators.

    Args:
        text: Raw input string.

    Returns:
        Cleaned string; empty string if input is falsy.
    """
    if not text:
        return ""

    # 1 — normalise line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 2 — strip control chars and invisible Unicode chars
    text = _CTRL_RE.sub("", text)
    text = _INVISIBLE_RE.sub(" ", text)

    # 3 — NFC normalisation (e.g. combining diacritics → precomposed form)
    text = unicodedata.normalize("NFC", text)

    # 4 — collapse 3+ consecutive newlines → exactly 2 (i.e. one blank line)
    text = _MULTI_BLANK_RE.sub("\n\n", text)

    # 5 — collapse intra-line whitespace (tabs / multiple spaces)
    #     Process line-by-line so we don't disturb paragraph boundaries.
    lines = [_MULTI_SPACE_RE.sub(" ", line).strip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()


# ---------------------------------------------------------------------------
# Sentence-boundary chunking
# ---------------------------------------------------------------------------

# Sentence boundary: a terminator (. ! ?) optionally followed by closing
# quote/bracket, then at least one whitespace character.
_SENT_SPLIT_RE = re.compile(r'(?<=[.!?])["\'\)\]]*\s+')


def chunk_text(
    text: str,
    max_words: int = 150,
    overlap: int = 20,
) -> list[str]:
    """Split text into overlapping chunks aligned to sentence boundaries.

    Each chunk contains at most *max_words* whitespace-delimited tokens so
    that, after WordPiece tokenisation, the result comfortably fits within
    Flan-T5's 512-token context window (rough ratio ≈ 1 word : 1.3 tokens).

    Overlap is implemented by reusing the last *overlap* words of a completed
    chunk as the opening words of the next chunk, preserving cross-boundary
    context.

    Args:
        text:      Cleaned input text.
        max_words: Maximum number of words per chunk (default 150).
        overlap:   Number of words to carry over between consecutive chunks
                   (default 20). Must be < max_words.

    Returns:
        List of non-empty chunk strings.  Returns ``[]`` for empty input.

    Example::

        >>> chunks = chunk_text("Sentence one. Sentence two.", max_words=10, overlap=3)
    """
    if not text:
        return []

    overlap = min(overlap, max_words - 1)  # guard: overlap must be < max_words

    # Split into sentences while keeping the terminator attached to its sentence.
    # re.split with a look-behind keeps the delimiter position correct.
    raw_sentences: list[str] = _SENT_SPLIT_RE.split(text)

    # Further clean and filter empty fragments
    sentences: list[str] = [s.strip() for s in raw_sentences if s.strip()]

    if not sentences:
        return []

    chunks: list[str] = []
    current_words: list[str] = []

    for sentence in sentences:
        sentence_words = sentence.split()

        # If this single sentence alone exceeds max_words, hard-split it.
        if len(sentence_words) > max_words:
            # Flush current buffer first
            if current_words:
                chunks.append(" ".join(current_words))
                current_words = current_words[-overlap:] if overlap else []

            # Hard-split the oversized sentence with overlap
            for i in range(0, len(sentence_words), max_words - overlap):
                segment = sentence_words[i : i + max_words]
                if segment:
                    chunks.append(" ".join(segment))
            # Seed next chunk with tail of the oversized sentence
            current_words = sentence_words[-(overlap):] if overlap else []
            continue

        # Would adding this sentence exceed the budget?
        if len(current_words) + len(sentence_words) > max_words:
            # Flush the current chunk
            if current_words:
                chunks.append(" ".join(current_words))
            # Start new chunk with overlap tail + current sentence
            current_words = (
                current_words[-overlap:] + sentence_words if overlap else sentence_words
            )
        else:
            current_words.extend(sentence_words)

    # Flush remaining words
    if current_words:
        chunks.append(" ".join(current_words))

    # Deduplicate consecutive identical chunks that may arise from overlap logic
    unique: list[str] = []
    for chunk in chunks:
        if not unique or chunk != unique[-1]:
            unique.append(chunk)

    return unique
