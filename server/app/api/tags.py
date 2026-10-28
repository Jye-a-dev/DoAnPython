"""
tags.py — Tags CRUD API endpoints (Tag: Cards & Tags).
Quản lý thực thể: tags (Table 8) và card_tags (Table 9).
"""

from __future__ import annotations

from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.flashcard import Card, Tag, card_tags

tags_bp = Blueprint("tags", __name__, url_prefix="/api/tags")
card_tags_bp = Blueprint("card_tags", __name__, url_prefix="/api/card-tags")


@tags_bp.route("", methods=["GET"])
def list_tags():
    """
    Lấy danh sách các thẻ nhãn tags (GET /api/tags)
    ---
    tags:
      - Cards & Tags
    summary: Lấy danh sách tags (id, name, user_id)
    parameters:
      - name: user_id
        in: query
        type: integer
        required: false
        description: Lọc theo ID người dùng
    responses:
      200:
        description: Danh sách tags
      500:
        description: Lỗi truy vấn
    """
    user_id = request.args.get("user_id", type=int)
    query = Tag.query
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    tags = query.order_by(Tag.id.asc()).all()
    return jsonify([t.to_dict() for t in tags]), 200


@tags_bp.route("", methods=["POST"])
def create_tag():
    """
    Tạo tag mới (POST /api/tags)
    ---
    tags:
      - Cards & Tags
    summary: Tạo tag mới (user_id, name)
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
          properties:
            name:
              type: string
              example: "python"
              description: Tên tag
            user_id:
              type: integer
              example: 1
              description: ID người dùng tạo tag
    responses:
      201:
        description: Tạo tag thành công
      200:
        description: Tag đã tồn tại (trả về tag hiện hữu)
      400:
        description: Tên tag rỗng
      500:
        description: Lỗi máy chủ
    """
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    if not name or not str(name).strip():
        return jsonify({"error": "Trường 'name' là bắt buộc"}), 400

    cleaned_name = str(name).strip().lower()
    existing = Tag.query.filter_by(name=cleaned_name).first()
    if existing:
        return jsonify(existing.to_dict()), 200

    tag = Tag(name=cleaned_name, user_id=data.get("user_id"))
    try:
        db.session.add(tag)
        db.session.commit()
        return jsonify(tag.to_dict()), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi tạo tag: {str(exc)}"}), 500


@tags_bp.route("/<int:tag_id>", methods=["GET"])
def get_tag_by_id(tag_id: int):
    """
    Xem chi tiết một tag (GET /api/tags/{id})
    ---
    tags:
      - Cards & Tags
    summary: Xem chi tiết tag theo ID
    parameters:
      - name: tag_id
        in: path
        type: integer
        required: true
        description: ID của tag
    responses:
      200:
        description: Chi tiết tag
      404:
        description: Không tìm thấy tag
    """
    tag = db.session.get(Tag, tag_id)
    if not tag:
        return jsonify({"error": f"Không tìm thấy thẻ nhãn ID {tag_id}"}), 404
    return jsonify(tag.to_dict()), 200


@tags_bp.route("/<int:tag_id>", methods=["PUT"])
def update_tag_by_id(tag_id: int):
    """
    Cập nhật tên tag (PUT /api/tags/{id})
    ---
    tags:
      - Cards & Tags
    summary: Cập nhật tên tag
    parameters:
      - name: tag_id
        in: path
        type: integer
        required: true
        description: ID tag
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: "advanced-python"
    responses:
      200:
        description: Cập nhật thành công
      404:
        description: Không tìm thấy tag
      409:
        description: Tên tag mới đã bị trùng
    """
    tag = db.session.get(Tag, tag_id)
    if not tag:
        return jsonify({"error": f"Không tìm thấy thẻ nhãn ID {tag_id}"}), 404

    data = request.get_json(silent=True) or {}
    if "name" in data and str(data["name"]).strip():
        new_name = str(data["name"]).strip().lower()
        existing = Tag.query.filter(Tag.name == new_name, Tag.id != tag_id).first()
        if existing:
            return jsonify({"error": f"Tên tag '{new_name}' đã tồn tại"}), 409
        tag.name = new_name

    try:
        db.session.commit()
        return jsonify(tag.to_dict()), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi cập nhật tag: {str(exc)}"}), 500


@tags_bp.route("/<int:tag_id>", methods=["DELETE"])
def delete_tag_by_id(tag_id: int):
    """
    Xóa tag (DELETE /api/tags/{id})
    ---
    tags:
      - Cards & Tags
    summary: Xóa tag (tự động xóa liên kết trong card_tags theo ON DELETE CASCADE)
    parameters:
      - name: tag_id
        in: path
        type: integer
        required: true
        description: ID tag cần xóa
    responses:
      200:
        description: Đã xóa tag thành công
      404:
        description: Không tìm thấy tag
      500:
        description: Lỗi xóa tag
    """
    tag = db.session.get(Tag, tag_id)
    if not tag:
        return jsonify({"error": f"Không tìm thấy thẻ nhãn ID {tag_id}"}), 404

    try:
        db.session.delete(tag)
        db.session.commit()
        return jsonify({"message": f"Đã xóa thẻ nhãn ID {tag_id} thành công"}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi xóa tag: {str(exc)}"}), 500


# ==============================================================================
# Helper routes for card_tags (backward compatibility)
# ==============================================================================


@card_tags_bp.route("", methods=["GET"])
def list_card_tags():
    """Lấy danh sách ánh xạ M:N giữa Card và Tag"""
    card_id = request.args.get("card_id", type=int)
    tag_id = request.args.get("tag_id", type=int)
    query = db.session.query(card_tags)
    if card_id is not None:
        query = query.filter(card_tags.c.card_id == card_id)
    if tag_id is not None:
        query = query.filter(card_tags.c.tag_id == tag_id)
    rows = query.all()
    results = [
        {
            "card_id": r.card_id,
            "tag_id": r.tag_id,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]
    return jsonify(results), 200


@card_tags_bp.route("", methods=["POST"])
def attach_card_tag_legacy():
    """Gán nhãn (Tag) cho một flashcard (Card)"""
    data = request.get_json(silent=True) or {}
    card_id = data.get("card_id")
    tag_id = data.get("tag_id")
    if not card_id or not tag_id:
        return jsonify({"error": "Trường 'card_id' và 'tag_id' là bắt buộc"}), 400
    card = db.session.get(Card, card_id)
    tag = db.session.get(Tag, tag_id)
    if not card or not tag:
        return jsonify({"error": "Không tìm thấy Card hoặc Tag tương ứng"}), 404
    existing = (
        db.session.query(card_tags).filter_by(card_id=card_id, tag_id=tag_id).first()
    )
    if not existing:
        stmt = card_tags.insert().values(
            card_id=card_id,
            tag_id=tag_id,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        db.session.execute(stmt)
        db.session.commit()
    return (
        jsonify(
            {
                "card_id": card_id,
                "tag_id": tag_id,
                "message": "Gán nhãn cho thẻ thành công",
            }
        ),
        201,
    )
