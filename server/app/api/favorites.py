"""
favorites.py — User Favorites CRUD API endpoints (Table 13: user_favorites).
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.study import UserFavorite

favorites_bp = Blueprint("favorites", __name__, url_prefix="/api/favorites")


@favorites_bp.route("", methods=["GET"])
def list_favorites():
    """Lấy danh sách mục yêu thích (Decks/Cards) của người dùng"""
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
    """Thêm một bộ thẻ hoặc flashcard vào danh sách yêu thích"""
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    deck_id = data.get("deck_id")
    card_id = data.get("card_id")
    if not user_id:
        return jsonify({"error": "Trường 'user_id' là bắt buộc"}), 400
    if not deck_id and not card_id:
        return jsonify({"error": "Phải cung cấp ít nhất 'deck_id' hoặc 'card_id'"}), 400
    query = UserFavorite.query.filter_by(user_id=user_id)
    if card_id is not None:
        query = query.filter_by(card_id=card_id)
    elif deck_id is not None:
        query = query.filter_by(deck_id=deck_id)
    fav = query.first()
    if not fav:
        fav = UserFavorite(user_id=user_id, deck_id=deck_id, card_id=card_id)
        db.session.add(fav)
        db.session.commit()
    return jsonify(fav.to_dict()), 201


@favorites_bp.route("/<int:fav_id>", methods=["GET"])
def get_favorite_by_id(fav_id: int):
    """Lấy chi tiết một mục yêu thích"""
    fav = db.session.get(UserFavorite, fav_id)
    if not fav:
        return jsonify({"error": f"Không tìm thấy mục yêu thích ID {fav_id}"}), 404
    return jsonify(fav.to_dict()), 200


@favorites_bp.route("/<int:fav_id>", methods=["DELETE"])
def delete_favorite_by_id(fav_id: int):
    """Xóa một mục khỏi danh sách yêu thích"""
    fav = db.session.get(UserFavorite, fav_id)
    if not fav:
        return jsonify({"error": f"Không tìm thấy mục yêu thích ID {fav_id}"}), 404
    db.session.delete(fav)
    db.session.commit()
    return jsonify({"message": f"Đã xóa mục yêu thích ID {fav_id} thành công"}), 200
