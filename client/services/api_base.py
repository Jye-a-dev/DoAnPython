from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Optional
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
            "message": "Không thể kết nối đến máy chủ Backend (Port 3000). Vui lòng kiểm tra lại tiến trình.",
        }
    if isinstance(err, httpx.ReadTimeout):
        logger.error(
            "Quá hạn thời gian chờ phản hồi (%ss) khi %s: %s",
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
        if resp is not None:
            try:
                body = resp.json()
                if isinstance(body, dict):
                    text = body.get("error") or body.get("message") or text
            except Exception:
                pass
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
            else (text if status_code == 404 else f"Lỗi HTTP {status_code}: {text}")
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
