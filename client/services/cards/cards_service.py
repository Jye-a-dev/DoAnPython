"""
cards_service.py — Flashcards CRUD and batch operations on client side.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union
from services.api_base import _handle_http_error, get_client


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
                payload["deck_id"] = fields["deck_id"]
        else:
            if deck_id is not None:
                payload["deck_id"] = deck_id
            payload["question"] = question
            payload["answer"] = answer
            if explanation:
                payload["explanation"] = explanation
            payload.update(fields)

        res = await client.post("/cards", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "tạo card mới")


async def create_cards_batch(
    deck_id: int,
    cards: list[dict[str, Any]],
    document_id: Optional[int] = None,
) -> dict[str, Any]:
    """Gửi mảng flashcards đã lọc lên POST /api/cards/batch trong một transaction."""
    try:
        client = get_client()
        payload: dict[str, Any] = {
            "deck_id": deck_id,
            "cards": cards,
        }
        if document_id is not None:
            payload["document_id"] = document_id

        res = await client.post("/cards/batch", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lưu hàng loạt flashcards vào deck")


async def update_card(card_id: int, **fields: Any) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.put(f"/cards/{card_id}", json=fields)
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
        params = {}
        if deck_id is not None:
            params["deck_id"] = deck_id
        res = await client.delete("/cards", params=params if params else None)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "xóa toàn bộ cards")
