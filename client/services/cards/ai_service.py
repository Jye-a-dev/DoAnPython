"""
ai_service.py — AI Generation and STT API operations on client side.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from services.api_base import _handle_http_error, get_client


async def generate_cards(
    doc_id: int, deck_id: Optional[int] = None, user_id: int = 1
) -> dict[str, Any]:
    try:
        client = get_client()
        payload: dict[str, Any] = {"user_id": user_id}
        if deck_id is not None:
            payload["deck_id"] = deck_id
        res = await client.post(f"/generate-from-doc/{doc_id}", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "sinh flashcards tự động từ tài liệu")


async def transcribe_audio(
    file_bytes: bytes, filename: str = "audio.wav", language: str = "vi"
) -> dict[str, Any]:
    try:
        client = get_client()
        files = {"file": (filename, file_bytes, "audio/wav")}
        data = {"language": language}
        res = await client.post("/transcribe", files=files, data=data)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "bóc băng âm thanh")


async def generate_flashcards(
    text: str, deck_id: Optional[int] = None, max_cards: int = 3
) -> dict[str, Any]:
    try:
        client = get_client()
        payload: dict[str, Any] = {"text": text, "max_cards": max_cards}
        if deck_id is not None:
            payload["deck_id"] = deck_id
        res = await client.post("/generate", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "sinh flashcards tự động từ văn bản")

