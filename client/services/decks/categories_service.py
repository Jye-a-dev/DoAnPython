"""
categories_service.py — Categories API operations on client side (Table 3: categories).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from services.api_base import _handle_http_error, get_client


async def get_categories(
    user_id: Optional[int] = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        params = {}
        if user_id is not None:
            params["user_id"] = user_id
        res = await client.get("/categories", params=params if params else None)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy danh sách categories")


async def get_category_by_id(category_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.get(f"/categories/{category_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy chi tiết category")


async def create_category(name: str, user_id: int = 1, **fields: Any) -> dict[str, Any]:
    try:
        client = get_client()
        payload = {"name": name, "user_id": user_id}
        payload.update(fields)
        res = await client.post("/categories", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "tạo category mới")


async def update_category(category_id: int, **fields: Any) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.put(f"/categories/{category_id}", json=fields)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "cập nhật category")


async def delete_category(category_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.delete(f"/categories/{category_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "xóa category")
