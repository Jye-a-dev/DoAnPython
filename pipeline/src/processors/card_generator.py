"""
card_generator.py — Flashcard generation pipeline using Flan-T5 (offline).

Public API:
    FlashcardPipeline                            — model wrapper
    parse_flashcard_output(raw_output) -> list[dict]
    FlashcardPipeline.generate_from_document(file_path, max_words_per_chunk) -> list[dict]
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Resolve project root so imports work regardless of cwd
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent  # pipeline/src/processors/
_PIPELINE_DIR = _THIS_DIR.parent.parent  # pipeline/
if str(_PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(_PIPELINE_DIR))

# Default offline model directory (relative to pipeline/)
_DEFAULT_MODEL_DIR = str(_PIPELINE_DIR / "models_weights" / "flan-t5-base")

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------
_PROMPT_TEMPLATE = "Produce question and answer pairs from the following text for flashcard study:\n{chunk_text}"


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

# Compiled patterns — ordered from most-specific to most-generic
_QA_PATTERNS: list[re.Pattern[str]] = [
    # "Q: ... | A: ..." or "Q: ... A: ..."  (case-insensitive, multi-line)
    re.compile(
        r"[Qq](?:uestion)?[:\.]\s*(.+?)\s*(?:[\|/]\s*)?[Aa](?:nswer)?[:\.]\s*(.+?)(?=\n\s*[Qq](?:uestion)?[:\.]|$)",
        re.DOTALL,
    ),
    # "Question: ... Answer: ..."
    re.compile(
        r"Question[:\.]\s*(.+?)\s*(?:[\|/]\s*)?Answer[:\.]\s*(.+?)(?=\nQuestion[:\.]|$)",
        re.DOTALL | re.IGNORECASE,
    ),
    # Numbered pairs: "1. ... 1. ..." or "1) ..."
    re.compile(
        r"\d+[\.\)]\s*(.+?)\?\s*\n+\s*(.+?)(?=\n\s*\d+[\.\)]|$)",
        re.DOTALL,
    ),
]

# Separator used when model outputs raw "Question ... Answer ..." inline
_INLINE_SEP_RE = re.compile(
    r"(?:^|\n)\s*(?:[Qq](?:uestion)?|[Aa](?:nswer)?)[:\.]",
    re.MULTILINE,
)


def parse_flashcard_output(raw_output: str) -> list[dict[str, str]]:
    """Parse Flan-T5 raw text into a list of ``{"question": ..., "answer": ...}`` dicts.

    Tries multiple regex patterns in priority order; falls back to a
    line-pair heuristic for unexpected formats.

    Args:
        raw_output: Raw string produced by the model pipeline.

    Returns:
        Filtered list of dicts with non-empty ``question`` and ``answer`` fields.
    """
    cards: list[dict[str, str]] = []

    if not raw_output or not raw_output.strip():
        return cards

    text = raw_output.strip()

    # --- Strategy 1: structured Q/A regex patterns ---
    for pattern in _QA_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            for q, a in matches:
                q_clean = q.strip().rstrip("?|/ \t").strip()
                a_clean = a.strip()
                if q_clean and a_clean:
                    cards.append({"question": q_clean + "?", "answer": a_clean})
            if cards:
                return _deduplicate(cards)

    # --- Strategy 2: alternating-line heuristic ---
    # Split on blank lines, then pair consecutive non-empty segments
    segments = [s.strip() for s in re.split(r"\n\s*\n", text) if s.strip()]
    if len(segments) >= 2:
        it = iter(segments)
        for q_seg in it:
            a_seg = next(it, None)
            if a_seg:
                # Strip common prefixes
                q_clean = re.sub(r"^(?:[Qq](?:uestion)?|Q)[:\.\s]+", "", q_seg).strip()
                q_clean = q_clean.rstrip("?|/ \t").strip()
                a_clean = re.sub(r"^(?:[Aa](?:nswer)?|A)[:\.\s]+", "", a_seg).strip()
                if q_clean and a_clean:
                    cards.append({"question": q_clean + "?", "answer": a_clean})
        if cards:
            return _deduplicate(cards)

    # --- Strategy 3: single-line sentence fallback ---
    # Treat the whole output as a single QA if it contains "?"
    if "?" in text:
        parts = text.split("?", 1)
        q_clean = parts[0].strip().rstrip("?|/ \t").strip()
        a_clean = parts[1].strip() if len(parts) > 1 else ""
        if q_clean and a_clean:
            cards.append({"question": q_clean + "?", "answer": a_clean})

    return _deduplicate(cards)


def _deduplicate(cards: list[dict[str, str]]) -> list[dict[str, str]]:
    """Remove duplicate Q/A pairs (case-insensitive question match)."""
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for card in cards:
        key = card["question"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(card)
    return unique


# ---------------------------------------------------------------------------
# Pipeline class
# ---------------------------------------------------------------------------


class FlashcardPipeline:
    """Offline Flan-T5 pipeline for flashcard generation.

    Uses AutoModelForSeq2SeqLM + AutoTokenizer directly (compatible with
    transformers v4 and v5, which removed the text2text-generation pipeline).

    Args:
        model_path: Path to the local model directory containing weights and
                    tokenizer files.  Defaults to
                    ``pipeline/models_weights/flan-t5-base/``.
    """

    def __init__(self, model_path: str = _DEFAULT_MODEL_DIR) -> None:
        import torch
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM  # lazy import

        model_path = str(Path(model_path).resolve())
        logger.info("Loading Flan-T5 from %s (local_files_only=True)…", model_path)
        print(f"[*] Loading model from: {model_path}")

        self._tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            local_files_only=True,
        )
        self._model = AutoModelForSeq2SeqLM.from_pretrained(
            model_path,
            local_files_only=True,
        )
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._model.to(self._device)
        self._model.eval()
        print(f"[✓] Model loaded successfully. Device: {self._device}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_prompt(self, chunk_text: str) -> str:
        return _PROMPT_TEMPLATE.format(chunk_text=chunk_text.strip())

    def _infer(self, chunk_text: str) -> str:
        """Run model inference on a single chunk and return raw text."""
        import torch

        prompt = self._build_prompt(chunk_text)

        inputs = self._tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        ).to(self._device)

        with torch.no_grad():
            output_ids = self._model.generate(
                **inputs,
                max_new_tokens=128,
                min_length=15,
                do_sample=False,
                num_beams=2,
                repetition_penalty=1.2,
                early_stopping=True,
            )

        return self._tokenizer.decode(output_ids[0], skip_special_tokens=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def parse_flashcard_output(raw_output: str) -> list[dict[str, str]]:
        """Static wrapper for parsing raw output into Q/A dict pairs."""
        return parse_flashcard_output(raw_output)

    def generate_from_chunk(self, chunk_text: str) -> list[dict[str, str]]:
        """Generate flashcards from a single text chunk.

        Args:
            chunk_text: A pre-cleaned text segment.

        Returns:
            Parsed list of ``{"question": ..., "answer": ...}`` dicts.
        """
        if not chunk_text or not chunk_text.strip():
            return []
        raw = self._infer(chunk_text)
        if not raw:
            return []
        logger.debug("Raw model output:\n%s", raw)
        return parse_flashcard_output(raw)

    def generate_from_document(
        self,
        file_path: str,
        max_words_per_chunk: int = 150,
    ) -> list[dict[str, str]]:
        """End-to-end pipeline: load → clean → chunk → generate → aggregate.

        Args:
            file_path:           Path to a ``.txt`` or ``.pdf`` source file.
            max_words_per_chunk: Maximum words per text chunk fed to the model
                                 (default 150, ≈ 195 tokens — safe for Flan-T5's
                                 512-token context window).

        Returns:
            Deduplicated list of flashcard dicts across all chunks.
        """
        from src.cleaners.text_cleaner import load_document, clean_text, chunk_text

        logger.info("Loading document: %s", file_path)
        raw_text = load_document(file_path)

        logger.info("Cleaning text…")
        cleaned = clean_text(raw_text)
        if not cleaned or not cleaned.strip():
            return []

        logger.info("Chunking text (max_words=%d)…", max_words_per_chunk)
        chunks = chunk_text(cleaned, max_words=max_words_per_chunk)
        logger.info("Total chunks: %d", len(chunks))
        if not chunks:
            return []

        all_cards: list[dict[str, str]] = []
        seen_questions: set[str] = set()

        for idx, chunk in enumerate(chunks, start=1):
            logger.info("Processing chunk %d/%d…", idx, len(chunks))
            cards = self.generate_from_chunk(chunk)
            for card in cards:
                key = card["question"].lower().strip()
                if key not in seen_questions:
                    seen_questions.add(key)
                    all_cards.append(card)

        logger.info("Total flashcards generated: %d", len(all_cards))
        return all_cards
