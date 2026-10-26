from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.flashcard import Card, Deck
from app.models.study import StudyReview, StudySession
from app.models.user import User
from app.validators.study_validator import (
    validate_study_review_payload,
    validate_study_session_payload,
)

study_bp = Blueprint("study", __name__, url_prefix="/api/study")


@study_bp.route("/sessions", methods=["POST"])
def start_study_session():
    """
    Mở phiên học mới (Study Session)
    ---
    tags:
      - Study
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
            deck_id:
              type: integer
              example: 1
    responses:
      201:
        description: Khởi tạo phiên học thành công
      400:
        description: Dữ liệu đầu vào không hợp lệ
      404:
        description: Người dùng hoặc bộ thẻ không tồn tại
    """
    data = request.get_json(silent=True) or {}
    is_valid, error_msg, cleaned_data = validate_study_session_payload(data)
    if not is_valid or cleaned_data is None:
        return jsonify({"error": error_msg}), 400

    user_id = cleaned_data["user_id"]
    deck_id = cleaned_data["deck_id"]

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": f"Không tìm thấy người dùng với ID {user_id}"}), 404

    deck = db.session.get(Deck, deck_id)
    if not deck:
        return jsonify({"error": f"Không tìm thấy bộ thẻ với ID {deck_id}"}), 404

    session = StudySession(
        user_id=user_id,
        deck_id=deck_id,
        started_at=datetime.utcnow(),
        total_reviewed=0,
    )
    db.session.add(session)
    db.session.commit()

    return (
        jsonify({"message": "Bắt đầu phiên học thành công", "session": session.to_dict()}),
        201,
    )


@study_bp.route("/sessions/<int:session_id>/end", methods=["PUT"])
def end_study_session(session_id: int):
    """Kết thúc một phiên học"""
    session = db.session.get(StudySession, session_id)
    if not session:
        return jsonify({"error": f"Không tìm thấy phiên học với ID {session_id}"}), 404

    session.ended_at = datetime.utcnow()
    db.session.commit()
    return (
        jsonify({"message": "Đã kết thúc phiên học", "session": session.to_dict()}),
        200,
    )


@study_bp.route("/review", methods=["POST"])
def submit_study_review():
    """
    Ghi nhận đánh giá thuật toán lặp lại ngắt quãng (SRS SM-2)
    ---
    tags:
      - Study
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
            review_rating:
              type: integer
              example: 3
              description: Đánh giá chất lượng nhớ [1, 2, 3, 4]
            ease_factor:
              type: number
              example: 2.5
              description: Hệ số dễ (phải > 1.3)
            interval_days:
              type: integer
              example: 1
            session_id:
              type: integer
              example: 1
            user_id:
              type: integer
              example: 1
    responses:
      201:
        description: Ghi nhận đánh giá thành công
      400:
        description: Dữ liệu review không hợp lệ
      404:
        description: Thẻ hoặc phiên học không tồn tại
    """
    data = request.get_json(silent=True) or {}
    is_valid, error_msg, cleaned_data = validate_study_review_payload(data)
    if not is_valid or cleaned_data is None:
        return jsonify({"error": error_msg}), 400

    card_id = cleaned_data["card_id"]
    card = db.session.get(Card, card_id)
    if not card:
        return jsonify({"error": f"Không tìm thấy flashcard với ID {card_id}"}), 404

    session_id = cleaned_data.get("session_id")
    user_id = cleaned_data.get("user_id")

    if session_id:
        session = db.session.get(StudySession, session_id)
        if not session:
            return jsonify({"error": f"Không tìm thấy phiên học với ID {session_id}"}), 404
        if not user_id:
            user_id = session.user_id
        session.total_reviewed += 1

    if not user_id:
        # Lấy user_id từ deck sở hữu thẻ nếu không có session
        if card.deck:
            user_id = card.deck.user_id
        else:
            return jsonify({"error": "Không thể xác định user_id cho lượt đánh giá này"}), 400

    interval_days = cleaned_data["interval_days"]
    next_review_date = datetime.utcnow() + timedelta(days=interval_days)

    review = StudyReview(
        session_id=session_id,
        card_id=card_id,
        user_id=user_id,
        review_rating=cleaned_data["review_rating"],
        ease_factor=cleaned_data["ease_factor"],
        interval_days=interval_days,
        next_review_date=next_review_date,
        reviewed_at=datetime.utcnow(),
    )
    db.session.add(review)
    db.session.commit()

    return (
        jsonify(
            {
                "message": "Ghi nhận đánh giá ôn tập thành công",
                "review": review.to_dict(),
            }
        ),
        201,
    )


@study_bp.route("/sessions", methods=["GET"])
def list_study_sessions():
    """Lấy danh sách các phiên ôn tập"""
    user_id = request.args.get("user_id", type=int)
    deck_id = request.args.get("deck_id", type=int)
    query = StudySession.query
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    if deck_id is not None:
        query = query.filter_by(deck_id=deck_id)
    sessions = query.order_by(StudySession.id.desc()).all()
    return jsonify([s.to_dict() for s in sessions]), 200


@study_bp.route("/sessions/<int:session_id>", methods=["GET"])
def get_study_session_by_id(session_id: int):
    """Lấy thông tin chi tiết một phiên ôn tập"""
    session = db.session.get(StudySession, session_id)
    if not session:
        return jsonify({"error": f"Không tìm thấy phiên học ID {session_id}"}), 404
    return jsonify(session.to_dict()), 200


@study_bp.route("/sessions/<int:session_id>", methods=["PUT"])
def update_study_session_by_id(session_id: int):
    """Cập nhật phiên ôn tập"""
    session = db.session.get(StudySession, session_id)
    if not session:
        return jsonify({"error": f"Không tìm thấy phiên học ID {session_id}"}), 404
    data = request.get_json(silent=True) or {}
    if "total_reviewed" in data:
        session.total_reviewed = int(data["total_reviewed"])
    if "ended_at" in data:
        session.ended_at = datetime.utcnow() if data["ended_at"] else None
    db.session.commit()
    return jsonify(session.to_dict()), 200


@study_bp.route("/sessions/<int:session_id>", methods=["DELETE"])
def delete_study_session_by_id(session_id: int):
    """Xóa phiên ôn tập"""
    session = db.session.get(StudySession, session_id)
    if not session:
        return jsonify({"error": f"Không tìm thấy phiên học ID {session_id}"}), 404
    db.session.delete(session)
    db.session.commit()
    return jsonify({"message": f"Đã xóa phiên học ID {session_id} thành công"}), 200


@study_bp.route("/reviews", methods=["GET"])
def list_study_reviews():
    """Lấy danh sách các lượt đánh giá SM-2"""
    session_id = request.args.get("session_id", type=int)
    card_id = request.args.get("card_id", type=int)
    user_id = request.args.get("user_id", type=int)
    query = StudyReview.query
    if session_id is not None:
        query = query.filter_by(session_id=session_id)
    if card_id is not None:
        query = query.filter_by(card_id=card_id)
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    reviews = query.order_by(StudyReview.id.desc()).all()
    return jsonify([r.to_dict() for r in reviews]), 200


@study_bp.route("/reviews/<int:review_id>", methods=["GET"])
def get_study_review_by_id(review_id: int):
    """Lấy chi tiết một lượt đánh giá SM-2"""
    review = db.session.get(StudyReview, review_id)
    if not review:
        return jsonify({"error": f"Không tìm thấy lượt đánh giá ID {review_id}"}), 404
    return jsonify(review.to_dict()), 200


@study_bp.route("/reviews/<int:review_id>", methods=["DELETE"])
def delete_study_review_by_id(review_id: int):
    """Xóa một lượt đánh giá SM-2"""
    review = db.session.get(StudyReview, review_id)
    if not review:
        return jsonify({"error": f"Không tìm thấy lượt đánh giá ID {review_id}"}), 404
    db.session.delete(review)
    db.session.commit()
    return jsonify({"message": f"Đã xóa lượt đánh giá ID {review_id} thành công"}), 200

