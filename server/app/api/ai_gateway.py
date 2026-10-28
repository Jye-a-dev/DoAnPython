"""
ai_gateway.py — AI Pipeline Gateway endpoints (Tag: AI Generator).
POST /api/generate: Forward text sang AI Pipeline để sinh Q&A flashcards.
POST /api/generate-from-doc/{doc_id}: Đọc extracted_text, sinh thẻ, lưu cards và ghi ai_generation_logs.
POST /api/transcribe: Forward file audio sang Whisper STT Pipeline.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.document import Document
from app.models.flashcard import Card
from app.services.ai_service import (
    generate_cards_from_document_id,
    generate_flashcards_service,
    transcribe_audio_service,
)

ai_gateway_bp = Blueprint("ai_gateway", __name__, url_prefix="/api")


@ai_gateway_bp.route("/generate", methods=["POST"])
def generate_from_raw_text():
    """
    Sinh flashcards tự động từ chuỗi văn bản (POST /api/generate)
    ---
    tags:
      - AI Generator
    summary: Forward văn bản sang AI Pipeline sinh câu hỏi Q&A flashcards
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
            deck_id:
              type: integer
              example: 1
              description: ID bộ thẻ đích để lưu thẻ sinh ra
            max_cards:
              type: integer
              default: 3
              example: 3
              description: Số lượng thẻ tối đa cần sinh
    responses:
      201:
        description: Sinh và lưu flashcards thành công
      400:
        description: Văn bản rỗng hoặc định dạng không hợp lệ
      500:
        description: Lỗi tiến trình AI Pipeline inference
    """
    data = request.get_json(silent=True) or {}
    text = data.get("text")
    deck_id = data.get("deck_id")
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

        saved_cards = []
        for item in generated_cards:
            card = Card(
                question=item["question"],
                answer=item["answer"],
                deck_id=deck_id,
            )
            db.session.add(card)
            saved_cards.append(card)

        db.session.commit()
        return (
            jsonify(
                {
                    "count": (
                        pipeline_data.get("count", len(saved_cards))
                        if isinstance(pipeline_data, dict)
                        else len(saved_cards)
                    ),
                    "cards": [c.to_dict() for c in saved_cards],
                    "inference_time_seconds": inference_time_seconds,
                }
            ),
            201,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi xử lý AI: {str(exc)}"}), 500


@ai_gateway_bp.route("/generate-from-doc/<int:doc_id>", methods=["POST"])
def generate_from_document_endpoint(doc_id: int):
    """
    Sinh flashcards tự động từ tài liệu đã lưu (POST /api/generate-from-doc/{doc_id})
    ---
    tags:
      - AI Generator
    summary: Đọc extracted_text từ Documents, gọi AI Pipeline sinh thẻ, lưu Cards và ghi AI Logs
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
          required:
            - deck_id
          properties:
            deck_id:
              type: integer
              example: 1
              description: ID của bộ thẻ để lưu kết quả flashcards
            user_id:
              type: integer
              example: 1
              description: ID của người dùng sở hữu bộ thẻ
    responses:
      201:
        description: Sinh và lưu flashcards cùng bản ghi telemetry thành công
      400:
        description: Thiếu dữ liệu hoặc deck_id không hợp lệ
      404:
        description: Không tìm thấy tài liệu hoặc bộ thẻ
      500:
        description: Lỗi xảy ra trong tiến trình AI inference
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

    document = db.session.get(Document, doc_id)
    if not document:
        return jsonify({"error": f"Không tìm thấy tài liệu với ID {doc_id}"}), 404

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
            doc_id=doc_id, deck_id=deck_id, user_id=user_id
        )
        return jsonify(result), 201
    except ValueError as val_err:
        return jsonify({"error": str(val_err)}), 400
    except Exception as exc:
        return jsonify({"error": f"Lỗi sinh thẻ AI: {str(exc)}"}), 500


@ai_gateway_bp.route("/transcribe", methods=["POST"])
def transcribe_audio_endpoint():
    """
    Bóc băng giọng nói sang văn bản (POST /api/transcribe)
    ---
    tags:
      - AI Generator
    summary: Forward file audio sang Whisper STT Pipeline bóc băng thành văn bản
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: Tệp âm thanh cần bóc băng (.mp3, .wav, .m4a)
      - name: language
        in: formData
        type: string
        required: false
        default: vi
        description: Mã ngôn ngữ (mặc định vi)
    responses:
      200:
        description: Bóc băng âm thanh thành công
      400:
        description: File âm thanh không hợp lệ hoặc rỗng
      500:
        description: Lỗi tiến trình Whisper STT
    """
    if "file" not in request.files:
        return jsonify({"error": "Không tìm thấy file âm thanh trong form data"}), 400

    audio_file = request.files["file"]
    filename = audio_file.filename or "audio.wav"
    language = request.form.get("language", "vi")

    file_bytes = audio_file.read()
    if not file_bytes:
        return jsonify({"error": "File âm thanh rỗng (0 bytes)"}), 400

    try:
        result = transcribe_audio_service(
            file_bytes=file_bytes,
            filename=filename,
            language=language,
        )
        return jsonify(result), 200
    except Exception as exc:
        return jsonify({"error": f"Lỗi bóc băng âm thanh: {str(exc)}"}), 500


# Alias for backward compatibility
generator_bp = ai_gateway_bp

