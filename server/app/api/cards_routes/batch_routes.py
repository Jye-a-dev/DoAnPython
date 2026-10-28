"""
batch_routes.py — Batch card creation endpoint (POST /api/cards/batch).
"""

from __future__ import annotations

from typing import Any
from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.flashcard import Card, Deck, Tag


def create_cards_batch():
    """
    Lưu hàng loạt flashcards đã được người dùng lọc/chọn (POST /api/cards/batch)
    ---
    tags:
      - Cards & Tags
    summary: Batch insert nhiều thẻ đã qua Preview Checklist vào một Deck trong một transaction
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - deck_id
            - cards
          properties:
            deck_id:
              type: integer
              example: 1
              description: ID bộ thẻ đích (bắt buộc)
            document_id:
              type: integer
              example: null
              description: ID tài liệu nguồn (tùy chọn)
            cards:
              type: array
              description: Danh sách thẻ đã lọc cần lưu
              items:
                type: object
                required:
                  - question
                  - answer
                properties:
                  question:
                    type: string
                    example: "What is Mitochondria?"
                  answer:
                    type: string
                    example: "Powerhouse of the cell"
                  explanation:
                    type: string
                    example: "Produces ATP"
                  difficulty:
                    type: string
                    default: medium
                    example: medium
                  tts_text:
                    type: string
                    example: "Mitochondria"
                  tts_lang:
                    type: string
                    default: en-US
                    example: en-US
                  tags:
                    type: array
                    items:
                      type: string
                    example: ["Biology", "Cell"]
    responses:
      201:
        description: Đã lưu thành công N thẻ
      400:
        description: deck_id không hợp lệ hoặc mảng cards rỗng
      404:
        description: Không tìm thấy Deck
      500:
        description: Lỗi máy chủ khi lưu hàng loạt
    """
    data = request.get_json(silent=True) or {}

    deck_id_raw = data.get("deck_id")
    if deck_id_raw is None:
        return jsonify({"error": "Trường 'deck_id' là bắt buộc trong JSON body"}), 400
    try:
        deck_id = int(deck_id_raw)
        if deck_id <= 0:
            return jsonify({"error": "Trường 'deck_id' phải là số nguyên dương"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Trường 'deck_id' phải là số nguyên"}), 400

    deck = db.session.get(Deck, deck_id)
    if not deck:
        return jsonify({"error": f"Không tìm thấy bộ thẻ Deck với ID {deck_id}"}), 404

    cards_input = data.get("cards")
    if not cards_input or not isinstance(cards_input, list):
        return jsonify({"error": "Mảng 'cards' không được để trống"}), 400

    document_id_raw = data.get("document_id")
    document_id: int | None = None
    if document_id_raw is not None:
        try:
            document_id = int(document_id_raw)
        except (ValueError, TypeError):
            document_id = None

    valid_cards: list[Card] = []
    card_tags_map: list[list[str]] = []

    for item in cards_input:
        if not isinstance(item, dict):
            continue
        q = str(item.get("question", "")).strip()
        a = str(item.get("answer", "")).strip()
        if not q or not a:
            continue

        exp = item.get("explanation")
        diff = item.get("difficulty", "medium")
        if diff not in ("easy", "medium", "hard"):
            diff = "medium"

        tts_text = item.get("tts_text") or q
        tts_lang = item.get("tts_lang") or "en-US"

        card = Card(
            deck_id=deck_id,
            document_id=document_id,
            question=q,
            answer=a,
            explanation=str(exp).strip() if exp else None,
            difficulty=diff,
            tts_text=tts_text,
            tts_lang=tts_lang,
        )
        valid_cards.append(card)

        raw_tags = item.get("tags", [])
        clean_tags: list[str] = []
        if isinstance(raw_tags, list):
            for t in raw_tags:
                if isinstance(t, str) and t.strip():
                    clean_tags.append(t.strip())
                elif isinstance(t, dict) and t.get("name"):
                    clean_tags.append(str(t["name"]).strip())
        card_tags_map.append(clean_tags)

    if not valid_cards:
        return (
            jsonify(
                {
                    "error": "Không có flashcard hợp lệ nào trong danh sách (thiếu câu hỏi hoặc câu trả lời)"
                }
            ),
            400,
        )

    try:
        user_id = deck.user_id
        db.session.add_all(valid_cards)
        db.session.flush()

        for card_obj, tag_names in zip(valid_cards, card_tags_map):
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name, user_id=user_id).first()
                if not tag:
                    tag = Tag(name=tag_name, user_id=user_id)
                    db.session.add(tag)
                    db.session.flush()
                card_obj.tags.append(tag)

        db.session.commit()
        return (
            jsonify(
                {
                    "message": f"Đã lưu thành công {len(valid_cards)} flashcards vào bộ thẻ '{deck.title}'",
                    "deck_id": deck_id,
                    "created_count": len(valid_cards),
                    "cards": [c.to_dict() for c in valid_cards],
                }
            ),
            201,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi lưu hàng loạt thẻ: {str(exc)}"}), 500


def register_batch_routes(bp: Blueprint) -> None:
    bp.add_url_rule("/batch", view_func=create_cards_batch, methods=["POST"])
