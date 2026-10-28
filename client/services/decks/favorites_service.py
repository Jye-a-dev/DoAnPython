"""
favorites_service.py — Favorites API operations on client side (Table 13: favorites).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from services.api_base import _handle_http_error, get_client


async def get_favorites(
    user_id: Optional[int] = None,
    card_id: Optional[int] = None,
    deck_id: Optional[int] = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        params = {}
        if user_id is not None:
            params["user_id"] = user_id
        if card_id is not None:
            params["card_id"] = card_id
        if deck_id is not None:
            params["deck_id"] = deck_id
        res = await client.get("/favorites", params=params if params else None)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy danh sách favorites")


async def get_favorite_by_id(fav_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.get(f"/favorites/{fav_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy chi tiết favorite")


async def add_favorite(
    user_id: int = 1,
    card_id: Optional[int] = None,
    deck_id: Optional[int] = None,
) -> dict[str, Any]:
    try:
        client = get_client()
        payload: dict[str, Any] = {"user_id": user_id}
        if card_id is not None:
            payload["card_id"] = card_id
        if deck_id is not None:
            payload["deck_id"] = deck_id
        res = await client.post("/favorites", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "thêm favorite")


async def delete_favorite(fav_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.delete(f"/favorites/{fav_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "xóa favorite")
