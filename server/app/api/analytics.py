"""
analytics.py — Learning Analytics & Spaced Repetition (SM-2) Streak Heatmap.
GET /api/analytics/streak-heatmap?user_id={id}&year={year}
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict
from flask import Blueprint, jsonify, request
from sqlalchemy import func
from app.core.database import db
from app.models.study import StudyReview, StudySession

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


def _calculate_level(count: int) -> int:
    """Xác định cấp độ màu (Level 0..4) theo số lượng ôn tập thẻ SM-2."""
    if count <= 0:
        return 0
    if count <= 4:
        return 1
    if count <= 9:
        return 2
    if count <= 19:
        return 3
    return 4


@analytics_bp.route("/streak-heatmap", methods=["GET"])
def get_streak_heatmap():
    """
    Biểu đồ đóng băng chuỗi ôn tập (Streak Heatmap)
    ---
    tags:
      - Analytics & Heatmap
    summary: Thống kê số thẻ review SM-2 và session theo từng ngày trong năm
    parameters:
      - name: user_id
        in: query
        type: integer
        required: true
        description: ID người dùng cần thống kê
      - name: year
        in: query
        type: integer
        required: false
        description: Năm thống kê (mặc định là năm hiện tại)
    responses:
      200:
        description: JSON map chuỗi ôn tập theo ngày
      400:
        description: Thiếu hoặc sai định dạng user_id
    """
    user_id_raw = request.args.get("user_id")
    if not user_id_raw:
        return jsonify({"error": "Tham số 'user_id' là bắt buộc"}), 400

    try:
        user_id = int(user_id_raw)
    except (ValueError, TypeError):
        return jsonify({"error": "Tham số 'user_id' phải là số nguyên"}), 400

    year_raw = request.args.get("year")
    now_year = datetime.utcnow().year
    try:
        year = int(year_raw) if year_raw else now_year
    except (ValueError, TypeError):
        year = now_year

    start_date = f"{year:04d}-01-01"
    end_date = f"{year:04d}-12-31 23:59:59"

    # 1. Thống kê số lượng thẻ đã review theo ngày từ study_reviews
    review_rows = (
        db.session.query(
            func.date(StudyReview.reviewed_at).label("rev_date"),
            func.count(StudyReview.id).label("rev_count"),
        )
        .filter(
            StudyReview.user_id == user_id,
            StudyReview.reviewed_at >= start_date,
            StudyReview.reviewed_at <= end_date,
        )
        .group_by(func.date(StudyReview.reviewed_at))
        .all()
    )

    # 2. Thống kê số lượng session đã hoàn thành theo ngày từ study_sessions
    session_rows = (
        db.session.query(
            func.date(StudySession.started_at).label("sess_date"),
            func.count(StudySession.id).label("sess_count"),
        )
        .filter(
            StudySession.user_id == user_id,
            StudySession.started_at >= start_date,
            StudySession.started_at <= end_date,
        )
        .group_by(func.date(StudySession.started_at))
        .all()
    )

    heatmap: Dict[str, Dict[str, Any]] = {}

    for rev_date, rev_cnt in review_rows:
        if rev_date:
            d_str = str(rev_date)
            cnt = int(rev_cnt or 0)
            heatmap[d_str] = {
                "review_count": cnt,
                "level": _calculate_level(cnt),
                "sessions": 0,
            }

    for sess_date, sess_cnt in session_rows:
        if sess_date:
            d_str = str(sess_date)
            scnt = int(sess_cnt or 0)
            if d_str in heatmap:
                heatmap[d_str]["sessions"] = scnt
            else:
                heatmap[d_str] = {
                    "review_count": 0,
                    "level": 0,
                    "sessions": scnt,
                }

    return jsonify(heatmap), 200
