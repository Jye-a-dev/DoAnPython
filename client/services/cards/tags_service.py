"""
tags_service.py — Tags and card_tags operations on client side.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from services.api_base import _handle_http_error, get_client


async def get_tags(
    user_id: Optional[int] = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        params = {}
        if user_id is not None:
            params["user_id"] = user_id
        res = await client.get("/tags", params=params if params else None)
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
        return _handle_http_error(err, "tạo tag mới")


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


async def get_card_tags(
    card_id: Optional[int] = None, tag_id: Optional[int] = None
) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        params = {}
        if card_id is not None:
            params["card_id"] = card_id
        if tag_id is not None:
            params["tag_id"] = tag_id
        res = await client.get("/card-tags", params=params if params else None)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy danh sách card_tags")


async def add_card_tag(card_id: int, tag_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.post(
            f"/cards/{card_id}/tags",
            json={"tag_id": tag_id},
        )
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "gán tag vào card")


async def remove_card_tag(card_id: int, tag_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.delete(f"/cards/{card_id}/tags/{tag_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "gỡ tag khỏi card")


async def get_tags_for_card(card_id: int) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        res = await client.get(f"/cards/{card_id}")
        res.raise_for_status()
        data = res.json()
        return data.get("tags", []) if isinstance(data, dict) else []
    except Exception as err:
        return _handle_http_error(err, "lấy danh sách tags của card")
