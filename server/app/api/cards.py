"""
cards.py — Flashcards & Tags Junction API endpoints (Tag: Cards & Tags).
Quản lý thực thể: cards (Table 7) và card_tags (Table 9).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.document import Document
from app.models.flashcard import Card, Deck, Tag, card_tags
from app.services.ai_service import generate_cards_from_document_id

cards_bp = Blueprint("cards", __name__, url_prefix="/api/cards")


@cards_bp.route("", methods=["GET"])
def get_all_cards():
    """
    Lấy danh sách các flashcards (GET /api/cards)
    ---
    tags:
      - Cards & Tags
    summary: Lấy danh sách flashcards (lọc theo ?deck_id=, ?document_id=, ?difficulty=, ?tag_id=)
    parameters:
      - name: deck_id
        in: query
        type: integer
        required: false
        description: Lọc theo ID bộ thẻ
      - name: document_id
        in: query
        type: integer
        required: false
        description: Lọc theo ID tài liệu nguồn
      - name: difficulty
        in: query
        type: string
        required: false
        description: Lọc theo độ khó (easy, medium, hard)
      - name: tag_id
        in: query
        type: integer
        required: false
        description: Lọc theo ID nhãn phân loại (bảng tags qua card_tags)
    responses:
      200:
        description: Danh sách flashcards
      500:
        description: Lỗi truy vấn
    """
    deck_id = request.args.get("deck_id", type=int)
    document_id = request.args.get("document_id", type=int)
    difficulty = request.args.get("difficulty")
    tag_id = request.args.get("tag_id", type=int)

    query = Card.query
    if deck_id is not None:
        query = query.filter_by(deck_id=deck_id)
    if document_id is not None:
        query = query.filter_by(document_id=document_id)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if tag_id is not None:
        query = query.join(card_tags, Card.id == card_tags.c.card_id).filter(
            card_tags.c.tag_id == tag_id
        )

    cards = query.order_by(Card.created_at.desc()).all()
    return jsonify([c.to_dict() for c in cards]), 200


@cards_bp.route("", methods=["POST"])
def create_new_card():
    """
    Tạo mới thẻ flashcard thủ công (POST /api/cards)
    ---
    tags:
      - Cards & Tags
    summary: Tạo thẻ mới thủ công (deck_id, question, answer, explanation, difficulty, document_id)
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - question
            - answer
          properties:
            deck_id:
              type: integer
              example: 1
              description: ID bộ thẻ đích
            question:
              type: string
              example: "Decorator trong Python dùng để làm gì?"
              description: Nội dung câu hỏi (mặt trước)
            answer:
              type: string
              example: "Dùng để bổ sung hoặc thay đổi hành vi của một hàm/phương thức mà không sửa mã gốc."
              description: Nội dung câu trả lời (mặt sau)
            explanation:
              type: string
              example: "Ví dụ: @timer, @app.route"
              description: Giải thích chi tiết
            difficulty:
              type: string
              default: medium
              example: medium
              description: Độ khó (easy, medium, hard)
            document_id:
              type: integer
              example: null
              description: ID tài liệu nguồn (nếu có)
    responses:
      201:
        description: Tạo flashcard thành công
      400:
        description: Câu hỏi hoặc câu trả lời để trống
      500:
        description: Lỗi máy chủ
    """
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or data.get("front") or "").strip()
    answer = (data.get("answer") or data.get("back") or "").strip()

    if not question:
        return (
            jsonify({"error": "Nội dung câu hỏi ('question') không được để trống"}),
            400,
        )
    if not answer:
        return (
            jsonify({"error": "Nội dung câu trả lời ('answer') không được để trống"}),
            400,
        )

    card = Card(
        deck_id=data.get("deck_id"),
        document_id=data.get("document_id"),
        question=question,
        answer=answer,
        explanation=data.get("explanation"),
        difficulty=data.get("difficulty", "medium"),
    )
    try:
        db.session.add(card)
        db.session.commit()
        card_dict = card.to_dict()
        card_dict["message"] = "Tạo flashcard thành công"
        return jsonify(card_dict), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi tạo thẻ: {str(exc)}"}), 500


@cards_bp.route("/<int:card_id>", methods=["GET"])
def get_card_detail(card_id: int):
    """
    Xem chi tiết thẻ kèm danh sách nhãn tags đang gắn (GET /api/cards/{id})
    ---
    tags:
      - Cards & Tags
    summary: Xem chi tiết thẻ kèm danh sách nhãn (tags) đang gắn
    parameters:
      - name: card_id
        in: path
        type: integer
        required: true
        description: ID thẻ flashcard
    responses:
      200:
        description: Chi tiết thẻ kèm tags
      404:
        description: Không tìm thấy thẻ
    """
    card = db.session.get(Card, card_id)
    if not card:
        return jsonify({"error": f"Không tìm thấy flashcard với ID {card_id}"}), 404

    card_dict = card.to_dict()
    card_tags_list: Any = getattr(card, "tags", [])
    card_dict["tag_objects"] = [{"id": t.id, "name": t.name} for t in card_tags_list]
    return jsonify(card_dict), 200


@cards_bp.route("/<int:card_id>", methods=["PUT"])
def update_card_detail(card_id: int):
    """
    Cập nhật nội dung thẻ flashcard (PUT /api/cards/{id})
    ---
    tags:
      - Cards & Tags
    summary: Cập nhật nội dung thẻ (question, answer, explanation, difficulty)
    parameters:
      - name: card_id
        in: path
        type: integer
        required: true
        description: ID thẻ cần cập nhật
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            question:
              type: string
              example: "Câu hỏi cập nhật"
            answer:
              type: string
              example: "Câu trả lời cập nhật"
            explanation:
              type: string
              example: "Giải thích cập nhật"
            difficulty:
              type: string
              example: "hard"
            deck_id:
              type: integer
              example: 1
    responses:
      200:
        description: Cập nhật thẻ thành công
      404:
        description: Không tìm thấy thẻ
      500:
        description: Lỗi máy chủ
    """
    card = db.session.get(Card, card_id)
    if not card:
        return jsonify({"error": f"Không tìm thấy flashcard với ID {card_id}"}), 404

    data = request.get_json(silent=True) or {}
    if "question" in data and str(data["question"]).strip():
        card.question = str(data["question"]).strip()
    if "front" in data and str(data["front"]).strip():
        card.question = str(data["front"]).strip()
    if "answer" in data and str(data["answer"]).strip():
        card.answer = str(data["answer"]).strip()
    if "back" in data and str(data["back"]).strip():
        card.answer = str(data["back"]).strip()
    if "explanation" in data:
        card.explanation = data["explanation"]
    if "difficulty" in data:
        card.difficulty = str(data["difficulty"])
    if "deck_id" in data:
        card.deck_id = data["deck_id"]

    card.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    try:
        db.session.commit()
        card_dict = card.to_dict()
        card_dict["message"] = "Cập nhật flashcard thành công"
        return jsonify(card_dict), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi cập nhật thẻ: {str(exc)}"}), 500


@cards_bp.route("/<int:card_id>", methods=["DELETE"])
def delete_card_endpoint(card_id: int):
    """
    Xóa thẻ flashcard (DELETE /api/cards/{id})
    ---
    tags:
      - Cards & Tags
    summary: Xóa một thẻ flashcard theo ID
    parameters:
      - name: card_id
        in: path
        type: integer
        required: true
        description: ID thẻ cần xóa
    responses:
      200:
        description: Đã xóa flashcard thành công
      404:
        description: Không tìm thấy thẻ
      500:
        description: Lỗi máy chủ khi xóa
    """
    card = db.session.get(Card, card_id)
    if not card:
        return jsonify({"error": f"Không tìm thấy flashcard với ID {card_id}"}), 404

    try:
        db.session.delete(card)
        db.session.commit()
        return jsonify({"message": f"Đã xóa flashcard ID {card_id} thành công"}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi xóa thẻ: {str(exc)}"}), 500


@cards_bp.route("", methods=["DELETE"])
def delete_all_cards_endpoint():
    """
    Xóa hàng loạt flashcards (DELETE /api/cards)
    ---
    tags:
      - Cards & Tags
    summary: Xóa hàng loạt thẻ (cho phép query ?deck_id= để xóa sạch thẻ trong deck)
    parameters:
      - name: deck_id
        in: query
        type: integer
        required: false
        description: ID bộ thẻ cần xóa sạch thẻ bên trong
    responses:
      200:
        description: Đã xóa các thẻ thành công
      500:
        description: Lỗi xóa
    """
    deck_id = request.args.get("deck_id", type=int)
    query = Card.query
    if deck_id is not None:
        query = query.filter_by(deck_id=deck_id)

    cards = query.all()
    count = len(cards)
    try:
        for c in cards:
            db.session.delete(c)
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Đã xóa flashcards thành công",
                    "deleted_count": count,
                    "deck_id": deck_id,
                }
            ),
            200,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi xóa hàng loạt: {str(exc)}"}), 500


@cards_bp.route("/<int:card_id>/tags", methods=["POST"])
def attach_tag_to_card(card_id: int):
    """
    Gán tag cho thẻ (POST /api/cards/{card_id}/tags)
    ---
    tags:
      - Cards & Tags
    summary: Gán tag cho thẻ (thêm bản ghi vào bảng liên kết card_tags)
    parameters:
      - name: card_id
        in: path
        type: integer
        required: true
        description: ID thẻ
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - tag_id
          properties:
            tag_id:
              type: integer
              example: 1
              description: ID của tag cần gán
    responses:
      201:
        description: Gán tag cho thẻ thành công
      400:
        description: Thiếu tag_id
      404:
        description: Không tìm thấy thẻ hoặc tag
      500:
        description: Lỗi máy chủ
    """
    card = db.session.get(Card, card_id)
    if not card:
        return jsonify({"error": f"Không tìm thấy thẻ ID {card_id}"}), 404

    data = request.get_json(silent=True) or {}
    tag_id = data.get("tag_id") or request.args.get("tag_id", type=int)
    if not tag_id:
        return jsonify({"error": "Trường 'tag_id' là bắt buộc trong body JSON"}), 400

    tag = db.session.get(Tag, int(tag_id))
    if not tag:
        return jsonify({"error": f"Không tìm thấy nhãn Tag ID {tag_id}"}), 404

    # Kiểm tra bản ghi trong bảng liên kết card_tags
    existing = (
        db.session.query(card_tags)
        .filter_by(card_id=card_id, tag_id=int(tag_id))
        .first()
    )
    if existing:
        return (
            jsonify(
                {
                    "message": "Tag đã được gán cho thẻ này từ trước",
                    "card_id": card_id,
                    "tag_id": int(tag_id),
                }
            ),
            200,
        )

    try:
        stmt = card_tags.insert().values(
            card_id=card_id,
            tag_id=int(tag_id),
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.session.execute(stmt)
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Gán tag cho thẻ thành công",
                    "card_id": card_id,
                    "tag_id": int(tag_id),
                }
            ),
            201,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi gán tag: {str(exc)}"}), 500


@cards_bp.route("/<int:card_id>/tags/<int:tag_id>", methods=["DELETE"])
def detach_tag_from_card(card_id: int, tag_id: int):
    """
    Gỡ tag khỏi thẻ (DELETE /api/cards/{card_id}/tags/{tag_id})
    ---
    tags:
      - Cards & Tags
    summary: Gỡ tag khỏi thẻ (xóa bản ghi trong bảng liên kết card_tags)
    parameters:
      - name: card_id
        in: path
        type: integer
        required: true
        description: ID thẻ
      - name: tag_id
        in: path
        type: integer
        required: true
        description: ID tag cần gỡ
    responses:
      200:
        description: Đã gỡ nhãn khỏi thẻ thành công
      404:
        description: Quan hệ giữa thẻ và nhãn không tồn tại
      500:
        description: Lỗi máy chủ
    """
    existing = (
        db.session.query(card_tags).filter_by(card_id=card_id, tag_id=tag_id).first()
    )
    if not existing:
        return (
            jsonify(
                {
                    "error": f"Không tìm thấy liên kết giữa thẻ {card_id} và nhãn {tag_id}"
                }
            ),
            404,
        )

    try:
        stmt = card_tags.delete().where(
            card_tags.c.card_id == card_id, card_tags.c.tag_id == tag_id
        )
        db.session.execute(stmt)
        db.session.commit()
        return (
            jsonify(
                {"message": f"Đã gỡ tag ID {tag_id} khỏi thẻ ID {card_id} thành công"}
            ),
            200,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi gỡ tag: {str(exc)}"}), 500


@cards_bp.route("/generate", methods=["POST"])
def generate_cards_from_doc_backward_compat():
    """
    Sinh flashcards tự động từ tài liệu qua AI Pipeline (POST /api/cards/generate)
    ---
    tags:
      - Cards & Tags
    summary: Tương thích ngược sinh thẻ tự động từ tài liệu
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - doc_id
          properties:
            doc_id:
              type: integer
              example: 1
            deck_id:
              type: integer
              example: 1
            user_id:
              type: integer
              example: 1
    responses:
      201:
        description: Sinh và lưu flashcards thành công
      400:
        description: Thiếu thông tin
      404:
        description: Không tìm thấy tài liệu
    """
    data = request.get_json(silent=True) or {}
    doc_id_raw = data.get("doc_id") or data.get("document_id")

    if doc_id_raw is None:
        return jsonify({"error": "Trường 'doc_id' là bắt buộc trong JSON body"}), 400

    try:
        doc_id = int(doc_id_raw)
    except (ValueError, TypeError):
        return jsonify({"error": "Trường 'doc_id' phải là số nguyên"}), 400

    document = db.session.get(Document, doc_id)
    if not document:
        return jsonify({"error": f"Không tìm thấy tài liệu với ID {doc_id}"}), 404

    user_id = data.get("user_id") or document.user_id
    deck_id = data.get("deck_id")
    if not deck_id:
        deck = Deck.query.filter_by(user_id=user_id).first()
        if not deck:
            deck = Deck(user_id=user_id, title=f"AI Deck - {document.filename}")
            db.session.add(deck)
            db.session.commit()
        deck_id = deck.id

    try:
        result = generate_cards_from_document_id(
            doc_id=doc_id, deck_id=deck_id, user_id=user_id
        )
        return jsonify(result), 201
    except Exception as exc:
        return jsonify({"error": f"Lỗi sinh thẻ AI: {str(exc)}"}), 500
