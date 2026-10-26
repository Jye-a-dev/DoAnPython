from flask import Blueprint, jsonify, request
from typing import Any, List
from app.core.database import db
from app.models.document import Document
from app.models.flashcard import Deck, Card, Tag
from app.services.ai_service import generate_cards_from_document_id
from app.services.flashcard_service import (
    create_card,
    get_card_by_id,
    list_cards,
    update_card,
    delete_card,
    delete_all_cards,
)
from app.validators.card_validator import validate_card_payload

cards_bp = Blueprint("cards", __name__, url_prefix="/api/cards")


@cards_bp.route("/generate", methods=["POST"])
def generate_cards_from_doc_endpoint():
    """
    Sinh flashcards tự động từ tài liệu (doc_id) qua AI Pipeline
    ---
    tags:
      - Cards
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
        description: Dữ liệu không hợp lệ
      404:
        description: Không tìm thấy tài liệu
      500:
        description: Lỗi AI inference
    """
    data = request.get_json(silent=True) or {}
    doc_id_raw = data.get("doc_id") or data.get("document_id")

    if doc_id_raw is None:
        return jsonify({"error": "Trường 'doc_id' là bắt buộc trong JSON body"}), 400

    try:
        doc_id = int(doc_id_raw)
        if doc_id <= 0:
            return jsonify({"error": "Trường 'doc_id' phải là số nguyên dương"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Trường 'doc_id' phải là số nguyên"}), 400

    document = db.session.get(Document, doc_id)
    if not document:
        return jsonify({"error": f"Không tìm thấy tài liệu với ID {doc_id}"}), 404

    user_id_raw = data.get("user_id")
    if user_id_raw is not None:
        try:
            user_id = int(user_id_raw)
        except (ValueError, TypeError):
            return jsonify({"error": "Trường 'user_id' phải là số nguyên"}), 400
    else:
        user_id = document.user_id

    deck_id_raw = data.get("deck_id")
    if deck_id_raw is not None:
        try:
            deck_id = int(deck_id_raw)
        except (ValueError, TypeError):
            return jsonify({"error": "Trường 'deck_id' phải là số nguyên"}), 400
    else:
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
    except ValueError as val_err:
        return jsonify({"error": str(val_err)}), 400
    except Exception as exc:
        return jsonify({"error": f"Lỗi sinh thẻ AI: {str(exc)}"}), 500


@cards_bp.route("", methods=["GET"])
def get_all_cards():
    """
    Lấy danh sách các flashcards
    ---
    tags:
      - Cards
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
    responses:
      200:
        description: Danh sách flashcards thành công
    """
    deck_id_raw = request.args.get("deck_id")
    document_id_raw = request.args.get("document_id")

    deck_id = int(deck_id_raw) if deck_id_raw and deck_id_raw.isdigit() else None
    document_id = (
        int(document_id_raw) if document_id_raw and document_id_raw.isdigit() else None
    )

    cards = list_cards(deck_id=deck_id, document_id=document_id)
    return jsonify([c.to_dict() for c in cards]), 200


@cards_bp.route("", methods=["POST"])
def create_new_card():
    """
    Tạo mới một flashcard
    ---
    tags:
      - Cards
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
            question:
              type: string
              example: "Tuple trong Python có bất biến không?"
            answer:
              type: string
              example: "Có"
            explanation:
              type: string
              example: "Tuple không thể thay đổi phần tử sau khi khởi tạo"
            difficulty:
              type: string
              example: "medium"
            deck_id:
              type: integer
              example: 1
            tags:
              type: array
              items:
                type: string
              example: ["python", "data-types"]
    responses:
      201:
        description: Tạo flashcard thành công
      400:
        description: Câu hỏi hoặc câu trả lời rỗng hoặc không hợp lệ
    """
    data = request.get_json(silent=True) or {}
    is_valid, error_msg, cleaned_data = validate_card_payload(data, is_update=False)
    if not is_valid or cleaned_data is None:
        return jsonify({"error": error_msg}), 400

    try:
        card = create_card(cleaned_data)
        card_dict = card.to_dict()
        card_dict["message"] = "Tạo flashcard thành công"
        card_dict["card"] = card.to_dict()
        return jsonify(card_dict), 201
    except Exception as exc:
        return jsonify({"error": f"Lỗi tạo flashcard: {str(exc)}"}), 500


@cards_bp.route("/<int:card_id>", methods=["GET"])
def get_card_detail(card_id: int):
    """Lấy chi tiết một thẻ theo ID"""
    card = get_card_by_id(card_id)
    if not card:
        return jsonify({"error": f"Không tìm thấy flashcard với ID {card_id}"}), 404
    return jsonify(card.to_dict()), 200


@cards_bp.route("/<int:card_id>", methods=["PUT"])
def update_card_detail(card_id: int):
    """Cập nhật nội dung flashcard"""
    data = request.get_json(silent=True) or {}
    is_valid, error_msg, cleaned_data = validate_card_payload(data, is_update=True)
    if not is_valid or cleaned_data is None:
        return jsonify({"error": error_msg}), 400

    card = update_card(card_id, cleaned_data)
    if not card:
        return jsonify({"error": f"Không tìm thấy flashcard với ID {card_id}"}), 404

    card_dict = card.to_dict()
    card_dict["message"] = "Cập nhật flashcard thành công"
    card_dict["card"] = card.to_dict()
    return jsonify(card_dict), 200


@cards_bp.route("/<int:card_id>", methods=["DELETE"])
def delete_card_endpoint(card_id: int):
    """Xóa flashcard theo ID"""
    success = delete_card(card_id)
    if not success:
        return jsonify({"error": f"Không tìm thấy flashcard với ID {card_id}"}), 404
    return jsonify({"message": f"Đã xóa flashcard ID {card_id} thành công"}), 200


@cards_bp.route("", methods=["DELETE"])
def delete_all_cards_endpoint():
    """Xóa toàn bộ flashcards (hoặc lọc theo query param deck_id)"""
    deck_id_raw = request.args.get("deck_id")
    deck_id = int(deck_id_raw) if deck_id_raw and deck_id_raw.isdigit() else None
    count = delete_all_cards(deck_id=deck_id)
    return (
        jsonify(
            {
                "message": "Đã xóa toàn bộ flashcards thành công",
                "deleted_count": count,
            }
        ),
        200,
    )


@cards_bp.route("/<int:card_id>/tags", methods=["GET"])
def get_card_tags_endpoint(card_id: int):
    """Lấy danh sách các thẻ nhãn của một flashcard"""
    card = db.session.get(Card, card_id)
    if not card:
        return jsonify({"error": f"Không tìm thấy thẻ ID {card_id}"}), 404
    card_tags_list: Any = getattr(card, "tags", [])
    return jsonify([t.to_dict() for t in card_tags_list]), 200


@cards_bp.route("/<int:card_id>/tags/<int:tag_id>", methods=["POST"])
def attach_tag_to_card_endpoint(card_id: int, tag_id: int):
    """Gán trực tiếp nhãn tag_id cho card_id"""
    card = db.session.get(Card, card_id)
    tag = db.session.get(Tag, tag_id)
    if not card or not tag:
        return jsonify({"error": "Không tìm thấy Card hoặc Tag"}), 404
    card_tags_list: Any = getattr(card, "tags", [])
    if tag not in card_tags_list:
        card_tags_list.append(tag)
        db.session.commit()
    return (
        jsonify(
            {
                "message": "Gán nhãn thành công",
                "tags": [t.to_dict() for t in card_tags_list],
            }
        ),
        200,
    )


@cards_bp.route("/<int:card_id>/tags/<int:tag_id>", methods=["DELETE"])
def detach_tag_from_card_endpoint(card_id: int, tag_id: int):
    """Gỡ nhãn tag_id khỏi card_id"""
    card = db.session.get(Card, card_id)
    tag = db.session.get(Tag, tag_id)
    if not card or not tag:
        return jsonify({"error": "Không tìm thấy Card hoặc Tag"}), 404
    card_tags_list: Any = getattr(card, "tags", [])
    if tag in card_tags_list:
        card_tags_list.remove(tag)
        db.session.commit()
    return (
        jsonify(
            {
                "message": "Gỡ nhãn thành công",
                "tags": [t.to_dict() for t in card_tags_list],
            }
        ),
        200,
    )

