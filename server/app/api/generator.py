from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.document import Document
from app.models.flashcard import Card
from app.services.ai_service import (
    generate_cards_from_document_id,
    generate_flashcards_service,
    transcribe_audio_service,
)

generator_bp = Blueprint("generator", __name__, url_prefix="/api")


@generator_bp.route("/generate-from-doc/<int:doc_id>", methods=["POST"])
def generate_from_document_endpoint(doc_id: int):
    """
    Sinh flashcards tự động từ tài liệu bằng AI Flan-T5
    ---
    tags:
      - AI Generator
    parameters:
      - name: doc_id
        in: path
        type: integer
        required: true
        description: ID của tài liệu nguồn
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
              description: ID của người dùng (tùy chọn, mặc định lấy theo tài liệu)
    responses:
      201:
        description: Sinh và lưu flashcards thành công
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

    # Lấy document để xác định user_id mặc định nếu không truyền
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


@generator_bp.route("/generate", methods=["POST"])
def generate_from_raw_text():
    """
    Sinh flashcards tự động từ chuỗi văn bản thuần (Hỗ trợ tương thích ngược)
    ---
    tags:
      - AI Generator
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - text
          properties:
            text:
              type: string
              example: "Thủ đô của Việt Nam là Hà Nội."
            deck_id:
              type: integer
              example: 1
    responses:
      201:
        description: Sinh thẻ thành công
      400:
        description: Văn bản rỗng
    """
    data = request.get_json(silent=True) or {}
    text = data.get("text")
    deck_id = data.get("deck_id")

    if not text or not isinstance(text, str) or not text.strip():
        return jsonify({"error": "Văn bản bài học không được để trống"}), 400

    try:
        generated_cards = generate_flashcards_service(text)
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
                    "count": len(saved_cards),
                    "cards": [c.to_dict() for c in saved_cards],
                }
            ),
            201,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi xử lý AI: {str(exc)}"}), 500


@generator_bp.route("/transcribe", methods=["POST"])
def transcribe_audio_endpoint():
    """
    Bóc băng âm thanh (Speech-to-Text) trung gian qua AI Pipeline Microservice
    ---
    tags:
      - AI Generator
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: File âm thanh (.mp3, .wav, .m4a)
      - name: language
        in: formData
        type: string
        required: false
        default: vi
        description: "Mã ngôn ngữ (mặc định: vi)"
    responses:
      200:
        description: Bóc băng thành công
      400:
        description: File không hợp lệ hoặc để trống
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
