"""
decks_service.py — Decks API operations on client side (Table 6: decks).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from services.api_base import _handle_http_error, get_client


async def get_decks(
    folder_id: Optional[int] = None,
    user_id: Optional[int] = None,
    document_id: Optional[int] = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        params = {}
        if folder_id is not None:
            params["folder_id"] = folder_id
        if user_id is not None:
            params["user_id"] = user_id
        if document_id is not None:
            params["document_id"] = document_id
        res = await client.get("/decks", params=params if params else None)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy danh sách decks")


async def get_deck_by_id(deck_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.get(f"/decks/{deck_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy chi tiết deck")


async def create_deck(title: str, user_id: int = 1, **fields: Any) -> dict[str, Any]:
    try:
        client = get_client()
        payload = {"title": title, "user_id": user_id}
        payload.update(fields)
        res = await client.post("/decks", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "tạo deck mới")


async def update_deck(
    deck_id: int, title: Optional[str] = None, **fields: Any
) -> dict[str, Any]:
    try:
        client = get_client()
        payload = {}
        if title is not None:
            payload["title"] = title
        payload.update(fields)
        res = await client.put(f"/decks/{deck_id}", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "cập nhật deck")


async def delete_deck(deck_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.delete(f"/decks/{deck_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "xóa deck")
