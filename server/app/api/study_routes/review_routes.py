"""
review_routes.py — Study Review endpoints (Table 12: study_reviews).
"""

from __future__ import annotations

from typing import Any
from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.flashcard import Card
from app.models.study import StudyReview, StudySession
from app.services.sm2_service import calculate_sm2_metrics


def submit_study_review():
    """
    Ghi nhận đánh giá ôn tập Spaced Repetition SM-2 (POST /api/study/review)
    ---
    tags:
      - Study & SRS Reviews
    summary: Ghi nhận đánh giá SM-2 (session_id, card_id, user_id, review_rating từ 1-4)
    description: Tự động tính toán ease_factor, interval_days, repetitions, next_review_date và tăng total_reviewed
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - card_id
            - review_rating
          properties:
            card_id:
              type: integer
              example: 1
              description: ID thẻ flashcard
            review_rating:
              type: integer
              example: 3
              description: "Đánh giá chất lượng nhớ (1: Again/Quên, 2: Hard/Khó, 3: Good/Tốt, 4: Easy/Dễ)"
            session_id:
              type: integer
              example: 1
              description: ID phiên học đang diễn ra
            user_id:
              type: integer
              example: 1
              description: ID người học
    responses:
      201:
        description: Ghi nhận đánh giá SM-2 thành công
      400:
        description: Dữ liệu review hoặc rating không hợp lệ
      404:
        description: Thẻ hoặc phiên học không tồn tại
      500:
        description: Lỗi máy chủ
    """
    data = request.get_json(silent=True) or {}
    card_id = data.get("card_id")
    rating_raw = (
        data.get("review_rating") if "review_rating" in data else data.get("rating")
    )

    if not card_id:
        return jsonify({"error": "Trường 'card_id' là bắt buộc"}), 400
    if rating_raw is None:
        return (
            jsonify({"error": "Trường 'review_rating' là bắt buộc (từ 1 đến 4)"}),
            400,
        )

    try:
        card_id = int(card_id)
        review_rating = int(rating_raw)
    except (ValueError, TypeError):
        return jsonify({"error": "card_id và review_rating phải là số nguyên"}), 400

    if review_rating not in {1, 2, 3, 4}:
        return (
            jsonify({"error": "Giá trị 'review_rating' phải thuộc tập [1, 2, 3, 4]"}),
            400,
        )

    card = db.session.get(Card, card_id)
    if not card:
        return jsonify({"error": f"Không tìm thấy flashcard với ID {card_id}"}), 404

    session_id = data.get("session_id")
    if session_id:
        try:
            session_id = int(session_id)
        except (ValueError, TypeError):
            session_id = None

    user_id = data.get("user_id")
    if user_id:
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            user_id = None

    session = None
    if session_id:
        session = db.session.get(StudySession, session_id)
        if not session:
            return (
                jsonify({"error": f"Không tìm thấy phiên học với ID {session_id}"}),
                404,
            )
        if not user_id:
            user_id = session.user_id

    if not user_id:
        if card.deck and card.deck.user_id:
            user_id = card.deck.user_id
        else:
            return (
                jsonify({"error": "Không thể xác định user_id cho lượt đánh giá này"}),
                400,
            )

    # 1. Truy vấn lịch sử ôn tập gần nhất của thẻ này bởi user
    last_review = (
        StudyReview.query.filter_by(user_id=user_id, card_id=card_id)
        .order_by(StudyReview.id.desc())
        .first()
    )

    prev_ef = last_review.ease_factor if last_review else 2.5
    prev_interval = last_review.interval_days if last_review else 1
    prev_repetitions = last_review.repetitions if last_review else 0

    # 2. Thuật toán SuperMemo SM-2 qua sm2_service
    metrics = calculate_sm2_metrics(
        review_rating=review_rating,
        prev_ef=prev_ef,
        prev_interval=prev_interval,
        prev_repetitions=prev_repetitions,
    )

    # 3. Tăng biến đếm total_reviewed trong phiên học
    if session:
        session.total_reviewed = (session.total_reviewed or 0) + 1

    review = StudyReview(
        session_id=session_id,
        card_id=card_id,
        user_id=user_id,
        review_rating=review_rating,
        ease_factor=metrics["ease_factor"],
        interval_days=metrics["interval_days"],
        repetitions=metrics["repetitions"],
        next_review_date=metrics["next_review_date"],
        reviewed_at=metrics["reviewed_at"],
    )

    try:
        db.session.add(review)
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Ghi nhận đánh giá SM-2 thành công",
                    "review": review.to_dict(),
                    "sm2_metrics": {
                        "ease_factor": review.ease_factor,
                        "interval_days": review.interval_days,
                        "repetitions": review.repetitions,
                        "next_review_date": (
                            review.next_review_date.isoformat()
                            if review.next_review_date
                            else None
                        ),
                    },
                }
            ),
            201,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi lưu trữ đánh giá: {str(exc)}"}), 500


def list_study_reviews():
    """
    Danh sách lịch sử ôn tập (GET /api/study/reviews)
    ---
    tags:
      - Study & SRS Reviews
    summary: Lấy danh sách lịch sử các lượt review đánh giá thẻ
    parameters:
      - name: user_id
        in: query
        type: integer
        required: false
        description: Lọc theo người dùng
      - name: session_id
        in: query
        type: integer
        required: false
        description: Lọc theo phiên học
      - name: card_id
        in: query
        type: integer
        required: false
        description: Lọc theo thẻ
    responses:
      200:
        description: Danh sách đánh giá
      500:
        description: Lỗi truy vấn
    """
    user_id = request.args.get("user_id", type=int)
    session_id = request.args.get("session_id", type=int)
    card_id = request.args.get("card_id", type=int)

    query = StudyReview.query
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    if session_id is not None:
        query = query.filter_by(session_id=session_id)
    if card_id is not None:
        query = query.filter_by(card_id=card_id)

    reviews = query.order_by(StudyReview.reviewed_at.desc()).all()
    return jsonify([r.to_dict() for r in reviews]), 200


def get_study_review_by_id(review_id: int):
    """
    Lấy chi tiết một lượt đánh giá (GET /api/study/reviews/{review_id})
    ---
    tags:
      - Study & SRS Reviews
    summary: Lấy chi tiết một lượt review theo ID
    parameters:
      - name: review_id
        in: path
        type: integer
        required: true
        description: ID bản ghi đánh giá
    responses:
      200:
        description: Chi tiết đánh giá
      404:
        description: Không tìm thấy
    """
    review = db.session.get(StudyReview, review_id)
    if not review:
        return jsonify({"error": f"Không tìm thấy lượt review với ID {review_id}"}), 404
    return jsonify(review.to_dict()), 200


def delete_study_review_by_id(review_id: int):
    """
    Xóa một lượt đánh giá (DELETE /api/study/reviews/{review_id})
    ---
    tags:
      - Study & SRS Reviews
    summary: Xóa một lượt review
    parameters:
      - name: review_id
        in: path
        type: integer
        required: true
        description: ID lượt review cần xóa
    responses:
      200:
        description: Xóa thành công
      404:
        description: Không tìm thấy
      500:
        description: Lỗi máy chủ
    """
    review = db.session.get(StudyReview, review_id)
    if not review:
        return jsonify({"error": f"Không tìm thấy lượt review với ID {review_id}"}), 404

    try:
        db.session.delete(review)
        db.session.commit()
        return (
            jsonify({"message": f"Đã xóa lượt review ID {review_id} thành công"}),
            200,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi xóa review: {str(exc)}"}), 500


def register_review_routes(bp: Blueprint) -> None:
    bp.add_url_rule("/review", view_func=submit_study_review, methods=["POST"])
    bp.add_url_rule("/reviews", view_func=list_study_reviews, methods=["GET"])
    bp.add_url_rule(
        "/reviews/<int:review_id>", view_func=get_study_review_by_id, methods=["GET"]
    )
    bp.add_url_rule(
        "/reviews/<int:review_id>",
        view_func=delete_study_review_by_id,
        methods=["DELETE"],
    )
