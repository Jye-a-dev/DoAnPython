from __future__ import annotations

from typing import Any, Dict, Optional
from services.api_base import _handle_http_error, get_client


# ===========================================================================
# 3. CATEGORIES API (Table 3: categories)
# ===========================================================================
async def get_categories(
    user_id: Optional[int] = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        params = {"user_id": user_id} if user_id else None
        res = await client.get("/categories", params=params)
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
        payload = {"name": name, "user_id": user_id, **fields}
        res = await client.post("/categories", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "tạo category")


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


# ===========================================================================
# 4. FOLDERS API (Table 4: folders)
# ===========================================================================
async def get_folders(
    user_id: Optional[int] = None, parent_id: Optional[int] = None
) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        params = {}
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
        payload = {"name": name, "user_id": user_id, **fields}
        res = await client.post("/folders", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "tạo folder")


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


# ===========================================================================
# 6. DECKS API (Table 6: decks)
# ===========================================================================
async def get_decks(
    user_id: Optional[int] = None, is_public: Optional[bool] = None
) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        params = {}
        if user_id is not None:
            params["user_id"] = user_id
        if is_public is not None:
            params["is_public"] = str(is_public).lower()
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
        payload = {"title": title, "user_id": user_id, **fields}
        res = await client.post("/decks", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "tạo deck")


async def update_deck(
    deck_id: int, data: Optional[Dict[str, Any]] = None, **fields: Any
) -> dict[str, Any]:
    try:
        client = get_client()
        payload: dict[str, Any] = {}
        if data and isinstance(data, dict):
            payload.update(data)
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


# ===========================================================================
# 13. USER FAVORITES API (Table 13: user_favorites)
# ===========================================================================
async def get_favorites(
    user_id: Optional[int] = None,
    deck_id: Optional[int] = None,
    card_id: Optional[int] = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        params = {
            k: v
            for k, v in {
                "user_id": user_id,
                "deck_id": deck_id,
                "card_id": card_id,
            }.items()
            if v is not None
        }
        res = await client.get("/favorites", params=params)
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
    user_id: int, deck_id: Optional[int] = None, card_id: Optional[int] = None
) -> dict[str, Any]:
    try:
        client = get_client()
        payload = {"user_id": user_id, "deck_id": deck_id, "card_id": card_id}
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
