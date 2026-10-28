"""
tag_routes.py — Card-Tag association endpoints (POST / DELETE /api/cards/<id>/tags).
"""

from __future__ import annotations

from datetime import datetime, timezone
from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.flashcard import Card, Tag, card_tags


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


def register_tag_routes(bp: Blueprint) -> None:
    bp.add_url_rule("/<int:card_id>/tags", view_func=attach_tag_to_card, methods=["POST"])
    bp.add_url_rule("/<int:card_id>/tags/<int:tag_id>", view_func=detach_tag_from_card, methods=["DELETE"])

