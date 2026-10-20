"""
ai_service.py — Service module providing Flashcard AI inference integration.
Applies Singleton / Lazy Loading pattern to load Flan-T5 model weights once.
"""

from __future__ import annotations

import logging
from pathlib import Path
import sys
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configure sys.path for pipeline integration and dependencies
# ---------------------------------------------------------------------------
_CURRENT_DIR = Path(__file__).resolve().parent  # server/app/services
_SERVER_DIR = _CURRENT_DIR.parent.parent  # server
_PROJECT_ROOT = _SERVER_DIR.parent  # workspace root
_PIPELINE_DIR = _PROJECT_ROOT / "pipeline"

# Add pipeline directory and root to sys.path so pipeline.src is importable
for _path in [str(_PIPELINE_DIR), str(_PROJECT_ROOT)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

# Fallback: Allow importing torch, transformers, sentencepiece from pipeline venv
_PIPELINE_SITE_PACKAGES = _PIPELINE_DIR / ".venv" / "Lib" / "site-packages"
if _PIPELINE_SITE_PACKAGES.exists() and str(_PIPELINE_SITE_PACKAGES) not in sys.path:
    sys.path.append(str(_PIPELINE_SITE_PACKAGES))

try:
    from pipeline.src.processors.card_generator import FlashcardPipeline
    from pipeline.src.cleaners.text_cleaner import clean_text, chunk_text
except ImportError:
    from src.processors.card_generator import FlashcardPipeline  # pyright: ignore[reportMissingImports] # type: ignore[import-not-found]
    from src.cleaners.text_cleaner import clean_text, chunk_text  # pyright: ignore[reportMissingImports] # type: ignore[import-not-found]

# Default model directory path
_MODEL_DIR = str(_PIPELINE_DIR / "models_weights" / "flan-t5-base")

# Module-level variable for Singleton instance
_pipeline_instance: Optional[FlashcardPipeline] = None


def get_pipeline() -> FlashcardPipeline:
    """Lazy-load and return the singleton instance of FlashcardPipeline."""
    global _pipeline_instance
    if _pipeline_instance is None:
        logger.info("Initializing FlashcardPipeline singleton instance...")
        _pipeline_instance = FlashcardPipeline(model_path=_MODEL_DIR)
    return _pipeline_instance


def generate_flashcards_service(text: str) -> list[dict]:
    """
    Nhận văn bản đầu vào, gọi pipeline AI xử lý và trả về
    danh sách dict: [{"question": "...", "answer": "..."}, ...]
    """
    if not text or not text.strip():
        return []

    cleaned = clean_text(text)
    if not cleaned or not cleaned.strip():
        return []

    pipeline = get_pipeline()
    chunks = chunk_text(cleaned, max_words=150)
    if not chunks:
        return []

    all_cards: list[dict] = []
    seen_questions: set[str] = set()

    for chunk in chunks:
        cards = pipeline.generate_from_chunk(chunk)
        for card in cards:
            key = card.get("question", "").lower().strip()
            if key and key not in seen_questions:
                seen_questions.add(key)
                all_cards.append(
                    {"question": card["question"], "answer": card["answer"]}
                )

    return all_cards
