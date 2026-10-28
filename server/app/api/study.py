"""
study.py — Study Sessions & SRS Reviews API endpoints (Tag: Study & SRS Reviews).
Quản lý thực thể: study_sessions (Table 11) và study_reviews (Table 12).
Thuật toán: Lặp lại ngắt quãng Spaced Repetition (SuperMemo SM-2).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.flashcard import Card, Deck
from app.models.study import StudyReview, StudySession
from app.models.user import User

study_bp = Blueprint("study", __name__, url_prefix="/api/study")


@study_bp.route("/sessions", methods=["POST"])
def start_study_session():
    """
    Mở phiên học mới (POST /api/study/sessions)
    ---
    tags:
      - Study & SRS Reviews
    summary: Mở phiên học mới (user_id, deck_id), trả về session_id
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - user_id
            - deck_id
          properties:
            user_id:
              type: integer
              example: 1
              description: ID người học
            deck_id:
              type: integer
              example: 1
              description: ID bộ thẻ ôn tập
    responses:
      201:
        description: Khởi tạo phiên học thành công
      400:
        description: Thiếu thông tin user_id hoặc deck_id
      404:
        description: Người dùng hoặc bộ thẻ không tồn tại
      500:
        description: Lỗi máy chủ
    """
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    deck_id = data.get("deck_id")

    if not user_id or not deck_id:
        return jsonify({"error": "Trường 'user_id' và 'deck_id' là bắt buộc"}), 400

    try:
        user_id = int(user_id)
        deck_id = int(deck_id)
    except (ValueError, TypeError):
        return (
            jsonify({"error": "Trường 'user_id' và 'deck_id' phải là số nguyên"}),
            400,
        )

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": f"Không tìm thấy người dùng ID {user_id}"}), 404

    deck = db.session.get(Deck, deck_id)
    if not deck:
        return jsonify({"error": f"Không tìm thấy bộ thẻ ID {deck_id}"}), 404

    session = StudySession(
        user_id=user_id,
        deck_id=deck_id,
        started_at=datetime.now(timezone.utc).replace(tzinfo=None),
        total_reviewed=0,
    )
    try:
        db.session.add(session)
        db.session.commit()
        return (
            jsonify(
                {
                    "session_id": session.id,
                    "session": session.to_dict(),
                    "message": "Bắt đầu phiên học thành công",
                }
            ),
            201,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi tạo phiên học: {str(exc)}"}), 500


@study_bp.route("/sessions/<int:session_id>", methods=["GET"])
def get_study_session_by_id(session_id: int):
    """
    Xem chi tiết phiên học (GET /api/study/sessions/{id})
    ---
    tags:
      - Study & SRS Reviews
    summary: Xem chi tiết phiên học (thời gian bắt đầu, kết thúc, tổng thẻ đã ôn)
    parameters:
      - name: session_id
        in: path
        type: integer
        required: true
        description: ID phiên học
    responses:
      200:
        description: Chi tiết phiên học
      404:
        description: Không tìm thấy phiên học
    """
    session = db.session.get(StudySession, session_id)
    if not session:
        return jsonify({"error": f"Không tìm thấy phiên học ID {session_id}"}), 404
    return jsonify(session.to_dict()), 200


@study_bp.route("/sessions/<int:session_id>/end", methods=["PUT"])
def end_study_session(session_id: int):
    """
    Đóng phiên học (PUT /api/study/sessions/{id}/end)
    ---
    tags:
      - Study & SRS Reviews
    summary: Đóng phiên học (cập nhật ended_at = CURRENT_TIMESTAMP)
    parameters:
      - name: session_id
        in: path
        type: integer
        required: true
        description: ID phiên học
      - name: body
        in: body
        required: false
        schema:
          type: object
          properties:
            total_reviewed:
              type: integer
              example: 15
              description: Cập nhật số thẻ đã ôn (tùy chọn)
    responses:
      200:
        description: Kết thúc phiên học thành công
      404:
        description: Không tìm thấy phiên học
      500:
        description: Lỗi máy chủ
    """
    session = db.session.get(StudySession, session_id)
    if not session:
        return jsonify({"error": f"Không tìm thấy phiên học ID {session_id}"}), 404

    data = request.get_json(silent=True) or {}
    session.ended_at = datetime.now(timezone.utc).replace(tzinfo=None)
    if "total_reviewed" in data:
        try:
            session.total_reviewed = int(data["total_reviewed"])
        except (ValueError, TypeError):
            pass

    try:
        db.session.commit()
        return (
            jsonify({"message": "Đã kết thúc phiên học", "session": session.to_dict()}),
            200,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi đóng phiên học: {str(exc)}"}), 500


@study_bp.route("/sessions", methods=["GET"])
def list_study_sessions():
    """
    Lịch sử các phiên học (GET /api/study/sessions)
    ---
    tags:
      - Study & SRS Reviews
    summary: Lịch sử các phiên học (lọc theo ?user_id=, ?deck_id=)
    parameters:
      - name: user_id
        in: query
        type: integer
        required: false
        description: Lọc theo người dùng
      - name: deck_id
        in: query
        type: integer
        required: false
        description: Lọc theo bộ thẻ
    responses:
      200:
        description: Danh sách các phiên học
      500:
        description: Lỗi máy chủ
    """
    user_id = request.args.get("user_id", type=int)
    deck_id = request.args.get("deck_id", type=int)

    query = StudySession.query
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    if deck_id is not None:
        query = query.filter_by(deck_id=deck_id)

    sessions = query.order_by(StudySession.id.desc()).all()
    return jsonify([s.to_dict() for s in sessions]), 200


@study_bp.route("/sessions/<int:session_id>", methods=["DELETE"])
def delete_study_session_by_id(session_id: int):
    """
    Xóa phiên học (DELETE /api/study/sessions/{id})
    ---
    tags:
      - Study & SRS Reviews
    summary: Xóa phiên học (tự động xóa các review liên quan theo ON DELETE CASCADE)
    parameters:
      - name: session_id
        in: path
        type: integer
        required: true
        description: ID phiên học cần xóa
    responses:
      200:
        description: Đã xóa phiên học thành công
      404:
        description: Không tìm thấy phiên học
    """
    session = db.session.get(StudySession, session_id)
    if not session:
        return jsonify({"error": f"Không tìm thấy phiên học ID {session_id}"}), 404

    try:
        db.session.delete(session)
        db.session.commit()
        return jsonify({"message": f"Đã xóa phiên học ID {session_id} thành công"}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi xóa phiên học: {str(exc)}"}), 500


@study_bp.route("/review", methods=["POST"])
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

    # 2. Thuật toán SuperMemo SM-2 chuẩn hóa cho thang điểm 1-4
    # Map [1, 2, 3, 4] -> thang SuperMemo q trong [2, 3, 4, 5]
    q_sm = review_rating + 1
    new_ef = prev_ef + (0.1 - (5 - q_sm) * (0.08 + (5 - q_sm) * 0.02))
    if new_ef < 1.3:
        new_ef = 1.3

    if review_rating < 3:
        # Đánh giá 1 (Again/Quên) hoặc 2 (Hard/Khó chưa đạt) -> lặp lại từ đầu
        new_repetitions = 0
        new_interval = 1
    else:
        # Đánh giá 3 (Good/Tốt) hoặc 4 (Easy/Dễ dàng) -> tăng chu kỳ
        new_repetitions = prev_repetitions + 1
        if new_repetitions == 1:
            new_interval = 1
        elif new_repetitions == 2:
            new_interval = 6
        else:
            new_interval = max(1, round(prev_interval * new_ef))
        if review_rating == 4:
            new_interval = round(new_interval * 1.3)

    now_dt = datetime.now(timezone.utc).replace(tzinfo=None)
    next_review_date = now_dt + timedelta(days=new_interval)

    # 3. Tăng biến đếm total_reviewed trong phiên học
    if session:
        session.total_reviewed = (session.total_reviewed or 0) + 1

    review = StudyReview(
        session_id=session_id,
        card_id=card_id,
        user_id=user_id,
        review_rating=review_rating,
        ease_factor=round(new_ef, 2),
        interval_days=new_interval,
        repetitions=new_repetitions,
        next_review_date=next_review_date,
        reviewed_at=now_dt,
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


@study_bp.route("/reviews", methods=["GET"])
def list_study_reviews():
    """
    Truy vấn lịch sử đánh giá thẻ (GET /api/study/reviews)
    ---
    tags:
      - Study & SRS Reviews
    summary: Truy vấn lịch sử đánh giá thẻ (lọc theo ?user_id=, ?card_id=, ?session_id=)
    parameters:
      - name: user_id
        in: query
        type: integer
        required: false
        description: Lọc theo ID người dùng
      - name: card_id
        in: query
        type: integer
        required: false
        description: Lọc theo ID thẻ
      - name: session_id
        in: query
        type: integer
        required: false
        description: Lọc theo ID phiên học
    responses:
      200:
        description: Danh sách lượt đánh giá SM-2
      500:
        description: Lỗi máy chủ
    """
    user_id = request.args.get("user_id", type=int)
    card_id = request.args.get("card_id", type=int)
    session_id = request.args.get("session_id", type=int)

    query = StudyReview.query
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    if card_id is not None:
        query = query.filter_by(card_id=card_id)
    if session_id is not None:
        query = query.filter_by(session_id=session_id)

    reviews = query.order_by(StudyReview.id.desc()).all()
    return jsonify([r.to_dict() for r in reviews]), 200


@study_bp.route("/reviews/<int:review_id>", methods=["GET"])
def get_study_review_by_id(review_id: int):
    """
    Xem chi tiết một lượt đánh giá (GET /api/study/reviews/{id})
    ---
    tags:
      - Study & SRS Reviews
    summary: Xem chi tiết một lượt đánh giá theo ID
    parameters:
      - name: review_id
        in: path
        type: integer
        required: true
        description: ID lượt đánh giá
    responses:
      200:
        description: Chi tiết đánh giá
      404:
        description: Không tìm thấy đánh giá
    """
    review = db.session.get(StudyReview, review_id)
    if not review:
        return jsonify({"error": f"Không tìm thấy lượt đánh giá ID {review_id}"}), 404
    return jsonify(review.to_dict()), 200


@study_bp.route("/reviews/<int:review_id>", methods=["DELETE"])
def delete_study_review_by_id(review_id: int):
    """
    Xóa một lượt đánh giá (DELETE /api/study/reviews/{id})
    ---
    tags:
      - Study & SRS Reviews
    summary: Xóa một bản ghi đánh giá ôn tập
    parameters:
      - name: review_id
        in: path
        type: integer
        required: true
        description: ID đánh giá cần xóa
    responses:
      200:
        description: Đã xóa lượt đánh giá thành công
      404:
        description: Không tìm thấy đánh giá
    """
    review = db.session.get(StudyReview, review_id)
    if not review:
        return jsonify({"error": f"Không tìm thấy lượt đánh giá ID {review_id}"}), 404

    try:
        db.session.delete(review)
        db.session.commit()
        return (
            jsonify({"message": f"Đã xóa lượt đánh giá ID {review_id} thành công"}),
            200,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi xóa đánh giá: {str(exc)}"}), 500
