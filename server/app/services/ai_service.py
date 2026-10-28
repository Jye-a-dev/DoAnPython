"""
ai_service.py — Backend Server AI Gateway client integration.
Delegates heavy AI inference tasks (Flan-T5 generation, Whisper STT)
to the standalone AI Pipeline Microservice running on Port 8000 via HTTP.

Tách rời AI Inference Phase và Database Commit Phase:
- persist_to_db=False (mặc định): trả về list[dict] in-memory draft,
  ghi telemetry vào ai_generation_logs nhưng tuyệt đối KHÔNG commit Card.
- persist_to_db=True (legacy): commit Card vào SQLite + ghi AIGenerationLog.
"""

from __future__ import annotations

import logging
import json
import time
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.core.config import Config
from app.core.database import db
from app.models.document import Document
from app.models.flashcard import Card, Deck
from app.models.study import AIGenerationLog

logger = logging.getLogger(__name__)

# Base endpoint for AI Pipeline Microservice
AI_PIPELINE_URL = getattr(
    Config, "AI_PIPELINE_URL", "http://127.0.0.1:8000/api"
).rstrip("/")

_fallback_pipeline = None


def _post_json(url: str, payload: Dict[str, Any], timeout: float) -> Any:
    req = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_multipart(
    url: str, filename: str, file_bytes: bytes, language: str, timeout: float
) -> Any:
    boundary = "----AIServiceBoundary7MA4YWxkTrZu0gW"
    body = (
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode("utf-8")
        + file_bytes
        + f"\r\n--{boundary}--\r\n".encode("ascii")
    )
    req = Request(
        f"{url}?{urlencode({'language': language})}",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def get_pipeline():
    """Fallback accessor for FlashcardPipeline in isolated offline/testing environments."""
    global _fallback_pipeline
    if _fallback_pipeline is None:
        try:
            from pipeline.src.processors.card_generator import FlashcardPipeline

            _fallback_pipeline = FlashcardPipeline()
        except Exception:
            _fallback_pipeline = None
    return _fallback_pipeline


def generate_flashcards_service(
    text: str, max_cards: int = 3, max_words_per_chunk: int = 150
) -> Dict[str, Any]:
    """
    Send lesson text to AI Pipeline Microservice (POST /api/pi/generate)
    and return response dict containing count, cards, and inference_time_seconds.
    """
    if not text or not text.strip():
        return {"count": 0, "cards": [], "inference_time_seconds": 0.0}

    candidate_urls = [
        f"{AI_PIPELINE_URL}/pi/generate",
        f"{AI_PIPELINE_URL}/generate",
    ]
    payload = {
        "text": text.strip(),
        "max_cards": max_cards,
        "max_words_per_chunk": max_words_per_chunk,
    }
    last_exc = None
    for target_url in candidate_urls:
        try:
            data = _post_json(target_url, payload, timeout=120.0)
            if isinstance(data, dict):
                return {
                    "count": data.get("count", len(data.get("cards", []))),
                    "cards": data.get("cards", []),
                    "inference_time_seconds": data.get("inference_time_seconds", 0.0),
                }
            if isinstance(data, list):
                return {
                    "count": len(data),
                    "cards": data,
                    "inference_time_seconds": 0.0,
                }
            return {"count": 0, "cards": [], "inference_time_seconds": 0.0}
        except (URLError, HTTPError, TimeoutError, OSError) as exc:
            last_exc = exc
            continue

    logger.warning(
        "AI Pipeline unreachable at candidate endpoints (%s). Attempting local fallback.",
        last_exc,
    )
    pipeline = get_pipeline()
    if pipeline:
        from pipeline.src.cleaners.text_cleaner import clean_text, chunk_text

        cleaned = clean_text(text)
        chunks = chunk_text(cleaned, max_words=max_words_per_chunk)
        cards = (
            pipeline.generate_from_chunks(chunks, max_cards_per_chunk=max_cards)
            if chunks
            else []
        )
        return {"count": len(cards), "cards": cards, "inference_time_seconds": 0.0}
    raise RuntimeError(
        f"Lỗi kết nối tới AI Pipeline Microservice (Port 8000): {str(last_exc)}"
    ) from last_exc


def transcribe_audio_service(
    file_bytes: bytes,
    filename: str = "audio.wav",
    language: str = "vi",
) -> Dict[str, Any]:
    """Forward uploaded audio bytes to AI Pipeline Microservice via multipart/form-data."""
    if not file_bytes:
        raise ValueError("Audio binary payload is empty.")

    candidate_urls = [
        f"{AI_PIPELINE_URL}/pi/transcribe",
        f"{AI_PIPELINE_URL}/transcribe",
    ]
    last_exc = None
    for target_url in candidate_urls:
        try:
            return _post_multipart(
                target_url, filename, file_bytes, language, timeout=180.0
            )
        except (URLError, HTTPError, TimeoutError, OSError) as exc:
            last_exc = exc
            continue

    logger.error("Failed to connect to AI Pipeline transcribe endpoints: %s", last_exc)
    raise RuntimeError(
        f"Lỗi kết nối tới AI Pipeline Microservice (Port 8000): {str(last_exc)}"
    ) from last_exc


def check_pipeline_health_service(timeout: float = 3.0) -> Dict[str, Any]:
    """Ping healthcheck endpoint của AI Pipeline Microservice (GET /api/pi/health)."""
    candidate_urls = [
        f"{AI_PIPELINE_URL}/pi/health",
        f"{AI_PIPELINE_URL}/health",
    ]
    for url in candidate_urls:
        try:
            req = Request(
                url, headers={"User-Agent": "Backend-HealthCheck"}, method="GET"
            )
            with urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception:
            continue
    return {
        "status": "unreachable",
        "error": "AI Pipeline microservice is not responding",
    }


def generate_cards_from_document_id(
    doc_id: int,
    deck_id: Optional[int],
    user_id: int,
    persist_to_db: bool = False,
) -> Dict[str, Any]:
    """
    Extract text từ Document, trigger AI Pipeline, rồi:

    - persist_to_db=False (mặc định — Draft Mode):
        Đóng gói thành list[dict] in-memory draft.
        Ghi telemetry vào ai_generation_logs.
        Tuyệt đối KHÔNG db.session.add(Card) hay commit Card.

    - persist_to_db=True (Persist Mode / legacy):
        Commit Card vào SQLite.
        Ghi AIGenerationLog.
    """
    # 1. Validate Document
    document = db.session.get(Document, doc_id)
    if not document:
        raise ValueError(f"Không tìm thấy tài liệu với ID: {doc_id}")

    # 2. Validate Deck khi persist_to_db
    if persist_to_db:
        if deck_id is None:
            raise ValueError("deck_id là bắt buộc khi persist_to_db=True")
        deck = db.session.get(Deck, deck_id)
        if not deck:
            raise ValueError(f"Không tìm thấy bộ thẻ (Deck) với ID: {deck_id}")

    extracted_text = document.extracted_text or ""
    if not extracted_text.strip():
        raise ValueError("Tài liệu không có nội dung văn bản để sinh thẻ flashcard")

    start_time = time.perf_counter()
    status = "SUCCESS"
    error_message: Optional[str] = None
    saved_cards: List[Card] = []
    draft_cards: List[Dict[str, Any]] = []

    try:
        # 3. Call AI Pipeline Microservice
        pipeline_res = generate_flashcards_service(extracted_text)
        generated_pairs = (
            pipeline_res.get("cards", [])
            if isinstance(pipeline_res, dict)
            else pipeline_res
        )

        if persist_to_db:
            # 4a. PERSIST MODE: Commit cards vào SQLite
            for pair in generated_pairs:
                q = pair.get("question", "").strip()
                a = pair.get("answer", "").strip()
                if q and a:
                    card = Card(
                        deck_id=deck_id,
                        document_id=doc_id,
                        question=q,
                        answer=a,
                        difficulty="medium",
                        tts_text=q,
                        tts_lang="en-US",
                    )
                    db.session.add(card)
                    saved_cards.append(card)
            db.session.commit()
        else:
            # 4b. DRAFT MODE: Chỉ đóng gói dict, KHÔNG add/commit Card nào
            for pair in generated_pairs:
                q = pair.get("question", "").strip()
                a = pair.get("answer", "").strip()
                if q and a:
                    draft_cards.append(
                        {
                            "question": q,
                            "answer": a,
                            "explanation": pair.get("explanation", ""),
                            "difficulty": pair.get("difficulty", "medium"),
                            "tts_text": q,
                            "tts_lang": "en-US",
                        }
                    )

    except Exception as exc:
        if persist_to_db:
            db.session.rollback()
        status = "FAILED"
        error_message = str(exc)
        logger.exception("Error generating flashcards for doc_id %d: %s", doc_id, exc)

    inference_time = time.perf_counter() - start_time

    # 5. Persist audit telemetry in ai_generation_logs (luôn chạy)
    cards_count = len(saved_cards) if persist_to_db else len(draft_cards)
    approx_prompt_tokens = len(extracted_text.split())
    if persist_to_db:
        approx_comp_tokens = sum(
            len(c.question.split()) + len(c.answer.split()) for c in saved_cards
        )
    else:
        approx_comp_tokens = sum(
            len(d["question"].split()) + len(d["answer"].split()) for d in draft_cards
        )

    log = AIGenerationLog()
    log.user_id = user_id
    log.document_id = doc_id
    log.deck_id = deck_id
    log.model_name = "flan-t5-base"
    log.cards_generated = cards_count
    log.inference_time_seconds = round(inference_time, 3)
    log.prompt_tokens = approx_prompt_tokens
    log.completion_tokens = approx_comp_tokens
    log.status = status
    log.error_message = error_message
    db.session.add(log)
    db.session.commit()

    if status == "FAILED":
        raise RuntimeError(f"Lỗi AI Pipeline: {error_message}")

    if persist_to_db:
        return {
            "status": "SUCCESS",
            "document_id": doc_id,
            "deck_id": deck_id,
            "user_id": user_id,
            "cards_generated": len(saved_cards),
            "inference_time_seconds": round(inference_time, 3),
            "log_id": log.id,
            "cards": [card.to_dict() for card in saved_cards],
        }
    return {
        "status": "DRAFT",
        "document_id": doc_id,
        "deck_id": deck_id,
        "user_id": user_id,
        "count": len(draft_cards),
        "cards_generated": len(draft_cards),
        "inference_time_seconds": round(inference_time, 3),
        "log_id": log.id,
        "cards": draft_cards,
    }
