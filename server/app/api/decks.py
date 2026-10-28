"""
decks.py — Decks CRUD API endpoints (Tag: Decks).
Quản lý thực thể: decks (Table 6).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.flashcard import Deck

decks_bp = Blueprint("decks", __name__, url_prefix="/api/decks")


@decks_bp.route("", methods=["GET"])
def get_all_decks():
    """
    Lấy danh sách các bộ thẻ (GET /api/decks)
    ---
    tags:
      - Decks
    summary: Danh sách bộ thẻ (lọc theo ?user_id=, ?folder_id=, ?category_id=, ?is_public=) kèm tổng số card
    parameters:
      - name: user_id
        in: query
        type: integer
        required: false
        description: Lọc theo ID người dùng
      - name: folder_id
        in: query
        type: integer
        required: false
        description: Lọc theo thư mục
      - name: category_id
        in: query
        type: integer
        required: false
        description: Lọc theo danh mục
      - name: is_public
        in: query
        type: boolean
        required: false
        description: Lọc theo trạng thái công khai (true/false)
    responses:
      200:
        description: Danh sách bộ thẻ kèm card_count
      500:
        description: Lỗi truy vấn
    """
    user_id = request.args.get("user_id", type=int)
    folder_id = request.args.get("folder_id", type=int)
    category_id = request.args.get("category_id", type=int)
    is_public_raw = request.args.get("is_public")

    query = Deck.query
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    if folder_id is not None:
        query = query.filter_by(folder_id=folder_id)
    if category_id is not None:
        query = query.filter_by(category_id=category_id)
    if is_public_raw is not None:
        is_pub = is_public_raw.lower() in ["true", "1", "yes"]
        query = query.filter_by(is_public=is_pub)

    decks = query.order_by(Deck.created_at.desc()).all()
    return jsonify([d.to_dict() for d in decks]), 200


@decks_bp.route("", methods=["POST"])
def create_new_deck():
    """
    Tạo mới bộ thẻ (POST /api/decks)
    ---
    tags:
      - Decks
    summary: Tạo bộ thẻ mới (user_id, title, description, folder_id, category_id, is_public)
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - user_id
            - title
          properties:
            user_id:
              type: integer
              example: 1
              description: ID người dùng sở hữu bộ thẻ
            title:
              type: string
              example: "Lập trình Python Toàn Diện"
              description: Tiêu đề bộ thẻ
            description:
              type: string
              example: "Bộ thẻ bao gồm cú pháp, OOP và mẹo tối ưu trong Python"
              description: Mô tả chi tiết
            folder_id:
              type: integer
              example: 1
              description: ID thư mục chứa bộ thẻ
            category_id:
              type: integer
              example: 1
              description: ID danh mục
            is_public:
              type: boolean
              default: false
              example: false
              description: Đánh dấu công khai bộ thẻ
    responses:
      201:
        description: Tạo bộ thẻ thành công
      400:
        description: Tiêu đề hoặc user_id không hợp lệ
      500:
        description: Lỗi máy chủ
    """
    data = request.get_json(silent=True) or {}
    title = data.get("title")
    user_id = data.get("user_id")

    if not title or not str(title).strip():
        return jsonify({"error": "Trường 'title' là bắt buộc và không được rỗng"}), 400
    if not user_id:
        return jsonify({"error": "Trường 'user_id' là bắt buộc"}), 400

    deck = Deck(
        user_id=int(user_id),
        title=str(title).strip(),
        description=data.get("description"),
        folder_id=data.get("folder_id"),
        category_id=data.get("category_id"),
        is_public=bool(data.get("is_public", False)),
    )
    try:
        db.session.add(deck)
        db.session.commit()
        deck_dict = deck.to_dict()
        deck_dict["message"] = "Tạo bộ thẻ thành công"
        return jsonify(deck_dict), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi tạo bộ thẻ: {str(exc)}"}), 500


@decks_bp.route("/<int:deck_id>", methods=["GET"])
def get_deck_detail(deck_id: int):
    """
    Xem chi tiết bộ thẻ kèm danh sách thẻ bên trong (GET /api/decks/{id})
    ---
    tags:
      - Decks
    summary: Chi tiết bộ thẻ kèm danh sách thẻ con bên trong
    parameters:
      - name: deck_id
        in: path
        type: integer
        required: true
        description: ID bộ thẻ
    responses:
      200:
        description: Chi tiết bộ thẻ kèm danh sách thẻ con
      404:
        description: Không tìm thấy bộ thẻ
    """
    deck = db.session.get(Deck, deck_id)
    if not deck:
        return jsonify({"error": f"Không tìm thấy bộ thẻ với ID {deck_id}"}), 404

    deck_dict = deck.to_dict()
    deck_cards: Any = getattr(deck, "cards", [])
    deck_dict["cards"] = [c.to_dict() for c in deck_cards] if deck_cards else []
    return jsonify(deck_dict), 200


@decks_bp.route("/<int:deck_id>", methods=["PUT"])
def update_deck_detail(deck_id: int):
    """
    Cập nhật thông tin bộ thẻ (PUT /api/decks/{id})
    ---
    tags:
      - Decks
    summary: Cập nhật tiêu đề, mô tả, thư mục chuyển đến hoặc cờ công khai
    parameters:
      - name: deck_id
        in: path
        type: integer
        required: true
        description: ID bộ thẻ
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
              example: "Lập trình Python Cập Nhật"
            description:
              type: string
              example: "Nội dung ôn tập cập nhật"
            folder_id:
              type: integer
              example: 2
            category_id:
              type: integer
              example: 1
            is_public:
              type: boolean
              example: true
    responses:
      200:
        description: Cập nhật bộ thẻ thành công
      404:
        description: Không tìm thấy bộ thẻ
      500:
        description: Lỗi máy chủ
    """
    deck = db.session.get(Deck, deck_id)
    if not deck:
        return jsonify({"error": f"Không tìm thấy bộ thẻ với ID {deck_id}"}), 404

    data = request.get_json(silent=True) or {}
    if "title" in data and str(data["title"]).strip():
        deck.title = str(data["title"]).strip()
    if "description" in data:
        deck.description = data["description"]
    if "folder_id" in data:
        deck.folder_id = data["folder_id"]
    if "category_id" in data:
        deck.category_id = data["category_id"]
    if "is_public" in data:
        deck.is_public = bool(data["is_public"])

    deck.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

    try:
        db.session.commit()
        deck_dict = deck.to_dict()
        deck_dict["message"] = "Cập nhật bộ thẻ thành công"
        return jsonify(deck_dict), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi cập nhật bộ thẻ: {str(exc)}"}), 500


@decks_bp.route("/<int:deck_id>", methods=["DELETE"])
def delete_deck_endpoint(deck_id: int):
    """
    Xóa bộ thẻ kích hoạt ON DELETE CASCADE (DELETE /api/decks/{id})
    ---
    tags:
      - Decks
    summary: Xóa bộ thẻ (xóa toàn bộ thẻ thuộc deck theo ON DELETE CASCADE)
    parameters:
      - name: deck_id
        in: path
        type: integer
        required: true
        description: ID bộ thẻ cần xóa
    responses:
      200:
        description: Đã xóa bộ thẻ thành công
      404:
        description: Không tìm thấy bộ thẻ
      500:
        description: Lỗi xóa bộ thẻ
    """
    deck = db.session.get(Deck, deck_id)
    if not deck:
        return jsonify({"error": f"Không tìm thấy bộ thẻ với ID {deck_id}"}), 404

    try:
        db.session.delete(deck)
        db.session.commit()
        return (
            jsonify(
                {
                    "message": f"Đã xóa bộ thẻ ID {deck_id} và toàn bộ thẻ bên trong thành công"
                }
            ),
            200,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi xóa bộ thẻ: {str(exc)}"}), 500
