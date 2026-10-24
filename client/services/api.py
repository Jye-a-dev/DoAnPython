from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Union
import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

PORT: int = int(os.getenv("PORT", 5000))
HOST: str = os.getenv("HOST", "0.0.0.0")
BACKEND_API_URL: str = os.getenv("BACKEND_API_URL", "http://127.0.0.1:3000/api").rstrip(
    "/"
)
DEFAULT_TIMEOUT: float = 120.0

import asyncio

_client: Optional[httpx.AsyncClient] = None
_client_loop: Optional[asyncio.AbstractEventLoop] = None


def get_client() -> httpx.AsyncClient:
    """Tái sử dụng singleton AsyncClient để tối ưu hóa connection pooling và an toàn theo Event Loop."""
    global _client, _client_loop
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    if _client is None or _client.is_closed or _client_loop != current_loop:
        _client = httpx.AsyncClient(
            base_url=BACKEND_API_URL,
            timeout=httpx.Timeout(DEFAULT_TIMEOUT, connect=5.0),
        )
        _client_loop = current_loop
    return _client


async def close_client() -> None:
    """Đóng connection pool AsyncClient khi dừng ứng dụng."""
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
        _client = None


def _handle_http_error(err: Exception, operation: str) -> dict[str, Any]:
    """Phân loại lỗi HTTP/Mạng và chuẩn hóa định dạng phản hồi lỗi."""
    if isinstance(err, httpx.ConnectError):
        logger.error(
            "Lỗi kết nối Backend tại %s khi %s: %s", BACKEND_API_URL, operation, err
        )
        return {
            "error": True,
            "status_code": 503,
            "is_connection_error": True,
            "message": f"Không thể kết nối đến máy chủ Backend (Port 3000). Vui lòng kiểm tra lại tiến trình.",
        }
    if isinstance(err, httpx.ReadTimeout):
        logger.error(
            "Quá hạn thời gian chờ phản hồi (%ss) khi %s (Suy luận CPU quá tải): %s",
            DEFAULT_TIMEOUT,
            operation,
            err,
        )
        return {
            "error": True,
            "status_code": 504,
            "is_connection_error": True,
            "message": f"Quá thời gian phản hồi từ máy chủ Backend ({DEFAULT_TIMEOUT}s). Tiến trình AI đang bận.",
        }
    if isinstance(err, httpx.HTTPStatusError):
        resp: Any = getattr(err, "response", None)
        status_code = getattr(resp, "status_code", 500) if resp is not None else 500
        text = getattr(resp, "text", str(err)) if resp is not None else str(err)
        logger.error(
            "Lỗi HTTP %s khi %s: %s",
            status_code,
            operation,
            text,
        )
        is_conn_err = status_code in (502, 503, 504)
        msg = (
            "Không thể kết nối đến máy chủ Backend (Port 3000). Vui lòng kiểm tra lại tiến trình."
            if status_code == 503
            else f"Lỗi HTTP {status_code}: {text}"
        )
        return {
            "error": True,
            "status_code": status_code,
            "is_connection_error": is_conn_err,
            "message": msg,
        }
    if isinstance(err, httpx.HTTPError):
        logger.error("Lỗi mạng HTTP khi %s: %s", operation, err)
        return {
            "error": True,
            "status_code": 503,
            "is_connection_error": True,
            "message": f"Không thể kết nối đến máy chủ Backend (Port 3000). Lỗi mạng: {err}",
        }

    logger.error("Lỗi ngoại lệ không xác định khi %s: %s", operation, err)
    return {"error": True, "message": str(err)}


def is_connection_error(resp: Any) -> bool:
    """Kiểm tra phản hồi API có phải là lỗi mất kết nối Backend hoặc 503 Service Unavailable."""
    if isinstance(resp, dict) and resp.get("error"):
        if resp.get("is_connection_error"):
            return True
        status_code = resp.get("status_code")
        if status_code in (502, 503, 504):
            return True
        msg = str(resp.get("message", "")).lower()
        if "không thể kết nối" in msg or "connecterror" in msg or "503" in msg:
            return True
    return False


# ===========================================================================
# 1. USERS API (Table 1: users)
# ===========================================================================
async def get_users(
    username: Optional[str] = None,
    email: Optional[str] = None,
    role: Optional[str] = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        params = {
            k: v
            for k, v in {"username": username, "email": email, "role": role}.items()
            if v
        }
        res = await client.get("/users", params=params)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy danh sách users")


async def get_user_by_id(user_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.get(f"/users/{user_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy thông tin user")


async def create_user(
    username: str, email: str, password: str = "default_pass", role: str = "user"
) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.post(
            "/users",
            json={
                "username": username,
                "email": email,
                "password": password,
                "role": role,
            },
        )
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "tạo user")


async def login_user(username_or_email: str, password: str = "") -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.post(
            "/users/login", json={"login": username_or_email, "password": password}
        )
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "đăng nhập user")


async def update_user(user_id: int, **fields: Any) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.put(f"/users/{user_id}", json=fields)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "cập nhật user")


async def delete_user(user_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.delete(f"/users/{user_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "xóa user")


# ===========================================================================
# 2. USER PROFILES API (Table 2: user_profiles)
# ===========================================================================
async def get_profiles(
    user_id: Optional[int] = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        params = {"user_id": user_id} if user_id else None
        res = await client.get("/profiles", params=params)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy danh sách profiles")


async def get_profile_by_id(profile_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.get(f"/profiles/{profile_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy chi tiết profile")


async def get_user_profile(user_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.get(f"/users/{user_id}/profile")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy profile theo user_id")


async def create_profile(user_id: int, **fields: Any) -> dict[str, Any]:
    try:
        client = get_client()
        payload = {"user_id": user_id, **fields}
        res = await client.post("/profiles", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "tạo profile")


async def update_profile(profile_id: int, **fields: Any) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.put(f"/profiles/{profile_id}", json=fields)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "cập nhật profile")


async def delete_profile(profile_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.delete(f"/profiles/{profile_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "xóa profile")


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


async def get_category_by_id(cat_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.get(f"/categories/{cat_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy chi tiết category")


async def create_category(
    name: str, user_id: Optional[int] = 1, **fields: Any
) -> dict[str, Any]:
    try:
        client = get_client()
        payload = {"name": name, "user_id": user_id, **fields}
        res = await client.post("/categories", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "tạo category")


async def update_category(cat_id: int, **fields: Any) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.put(f"/categories/{cat_id}", json=fields)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "cập nhật category")


async def delete_category(cat_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.delete(f"/categories/{cat_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "xóa category")


# ===========================================================================
# 4. FOLDERS API (Table 4: folders)
# ===========================================================================
async def get_folders(
    user_id: Optional[int] = None,
    category_id: Optional[int] = None,
    parent_id: Optional[int] = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        params = {
            k: v
            for k, v in {
                "user_id": user_id,
                "category_id": category_id,
                "parent_id": parent_id,
            }.items()
            if v is not None
        }
        res = await client.get("/folders", params=params)
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
# 5. DOCUMENTS API (Table 5: documents)
# ===========================================================================
async def upload_doc(
    file_bytes: bytes, filename: str, user_id: int = 1
) -> dict[str, Any]:
    """Gửi request POST /documents/upload dạng multipart/form-data."""
    try:
        client = get_client()
        files = {"file": (filename, file_bytes)}
        data = {"user_id": str(user_id)}
        res = await client.post("/documents/upload", files=files, data=data)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "upload tài liệu")


async def get_documents(
    user_id: Optional[int] = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        params = {"user_id": user_id} if user_id else None
        res = await client.get("/documents", params=params)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy danh sách documents")


async def get_document_by_id(doc_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.get(f"/documents/{doc_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy chi tiết document")


async def update_document(doc_id: int, **fields: Any) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.put(f"/documents/{doc_id}", json=fields)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "cập nhật document")


async def delete_document(doc_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.delete(f"/documents/{doc_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "xóa document")


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


async def update_deck(deck_id: int, **fields: Any) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.put(f"/decks/{deck_id}", json=fields)
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
    question: str, answer: str, deck_id: Optional[int] = 1, **fields: Any
) -> dict[str, Any]:
    try:
        client = get_client()
        payload = {"question": question, "answer": answer, "deck_id": deck_id, **fields}
        res = await client.post("/cards", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "tạo card")


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
        params = {"deck_id": deck_id} if deck_id is not None else None
        res = await client.delete("/cards", params=params)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "xóa toàn bộ cards")


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
# 10. AI GENERATION LOGS API (Table 10: ai_generation_logs)
# ===========================================================================
async def get_ai_logs(
    user_id: Optional[int] = None,
    document_id: Optional[int] = None,
    deck_id: Optional[int] = None,
    status: Optional[str] = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        params = {
            k: v
            for k, v in {
                "user_id": user_id,
                "document_id": document_id,
                "deck_id": deck_id,
                "status": status,
            }.items()
            if v is not None
        }
        res = await client.get("/ai-logs", params=params)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy danh sách ai_logs")


async def get_ai_log_by_id(log_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.get(f"/ai-logs/{log_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy chi tiết ai_log")


async def create_ai_log(user_id: int, **fields: Any) -> dict[str, Any]:
    try:
        client = get_client()
        payload = {"user_id": user_id, **fields}
        res = await client.post("/ai-logs", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "tạo ai_log")


async def update_ai_log(log_id: int, **fields: Any) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.put(f"/ai-logs/{log_id}", json=fields)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "cập nhật ai_log")


async def delete_ai_log(log_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.delete(f"/ai-logs/{log_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "xóa ai_log")


# ===========================================================================
# 11. STUDY SESSIONS API (Table 11: study_sessions)
# ===========================================================================
async def get_study_sessions(
    user_id: Optional[int] = None, deck_id: Optional[int] = None
) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        params = {
            k: v
            for k, v in {"user_id": user_id, "deck_id": deck_id}.items()
            if v is not None
        }
        res = await client.get("/study/sessions", params=params)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy danh sách study_sessions")


async def get_study_session_by_id(session_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.get(f"/study/sessions/{session_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy chi tiết study_session")


async def create_study_session(deck_id: int, user_id: int = 1) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.post(
            "/study/sessions", json={"deck_id": deck_id, "user_id": user_id}
        )
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "tạo study_session")


async def end_study_session(session_id: int, total_reviewed: int = 0) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.put(
            f"/study/sessions/{session_id}/end", json={"total_reviewed": total_reviewed}
        )
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "kết thúc study_session")


async def delete_study_session(session_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.delete(f"/study/sessions/{session_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "xóa study_session")


# ===========================================================================
# 12. STUDY REVIEWS API (Table 12: study_reviews)
# ===========================================================================
async def get_study_reviews(
    session_id: Optional[int] = None,
    card_id: Optional[int] = None,
    user_id: Optional[int] = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        params = {
            k: v
            for k, v in {
                "session_id": session_id,
                "card_id": card_id,
                "user_id": user_id,
            }.items()
            if v is not None
        }
        res = await client.get("/study/reviews", params=params)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy danh sách study_reviews")


async def get_study_review_by_id(review_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.get(f"/study/reviews/{review_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy chi tiết study_review")


async def submit_srs_review(
    session_id: int, card_id: int, rating: int
) -> dict[str, Any]:
    """Gửi đánh giá SRS SM-2 (1: Again, 2: Hard, 3: Good, 4: Easy)."""
    if rating not in {1, 2, 3, 4}:
        return {
            "error": True,
            "message": f"Rating không hợp lệ ({rating}). Đánh giá hợp lệ trong khoảng [1, 2, 3, 4].",
        }
    try:
        client = get_client()
        payload = {
            "session_id": session_id,
            "card_id": card_id,
            "review_rating": rating,
        }
        res = await client.post("/study/review", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "ghi nhận đánh giá SRS")


async def delete_study_review(review_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.delete(f"/study/reviews/{review_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "xóa study_review")


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


async def check_system_health() -> dict[str, Any]:
    """Kiểm tra sức khỏe hệ thống Backend và AI Pipeline."""
    try:
        client = get_client()
        res = await client.get("/health")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "kiểm tra sức khỏe hệ thống")
