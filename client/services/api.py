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
BACKEND_API_URL: str = os.getenv("BACKEND_API_URL", "http://127.0.0.1:3000/api").rstrip("/")
DEFAULT_TIMEOUT: float = 120.0

_client: Optional[httpx.AsyncClient] = None


def get_client() -> httpx.AsyncClient:
    """Tái sử dụng singleton AsyncClient để tối ưu hóa connection pooling."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=BACKEND_API_URL,
            timeout=httpx.Timeout(DEFAULT_TIMEOUT, connect=10.0),
        )
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
        logger.error("Lỗi kết nối Backend tại %s khi %s: %s", BACKEND_API_URL, operation, err)
        return {
            "error": True,
            "message": f"Không thể kết nối đến máy chủ Backend ({BACKEND_API_URL}). Vui lòng kiểm tra server.",
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
            "message": f"Quá thời gian phản hồi từ máy chủ Backend ({DEFAULT_TIMEOUT}s). Tiến trình AI đang bận.",
        }
    if isinstance(err, httpx.HTTPStatusError):
        logger.error(
            "Lỗi HTTP %s khi %s: %s",
            err.response.status_code,
            operation,
            err.response.text,
        )
        return {
            "error": True,
            "message": f"Lỗi HTTP {err.response.status_code}: {err.response.text}",
        }
    if isinstance(err, httpx.HTTPError):
        logger.error("Lỗi mạng HTTP khi %s: %s", operation, err)
        return {"error": True, "message": f"Lỗi mạng HTTP: {err}"}

    logger.error("Lỗi ngoại lệ không xác định khi %s: %s", operation, err)
    return {"error": True, "message": str(err)}


async def upload_doc(
    file_bytes: bytes, filename: str, user_id: int = 1
) -> dict[str, Any]:
    """
    Gửi request POST /documents/upload dạng multipart/form-data để trích xuất text tài liệu.
    """
    try:
        client = get_client()
        files = {"file": (filename, file_bytes)}
        data = {"user_id": str(user_id)}
        response = await client.post("/documents/upload", files=files, data=data)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as err:
        return _handle_http_error(err, "upload tài liệu")
    except Exception as err:
        return _handle_http_error(err, "upload tài liệu")


async def generate_cards(
    doc_id: int, deck_id: Optional[int] = 1, user_id: int = 1
) -> dict[str, Any]:
    """
    Gửi request POST /generate-from-doc/{doc_id} để tạo flashcard tự động bằng AI.
    """
    try:
        client = get_client()
        payload: dict[str, Any] = {"user_id": user_id}
        if deck_id is not None:
            payload["deck_id"] = deck_id
        response = await client.post(f"/generate-from-doc/{doc_id}", json=payload)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as err:
        return _handle_http_error(err, "sinh flashcards từ tài liệu")
    except Exception as err:
        return _handle_http_error(err, "sinh flashcards từ tài liệu")


async def transcribe_audio(
    file_bytes: bytes, filename: str = "audio.wav", language: str = "vi"
) -> dict[str, Any]:
    """
    Gửi request POST /transcribe dạng multipart/form-data để bóc băng âm thanh (STT).
    """
    try:
        client = get_client()
        files = {"file": (filename, file_bytes)}
        data = {"language": language}
        response = await client.post("/transcribe", files=files, data=data)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as err:
        return _handle_http_error(err, "bóc băng âm thanh")
    except Exception as err:
        return _handle_http_error(err, "bóc băng âm thanh")


async def get_decks() -> list[dict[str, Any]] | dict[str, Any]:
    """
    Gửi request GET /decks để lấy danh sách bộ thẻ kèm số lượng thẻ bên trong.
    """
    try:
        client = get_client()
        response = await client.get("/decks")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as err:
        return _handle_http_error(err, "lấy danh sách bộ thẻ")
    except Exception as err:
        return _handle_http_error(err, "lấy danh sách bộ thẻ")


async def get_cards(
    deck_id: Optional[int] = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    """
    Gửi request GET /cards (hỗ trợ lọc theo query param ?deck_id={deck_id}).
    """
    try:
        client = get_client()
        params = {"deck_id": deck_id} if deck_id is not None else None
        response = await client.get("/cards", params=params)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as err:
        return _handle_http_error(err, "lấy danh sách flashcards")
    except Exception as err:
        return _handle_http_error(err, "lấy danh sách flashcards")


async def submit_srs_review(
    session_id: int, card_id: int, rating: int
) -> dict[str, Any]:
    """
    Gửi request POST /study/review ghi nhận kết quả ôn tập thuật toán SM-2 SRS.
    Rating hợp lệ trong khoảng [1, 2, 3, 4].
    """
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
        response = await client.post("/study/review", json=payload)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as err:
        return _handle_http_error(err, "ghi nhận đánh giá SRS")
    except Exception as err:
        return _handle_http_error(err, "ghi nhận đánh giá SRS")


async def generate_flashcards(
    text: str, deck_id: Optional[int] = None
) -> list[dict[str, Any]] | dict[str, Any]:
    """
    Gửi yêu cầu sinh flashcard từ văn bản thuần tới Backend (tương thích ngược).
    """
    payload: dict[str, Any] = {"text": text}
    if deck_id is not None:
        payload["deck_id"] = deck_id

    try:
        client = get_client()
        response = await client.post("/generate", json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("cards", data if isinstance(data, list) else [])
    except httpx.HTTPError as err:
        return _handle_http_error(err, "sinh flashcards từ văn bản")
    except Exception as err:
        return _handle_http_error(err, "sinh flashcards từ văn bản")
