"""
generator_routes.py — Legacy card generator endpoint (POST /api/cards/generate).
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.document import Document
from app.models.flashcard import Deck
from app.services.ai_service import generate_cards_from_document_id


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
            doc_id=doc_id, deck_id=deck_id, user_id=user_id, persist_to_db=True
        )
        return jsonify(result), 201
    except Exception as exc:
        return jsonify({"error": f"Lỗi sinh thẻ AI: {str(exc)}"}), 500


def register_generator_routes(bp: Blueprint) -> None:
    bp.add_url_rule(
        "/generate", view_func=generate_cards_from_doc_backward_compat, methods=["POST"]
    )
