"""
generation_routes.py — Flashcard generation endpoints via AI Pipeline.
"""

from __future__ import annotations

from typing import Any
from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.document import Document
from app.services.ai_service import (
    generate_cards_from_document_id,
    generate_flashcards_service,
)


def generate_from_raw_text():
    """
    Sinh flashcards nháp (in-memory) từ chuỗi văn bản (POST /api/generate)
    ---
    tags:
      - AI Generator
    summary: Forward văn bản sang AI Pipeline sinh Q&A flashcards — trả về draft, KHÔNG lưu DB
    parameters:
      - name: body
        in: body
        required: true
        description: Văn bản bài học đầu vào
        schema:
          type: object
          required:
            - text
          properties:
            text:
              type: string
              example: "Thủ đô của Việt Nam là Hà Nội."
              description: Nội dung đoạn văn bản
            max_cards:
              type: integer
              default: 3
              example: 3
              description: Số lượng thẻ tối đa cần sinh
    responses:
      200:
        description: Danh sách thẻ nháp (chưa lưu vào DB)
      400:
        description: Văn bản rỗng hoặc định dạng không hợp lệ
      500:
        description: Lỗi tiến trình AI Pipeline inference
    """
    data: dict[str, Any] = request.get_json(silent=True) or {}
    text = data.get("text")
    max_cards = data.get("max_cards", 3)
    try:
        max_cards = int(max_cards)
    except (ValueError, TypeError):
        max_cards = 3

    if not text or not isinstance(text, str) or not text.strip():
        return jsonify({"error": "Văn bản bài học không được để trống"}), 400

    try:
        pipeline_data = generate_flashcards_service(text, max_cards=max_cards)
        if isinstance(pipeline_data, dict):
            generated_cards = pipeline_data.get("cards", [])
            inference_time_seconds = pipeline_data.get("inference_time_seconds", 0.0)
        else:
            generated_cards = pipeline_data
            inference_time_seconds = 0.0

        draft_cards = []
        for item in generated_cards:
            q = str(item.get("question", "")).strip()
            a = str(item.get("answer", "")).strip()
            if not q or not a:
                continue
            draft_cards.append(
                {
                    "question": q,
                    "answer": a,
                    "explanation": item.get("explanation", ""),
                    "difficulty": item.get("difficulty", "medium"),
                    "tts_text": q,
                    "tts_lang": "en-US",
                }
            )

        return (
            jsonify(
                {
                    "count": len(draft_cards),
                    "cards": draft_cards,
                    "inference_time_seconds": inference_time_seconds,
                }
            ),
            200,
        )
    except Exception as exc:
        return jsonify({"error": f"Lỗi xử lý AI: {str(exc)}"}), 500


def generate_from_document_endpoint(doc_id: int):
    """
    Sinh flashcards nháp từ tài liệu đã lưu (POST /api/generate-from-doc/{doc_id})
    ---
    tags:
      - AI Generator
    summary: Đọc extracted_text từ Documents, gọi AI Pipeline sinh thẻ nháp — trả về để Preview (KHÔNG lưu DB)
    parameters:
      - name: doc_id
        in: path
        type: integer
        required: true
        description: ID tài liệu nguồn (bảng documents)
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            deck_id:
              type: integer
              example: null
              description: ID của bộ thẻ (tùy chọn, để null khi dùng Preview Checklist)
            user_id:
              type: integer
              example: 1
              description: ID của người dùng sở hữu bộ thẻ
    responses:
      200:
        description: Danh sách thẻ nháp (chưa lưu vào DB) kèm telemetry log
      400:
        description: Thiếu dữ liệu hoặc deck_id không hợp lệ
      404:
        description: Không tìm thấy tài liệu
      500:
        description: Lỗi xảy ra trong tiến trình AI inference
    """
    data = request.get_json(silent=True) or {}

    document = db.session.get(Document, doc_id)
    if not document:
        return jsonify({"error": f"Không tìm thấy tài liệu với ID {doc_id}"}), 404

    deck_id_raw = data.get("deck_id")
    deck_id: int | None = None
    if deck_id_raw is not None:
        try:
            deck_id = int(deck_id_raw)
            if deck_id <= 0:
                deck_id = None
        except (ValueError, TypeError):
            return jsonify({"error": "Trường 'deck_id' phải là số nguyên"}), 400

    user_id_raw = data.get("user_id")
    if user_id_raw is not None:
        try:
            user_id = int(user_id_raw)
        except (ValueError, TypeError):
            return jsonify({"error": "Trường 'user_id' phải là số nguyên"}), 400
    else:
        user_id = document.user_id

    try:
        result = generate_cards_from_document_id(
            doc_id=doc_id,
            deck_id=deck_id,
            user_id=user_id,
            persist_to_db=False,
        )
        return jsonify(result), 200
    except ValueError as val_err:
        return jsonify({"error": str(val_err)}), 400
    except Exception as exc:
        return jsonify({"error": f"Lỗi sinh thẻ AI: {str(exc)}"}), 500


def register_generation_routes(bp: Blueprint) -> None:
    bp.add_url_rule("/generate", view_func=generate_from_raw_text, methods=["POST"])
    bp.add_url_rule(
        "/generate-from-doc/<int:doc_id>",
        view_func=generate_from_document_endpoint,
        methods=["POST"],
    )
