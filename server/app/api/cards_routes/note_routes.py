"""
note_routes.py — Endpoint cập nhật ghi chú cá nhân trên thẻ (Personal Notes / Side Annotation).
PATCH /api/cards/<card_id>/notes
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.flashcard import Card


def update_card_notes(card_id: int):
    """
    Cập nhật ghi chú cá nhân (Personal Notes) cho flashcard mà không ảnh hưởng nội dung gốc
    ---
    tags:
      - Cards & Tags
    summary: Cập nhật ghi chú cá nhân / mẹo nhớ riêng cho thẻ
    parameters:
      - name: card_id
        in: path
        type: integer
        required: true
        description: ID thẻ cần ghi chú
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            personal_notes:
              type: string
              example: "Mẹo nhớ: Tế bào ti thể như nhà máy phát điện của thành phố"
    responses:
      200:
        description: Cập nhật ghi chú thành công
      404:
        description: Không tìm thấy thẻ
      500:
        description: Lỗi máy chủ
    """
    card = db.session.get(Card, card_id)
    if not card:
        return jsonify({"error": f"Không tìm thấy thẻ với ID {card_id}"}), 404

    data = request.get_json(silent=True) or {}
    raw_notes = data.get("personal_notes")
    if raw_notes is None and "notes" in data:
        raw_notes = data.get("notes")

    card.personal_notes = str(raw_notes).strip() if raw_notes is not None else None

    try:
        db.session.commit()
        return jsonify({
            "message": "Cập nhật ghi chú cá nhân thành công",
            "card_id": card_id,
            "personal_notes": card.personal_notes,
            "card": card.to_dict(),
        }), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi cập nhật ghi chú: {str(exc)}"}), 500


def register_note_routes(bp: Blueprint) -> None:
    bp.add_url_rule("/<int:card_id>/notes", view_func=update_card_notes, methods=["PATCH", "PUT", "POST"])

