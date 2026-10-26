"""
tags.py — Tags & Card Tags M:N CRUD API endpoints (Tables 8 & 9).
"""

from __future__ import annotations

from datetime import datetime
from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.flashcard import Card, Tag, card_tags

tags_bp = Blueprint("tags", __name__, url_prefix="/api/tags")
card_tags_bp = Blueprint("card_tags", __name__, url_prefix="/api/card-tags")


@tags_bp.route("", methods=["GET"])
def list_tags():
    """Lấy danh sách các thẻ nhãn (Tags)"""
    user_id = request.args.get("user_id", type=int)
    query = Tag.query
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    tags = query.order_by(Tag.id.asc()).all()
    return jsonify([t.to_dict() for t in tags]), 200


@tags_bp.route("", methods=["POST"])
def create_tag():
    """Tạo mới thẻ nhãn (Tag)"""
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    if not name or not str(name).strip():
        return jsonify({"error": "Trường 'name' là bắt buộc"}), 400
    cleaned_name = str(name).strip()
    existing = Tag.query.filter_by(name=cleaned_name).first()
    if existing:
        return jsonify(existing.to_dict()), 200
    tag = Tag(name=cleaned_name, user_id=data.get("user_id"))
    db.session.add(tag)
    db.session.commit()
    return jsonify(tag.to_dict()), 201


@tags_bp.route("/<int:tag_id>", methods=["GET"])
def get_tag_by_id(tag_id: int):
    """Lấy chi tiết một thẻ nhãn"""
    tag = db.session.get(Tag, tag_id)
    if not tag:
        return jsonify({"error": f"Không tìm thấy thẻ nhãn ID {tag_id}"}), 404
    return jsonify(tag.to_dict()), 200


@tags_bp.route("/<int:tag_id>", methods=["PUT"])
def update_tag_by_id(tag_id: int):
    """Cập nhật tên thẻ nhãn"""
    tag = db.session.get(Tag, tag_id)
    if not tag:
        return jsonify({"error": f"Không tìm thấy thẻ nhãn ID {tag_id}"}), 404
    data = request.get_json(silent=True) or {}
    if "name" in data and str(data["name"]).strip():
        tag.name = str(data["name"]).strip()
    db.session.commit()
    return jsonify(tag.to_dict()), 200


@tags_bp.route("/<int:tag_id>", methods=["DELETE"])
def delete_tag_by_id(tag_id: int):
    """Xóa thẻ nhãn"""
    tag = db.session.get(Tag, tag_id)
    if not tag:
        return jsonify({"error": f"Không tìm thấy thẻ nhãn ID {tag_id}"}), 404
    db.session.delete(tag)
    db.session.commit()
    return jsonify({"message": f"Đã xóa thẻ nhãn ID {tag_id} thành công"}), 200


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
def attach_card_tag():
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
            card_id=card_id, tag_id=tag_id, created_at=datetime.utcnow()
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


@card_tags_bp.route("/<int:card_id>/<int:tag_id>", methods=["GET"])
def get_card_tag_relation(card_id: int, tag_id: int):
    """Kiểm tra quan hệ gán nhãn giữa Card và Tag"""
    existing = (
        db.session.query(card_tags).filter_by(card_id=card_id, tag_id=tag_id).first()
    )
    if not existing:
        return jsonify({"error": "Quan hệ Card-Tag không tồn tại"}), 404
    return jsonify({"card_id": card_id, "tag_id": tag_id, "attached": True}), 200


@card_tags_bp.route("/<int:card_id>/<int:tag_id>", methods=["DELETE"])
def detach_card_tag(card_id: int, tag_id: int):
    """Gỡ thẻ nhãn khỏi một flashcard"""
    stmt = card_tags.delete().where(
        card_tags.c.card_id == card_id, card_tags.c.tag_id == tag_id
    )
    db.session.execute(stmt)
    db.session.commit()
    return jsonify({"message": f"Đã gỡ nhãn {tag_id} khỏi thẻ {card_id}"}), 200
