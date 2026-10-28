"""
crud_routes.py — CRUD endpoints for cards (Table 7: cards).
"""

from __future__ import annotations

from typing import Any
from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.flashcard import Card, Deck, card_tags


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
              example: "Là hàm bọc (wrapper) bổ sung hành vi cho hàm khác mà không sửa code gốc."
              description: Đáp án chính xác (mặt sau)
            explanation:
              type: string
              example: "Cú pháp @decorator là syntactic sugar."
              description: Giải thích hoặc ngữ cảnh bổ sung
            difficulty:
              type: string
              enum: [easy, medium, hard]
              default: medium
              example: medium
            document_id:
              type: integer
              example: 1
              description: ID tài liệu nguồn (nếu có)
    responses:
      201:
        description: Tạo flashcard thành công
      400:
        description: Thiếu dữ liệu bắt buộc
      404:
        description: Không tìm thấy bộ thẻ hoặc tài liệu nguồn
      500:
        description: Lỗi máy chủ
    """
    data: dict[str, Any] = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    answer = (data.get("answer") or "").strip()

    if not question or not answer:
        return jsonify({"error": "Trường 'question' và 'answer' là bắt buộc"}), 400

    deck_id = data.get("deck_id")
    if deck_id is not None:
        deck = db.session.get(Deck, int(deck_id))
        if not deck:
            return jsonify({"error": f"Không tìm thấy bộ thẻ ID {deck_id}"}), 404

    card = Card(
        deck_id=int(deck_id) if deck_id is not None else None,
        document_id=int(data["document_id"]) if data.get("document_id") else None,
        question=question,
        answer=answer,
        explanation=data.get("explanation"),
        difficulty=data.get("difficulty", "medium"),
        tts_text=data.get("tts_text") or question,
        tts_lang=data.get("tts_lang") or "en-US",
    )

    try:
        db.session.add(card)
        db.session.commit()
        return jsonify(card.to_dict()), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi tạo flashcard: {str(exc)}"}), 500


def get_card_detail(card_id: int):
    """
    Lấy chi tiết một flashcard (GET /api/cards/{card_id})
    ---
    tags:
      - Cards & Tags
    summary: Lấy chi tiết một flashcard theo ID
    parameters:
      - name: card_id
        in: path
        type: integer
        required: true
        description: ID thẻ
    responses:
      200:
        description: Thông tin chi tiết thẻ
      404:
        description: Không tìm thấy thẻ
    """
    card = db.session.get(Card, card_id)
    if not card:
        return jsonify({"error": f"Không tìm thấy thẻ với ID {card_id}"}), 404
    return jsonify(card.to_dict()), 200


def update_card_detail(card_id: int):
    """
    Cập nhật flashcard (PUT /api/cards/{card_id})
    ---
    tags:
      - Cards & Tags
    summary: Cập nhật thông tin flashcard
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
          properties:
            question:
              type: string
            answer:
              type: string
            explanation:
              type: string
            difficulty:
              type: string
              enum: [easy, medium, hard]
            deck_id:
              type: integer
    responses:
      200:
        description: Cập nhật thành công
      404:
        description: Không tìm thấy thẻ
      500:
        description: Lỗi máy chủ
    """
    card = db.session.get(Card, card_id)
    if not card:
        return jsonify({"error": f"Không tìm thấy thẻ với ID {card_id}"}), 404

    data = request.get_json(silent=True) or {}
    if "question" in data:
        card.question = str(data["question"]).strip()
    if "answer" in data:
        card.answer = str(data["answer"]).strip()
    if "explanation" in data:
        card.explanation = data["explanation"]
    if "difficulty" in data:
        card.difficulty = data["difficulty"]
    if "deck_id" in data:
        card.deck_id = int(data["deck_id"]) if data["deck_id"] is not None else None
    if "tts_text" in data:
        card.tts_text = data["tts_text"]
    if "tts_lang" in data:
        card.tts_lang = data["tts_lang"]

    try:
        db.session.commit()
        return jsonify(card.to_dict()), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi cập nhật thẻ: {str(exc)}"}), 500


def delete_card_endpoint(card_id: int):
    """
    Xóa một thẻ flashcard (DELETE /api/cards/{card_id})
    ---
    tags:
      - Cards & Tags
    summary: Xóa flashcard theo ID
    parameters:
      - name: card_id
        in: path
        type: integer
        required: true
        description: ID thẻ
    responses:
      200:
        description: Xóa thẻ thành công
      404:
        description: Không tìm thấy thẻ
      500:
        description: Lỗi xóa
    """
    card = db.session.get(Card, card_id)
    if not card:
        return jsonify({"error": f"Không tìm thấy thẻ với ID {card_id}"}), 404

    try:
        db.session.delete(card)
        db.session.commit()
        return jsonify({"message": f"Đã xóa thành công thẻ ID {card_id}"}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi xóa thẻ: {str(exc)}"}), 500


def delete_all_cards_endpoint():
    """
    Xóa toàn bộ flashcards (DELETE /api/cards?deck_id=X)
    ---
    tags:
      - Cards & Tags
    summary: Xóa toàn bộ thẻ flashcard (hoặc xóa toàn bộ thẻ thuộc về một deck_id)
    parameters:
      - name: deck_id
        in: query
        type: integer
        required: false
        description: ID bộ thẻ cần xóa sạch cards (nếu bỏ trống sẽ xóa tất cả)
    responses:
      200:
        description: Đã xóa thành công N thẻ
      500:
        description: Lỗi máy chủ
    """
    deck_id = request.args.get("deck_id", type=int)
    try:
        query = Card.query
        if deck_id is not None:
            query = query.filter_by(deck_id=deck_id)
        deleted_count = query.delete(synchronize_session=False)
        db.session.commit()
        return (
            jsonify(
                {
                    "message": f"Đã xóa thành công {deleted_count} thẻ flashcards",
                    "deleted_count": deleted_count,
                    "deck_id": deck_id,
                }
            ),
            200,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi xóa hàng loạt: {str(exc)}"}), 500


def register_crud_routes(bp: Blueprint) -> None:
    bp.add_url_rule("", view_func=get_all_cards, methods=["GET"])
    bp.add_url_rule("", view_func=create_new_card, methods=["POST"])
    bp.add_url_rule("/<int:card_id>", view_func=get_card_detail, methods=["GET"])
    bp.add_url_rule("/<int:card_id>", view_func=update_card_detail, methods=["PUT"])
    bp.add_url_rule(
        "/<int:card_id>", view_func=delete_card_endpoint, methods=["DELETE"]
    )
    bp.add_url_rule("", view_func=delete_all_cards_endpoint, methods=["DELETE"])
