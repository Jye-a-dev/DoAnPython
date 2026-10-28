"""
folders_service.py — Folders API operations on client side (Table 4: folders).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from services.api_base import _handle_http_error, get_client


async def get_folders(
    category_id: Optional[int] = None,
    user_id: Optional[int] = None,
    parent_id: Optional[int] = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        params = {}
        if category_id is not None:
            params["category_id"] = category_id
        if user_id is not None:
            params["user_id"] = user_id
        if parent_id is not None:
            params["parent_id"] = parent_id
        res = await client.get("/folders", params=params if params else None)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy danh sách folders")


async def get_folder_by_id(folder_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.get(f"/folders/{folder_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy chi tiết folder")


async def create_folder(name: str, user_id: int = 1, **fields: Any) -> dict[str, Any]:
    try:
        client = get_client()
        payload = {"name": name, "user_id": user_id}
        payload.update(fields)
        res = await client.post("/folders", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "tạo folder mới")


async def update_folder(folder_id: int, **fields: Any) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.put(f"/folders/{folder_id}", json=fields)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "cập nhật folder")


async def delete_folder(folder_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.delete(f"/folders/{folder_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "xóa folder")
