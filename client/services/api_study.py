from __future__ import annotations

from typing import Any, Optional
from services.api_base import _handle_http_error, get_client


# ===========================================================================
# 5. DOCUMENTS API (Table 5: documents)
# ===========================================================================
async def upload_doc(
    filename: str, file_bytes: bytes, user_id: int = 1, file_type: str = "txt"
) -> dict[str, Any]:
    try:
        client = get_client()
        files = {"file": (filename, file_bytes, "application/octet-stream")}
        data = {"user_id": str(user_id), "file_type": file_type}
        res = await client.post("/documents/upload", files=files, data=data)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "upload document")


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
# 14. HEALTH & SYSTEM API
# ===========================================================================
async def check_system_health() -> dict[str, Any]:
    """Kiểm tra sức khỏe hệ thống Backend và AI Pipeline."""
    try:
        client = get_client()
        res = await client.get("/health")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "kiểm tra sức khỏe hệ thống")
