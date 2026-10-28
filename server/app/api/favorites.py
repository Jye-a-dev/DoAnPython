"""
favorites.py — User Favorites CRUD API endpoints (Tag: User Favorites).
Quản lý thực thể: user_favorites (Table 13).
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.study import UserFavorite

favorites_bp = Blueprint("favorites", __name__, url_prefix="/api/favorites")


@favorites_bp.route("", methods=["GET"])
def list_favorites():
    """
    Lấy danh sách mục yêu thích của người dùng (GET /api/favorites)
    ---
    tags:
      - User Favorites
    summary: Lấy danh sách yêu thích (?user_id=, hỗ trợ lọc theo deck_id hoặc card_id)
    parameters:
      - name: user_id
        in: query
        type: integer
        required: false
        description: ID người dùng
      - name: deck_id
        in: query
        type: integer
        required: false
        description: Lọc theo ID bộ thẻ yêu thích
      - name: card_id
        in: query
        type: integer
        required: false
        description: Lọc theo ID thẻ yêu thích
    responses:
      200:
        description: Danh sách các mục yêu thích
      500:
        description: Lỗi máy chủ
    """
    user_id = request.args.get("user_id", type=int)
    deck_id = request.args.get("deck_id", type=int)
    card_id = request.args.get("card_id", type=int)

    query = UserFavorite.query
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    if deck_id is not None:
        query = query.filter_by(deck_id=deck_id)
    if card_id is not None:
        query = query.filter_by(card_id=card_id)

    favorites = query.order_by(UserFavorite.id.desc()).all()
    return jsonify([f.to_dict() for f in favorites]), 200


@favorites_bp.route("", methods=["POST"])
def add_favorite():
    """
    Thêm Deck hoặc Card vào danh sách yêu thích (POST /api/favorites)
    ---
    tags:
      - User Favorites
    summary: Thêm Deck hoặc Card vào yêu thích (xử lý ràng buộc UNIQUE không lưu trùng)
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - user_id
          properties:
            user_id:
              type: integer
              example: 1
              description: ID người dùng
            deck_id:
              type: integer
              example: 1
              description: ID bộ thẻ yêu thích (tùy chọn nếu lưu card_id)
            card_id:
              type: integer
              example: 1
              description: ID thẻ yêu thích (tùy chọn nếu lưu deck_id)
    responses:
      201:
        description: Đã thêm vào yêu thích thành công
      400:
        description: Thiếu thông tin user_id hoặc không có deck_id/card_id
      409:
        description: Mục này đã tồn tại trong danh sách yêu thích của người dùng
      500:
        description: Lỗi máy chủ
    """
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    deck_id = data.get("deck_id")
    card_id = data.get("card_id")

    if not user_id:
        return jsonify({"error": "Trường 'user_id' là bắt buộc"}), 400
    if not deck_id and not card_id:
        return jsonify({"error": "Phải cung cấp ít nhất 'deck_id' hoặc 'card_id'"}), 400

    try:
        user_id = int(user_id)
        deck_id = int(deck_id) if deck_id else None
        card_id = int(card_id) if card_id else None
    except (ValueError, TypeError):
        return jsonify({"error": "Các trường ID phải là số nguyên"}), 400

    # Kiểm tra ràng buộc UNIQUE không lưu trùng
    query = UserFavorite.query.filter_by(user_id=user_id)
    if card_id is not None:
        query = query.filter_by(card_id=card_id)
    elif deck_id is not None:
        query = query.filter_by(deck_id=deck_id, card_id=None)

    existing = query.first()
    if existing:
        return (
            jsonify(
                {
                    "error": "Mục này đã tồn tại trong danh sách yêu thích",
                    "favorite_id": existing.id,
                    "favorite": existing.to_dict(),
                }
            ),
            409,
        )

    fav = UserFavorite(user_id=user_id, deck_id=deck_id, card_id=card_id)
    try:
        db.session.add(fav)
        db.session.commit()
        return jsonify(fav.to_dict()), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi lưu mục yêu thích: {str(exc)}"}), 500


@favorites_bp.route("/<int:fav_id>", methods=["GET"])
def get_favorite_by_id(fav_id: int):
    """
    Xem chi tiết mục yêu thích (GET /api/favorites/{id})
    ---
    tags:
      - User Favorites
    summary: Xem chi tiết một bản ghi yêu thích theo ID
    parameters:
      - name: fav_id
        in: path
        type: integer
        required: true
        description: ID mục yêu thích
    responses:
      200:
        description: Chi tiết mục yêu thích
      404:
        description: Không tìm thấy mục yêu thích
    """
    fav = db.session.get(UserFavorite, fav_id)
    if not fav:
        return jsonify({"error": f"Không tìm thấy mục yêu thích ID {fav_id}"}), 404
    return jsonify(fav.to_dict()), 200


@favorites_bp.route("/<int:fav_id>", methods=["DELETE"])
def delete_favorite_by_id(fav_id: int):
    """
    Xóa mục yêu thích theo ID (DELETE /api/favorites/{id})
    ---
    tags:
      - User Favorites
    summary: Xóa một bản ghi yêu thích theo ID
    parameters:
      - name: fav_id
        in: path
        type: integer
        required: true
        description: ID bản ghi yêu thích cần xóa
    responses:
      200:
        description: Đã xóa mục yêu thích thành công
      404:
        description: Không tìm thấy mục yêu thích
      500:
        description: Lỗi xóa
    """
    fav = db.session.get(UserFavorite, fav_id)
    if not fav:
        return jsonify({"error": f"Không tìm thấy mục yêu thích ID {fav_id}"}), 404

    try:
        db.session.delete(fav)
        db.session.commit()
        return jsonify({"message": f"Đã xóa mục yêu thích ID {fav_id} thành công"}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi xóa mục yêu thích: {str(exc)}"}), 500


@favorites_bp.route("/card", methods=["DELETE"])
def delete_favorite_card():
    """
    Bỏ yêu thích nhanh thẻ flashcard (DELETE /api/favorites/card)
    ---
    tags:
      - User Favorites
    summary: Bỏ yêu thích nhanh qua user_id và card_id
    parameters:
      - name: user_id
        in: query
        type: integer
        required: false
        description: ID người dùng (có thể gửi qua query param hoặc body)
      - name: card_id
        in: query
        type: integer
        required: false
        description: ID thẻ cần bỏ yêu thích (có thể gửi qua query param hoặc body)
      - name: body
        in: body
        required: false
        schema:
          type: object
          properties:
            user_id:
              type: integer
              example: 1
            card_id:
              type: integer
              example: 1
    responses:
      200:
        description: Đã bỏ yêu thích thẻ thành công
      400:
        description: Thiếu user_id hoặc card_id
      404:
        description: Không tìm thấy bản ghi yêu thích tương ứng
      500:
        description: Lỗi máy chủ
    """
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id") or request.args.get("user_id", type=int)
    card_id = data.get("card_id") or request.args.get("card_id", type=int)

    if not user_id or not card_id:
        return jsonify({"error": "Trường 'user_id' và 'card_id' là bắt buộc"}), 400

    try:
        user_id = int(user_id)
        card_id = int(card_id)
    except (ValueError, TypeError):
        return jsonify({"error": "user_id và card_id phải là số nguyên"}), 400

    fav = UserFavorite.query.filter_by(user_id=user_id, card_id=card_id).first()
    if not fav:
        return (
            jsonify(
                {
                    "error": f"Không tìm thấy thẻ {card_id} trong danh sách yêu thích của user {user_id}"
                }
            ),
            404,
        )

    try:
        db.session.delete(fav)
        db.session.commit()
        return (
            jsonify({"message": f"Đã bỏ yêu thích thẻ ID {card_id} thành công"}),
            200,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi bỏ yêu thích: {str(exc)}"}), 500
