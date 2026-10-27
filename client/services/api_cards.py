from __future__ import annotations

from typing import Any, Dict, Optional, Union
from services.api_base import _handle_http_error, get_client


# ===========================================================================
# 7. CARDS API (Table 7: cards)
# ===========================================================================
async def get_cards(
    deck_id: Optional[int] = None, user_id: Optional[int] = None
) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        params = {}
        if deck_id is not None:
            params["deck_id"] = deck_id
        if user_id is not None:
            params["user_id"] = user_id
        res = await client.get("/cards", params=params if params else None)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy danh sách cards")


async def get_card_by_id(card_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.get(f"/cards/{card_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy chi tiết card")


async def create_card(
    deck_id: Optional[Union[int, str]] = None,
    question: str = "",
    answer: str = "",
    explanation: Optional[str] = None,
    **fields: Any,
) -> dict[str, Any]:
    try:
        client = get_client()
        payload: dict[str, Any] = {}
        if isinstance(deck_id, str) and not answer:
            payload["question"] = deck_id
            payload["answer"] = question
            if "deck_id" in fields:
                payload["deck_id"] = fields.pop("deck_id")
        else:
            if deck_id is not None:
                payload["deck_id"] = deck_id
            if question:
                payload["question"] = question
            if answer:
                payload["answer"] = answer
        if explanation is not None:
            payload["explanation"] = explanation
        payload.update(fields)
        res = await client.post("/cards", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "tạo card")


async def update_card(
    card_id: int, data: Optional[dict[str, Any]] = None, **fields: Any
) -> dict[str, Any]:
    try:
        client = get_client()
        payload: dict[str, Any] = {}
        if data and isinstance(data, dict):
            payload.update(data)
        payload.update(fields)
        res = await client.put(f"/cards/{card_id}", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "cập nhật card")


async def delete_card(card_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.delete(f"/cards/{card_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "xóa card")


async def delete_all_cards(deck_id: Optional[int] = None) -> dict[str, Any]:
    try:
        client = get_client()
        params = {"deck_id": deck_id} if deck_id else None
        res = await client.delete("/cards", params=params)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "xóa tất cả cards")


# ===========================================================================
# 8. TAGS API (Table 8: tags)
# ===========================================================================
async def get_tags(
    user_id: Optional[int] = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        params = {"user_id": user_id} if user_id else None
        res = await client.get("/tags", params=params)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy danh sách tags")


async def get_tag_by_id(tag_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.get(f"/tags/{tag_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy chi tiết tag")


async def create_tag(name: str, user_id: Optional[int] = 1) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.post("/tags", json={"name": name, "user_id": user_id})
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "tạo tag")


async def update_tag(tag_id: int, name: str) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.put(f"/tags/{tag_id}", json={"name": name})
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "cập nhật tag")


async def delete_tag(tag_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.delete(f"/tags/{tag_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "xóa tag")


# ===========================================================================
# 9. CARD_TAGS API (Table 9: card_tags M:N)
# ===========================================================================
async def get_card_tags(
    card_id: Optional[int] = None, tag_id: Optional[int] = None
) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        params = {
            k: v
            for k, v in {"card_id": card_id, "tag_id": tag_id}.items()
            if v is not None
        }
        res = await client.get("/card-tags", params=params)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy danh sách card_tags")


async def add_card_tag(card_id: int, tag_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.post(
            "/card-tags", json={"card_id": card_id, "tag_id": tag_id}
        )
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "gán tag cho card")


async def remove_card_tag(card_id: int, tag_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.delete(f"/card-tags/{card_id}/{tag_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "gỡ tag khỏi card")


async def get_tags_for_card(card_id: int) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        res = await client.get(f"/cards/{card_id}/tags")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy tags của card")


# ===========================================================================
# AI PIPELINE & GENERATION GATEWAY
# ===========================================================================
async def generate_cards(
    doc_id: int, deck_id: Optional[int] = 1, user_id: int = 1
) -> dict[str, Any]:
    """Gửi request POST /generate-from-doc/{doc_id} để tạo flashcard tự động."""
    try:
        client = get_client()
        payload: dict[str, Any] = {"user_id": user_id}
        if deck_id is not None:
            payload["deck_id"] = deck_id
        res = await client.post(f"/generate-from-doc/{doc_id}", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "sinh flashcards từ tài liệu")


async def transcribe_audio(
    file_bytes: bytes, filename: str = "audio.wav", language: str = "vi"
) -> dict[str, Any]:
    """Gửi request POST /transcribe để bóc băng âm thanh (STT)."""
    try:
        client = get_client()
        files = {"file": (filename, file_bytes)}
        data = {"language": language}
        res = await client.post("/transcribe", files=files, data=data)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "bóc băng âm thanh")


async def generate_flashcards(
    text: str, deck_id: Optional[int] = None
) -> list[dict[str, Any]] | dict[str, Any]:
    """Gửi yêu cầu sinh flashcard từ văn bản thuần tới Backend."""
    payload: dict[str, Any] = {"text": text}
    if deck_id is not None:
        payload["deck_id"] = deck_id
    try:
        client = get_client()
        res = await client.post("/generate", json=payload)
        res.raise_for_status()
        data = res.json()
        return data.get("cards", data if isinstance(data, list) else [])
    except Exception as err:
        return _handle_http_error(err, "sinh flashcards từ văn bản")
