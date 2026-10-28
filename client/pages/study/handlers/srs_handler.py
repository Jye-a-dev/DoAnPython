"""
srs_handler.py — Logic nghiệp vụ tải dữ liệu bài học, giải mã Deck và tương tác SM-2 SRS.
"""

from __future__ import annotations

import urllib.parse
from typing import Any, Dict, List, Optional, Tuple
from services import api


async def resolve_deck(
    identifier: str | int, user_id: int
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Giải mã deck_identifier theo ID số nguyên hoặc Title/Slug tiếng Việt URL-encoded."""
    raw_str = urllib.parse.unquote(str(identifier)).strip()
    if not raw_str:
        return None, "Định danh bộ thẻ không hợp lệ"

    # 1. Thử truy vấn trực tiếp theo ID số
    if raw_str.isdigit():
        deck_resp = await api.get_deck_by_id(int(raw_str))
        if api.is_connection_error(deck_resp):
            return None, "Không thể kết nối đến máy chủ Backend"
        if isinstance(deck_resp, dict) and "id" in deck_resp:
            return deck_resp, None

    # 2. Truy vấn danh sách bộ thẻ của User để match theo Title hoặc Slug
    decks_resp = await api.get_decks(user_id=user_id)
    if api.is_connection_error(decks_resp):
        return None, "Không thể kết nối đến máy chủ Backend"
    if not isinstance(decks_resp, list):
        return None, "Không thể tải danh sách bộ thẻ"

    norm_target = raw_str.lower().replace("-", " ")
    for d in decks_resp:
        if not isinstance(d, dict):
            continue
        if str(d.get("id")) == raw_str:
            return d, None
        title = str(d.get("title", "")).strip().lower()
        if title == raw_str.lower() or title == norm_target:
            return d, None
        slug = title.replace(" ", "-")
        if slug == raw_str.lower():
            return d, None

    return None, f"Không tìm thấy bộ thẻ tương ứng với '{raw_str}'"


async def load_deck_cards(
    deck_id: int, user_id: int
) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """Tải chính xác danh sách thẻ thuộc về Deck chỉ định."""
    cards_resp = await api.get_cards(deck_id=deck_id, user_id=user_id)
    if api.is_connection_error(cards_resp):
        return None, "Mất kết nối máy chủ khi nạp thẻ"
    if isinstance(cards_resp, dict) and cards_resp.get("error"):
        return None, cards_resp.get("message", "Lỗi tải thẻ từ hệ thống")
    if isinstance(cards_resp, list):
        return [c for c in cards_resp if isinstance(c, dict)], None
    return [], None


async def start_study_session(deck_id: int, user_id: int) -> int:
    """Khởi tạo phiên ôn tập mới và trả về session_id."""
    sess_resp = await api.create_study_session(deck_id=deck_id, user_id=user_id)
    if isinstance(sess_resp, dict):
        return sess_resp.get("session_id") or sess_resp.get("id") or 1
    return 1


async def record_card_review(session_id: int, card_id: int, rating: int) -> None:
    """Gửi đánh giá SM-2 (1-4) lên máy chủ."""
    await api.submit_srs_review(session_id=session_id, card_id=card_id, rating=rating)


async def complete_study_session(session_id: int, total_reviewed: int) -> None:
    """Kết thúc phiên ôn tập khi đã duyệt hết thẻ."""
    await api.end_study_session(session_id=session_id, total_reviewed=total_reviewed)
