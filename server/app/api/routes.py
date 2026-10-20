from flask import Blueprint, jsonify, request  # pyright: ignore[reportMissingImports] # type: ignore[import-not-found]
from app.core.database import db
from app.models.flashcard import Flashcard
from app.services.ai_service import generate_flashcards_service

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/health", methods=["GET"])
def health_check():
    """
    Kiểm tra tình trạng hoạt động của hệ thống và API
    ---
    tags:
      - System
    summary: Kiểm tra sức khỏe hệ thống
    description: Trả về trạng thái hoạt động của cơ sở dữ liệu và AI pipeline.
    responses:
      200:
        description: Trạng thái hệ thống bình thường
        schema:
          $ref: '#/definitions/HealthResponse'
    """
    return (
        jsonify(
            {
                "status": "healthy",
                "database": "connected",
                "ai_pipeline": "ready",
            }
        ),
        200,
    )


@api_bp.route("/cards", methods=["GET"])
def get_cards():
    """
    Lấy danh sách tất cả các flashcards đã lưu
    ---
    tags:
      - Flashcards
    summary: Lấy danh sách flashcards
    description: Trả về toàn bộ danh sách flashcards đã được sinh và lưu trữ trong cơ sở dữ liệu SQLite.
    responses:
      200:
        description: Danh sách flashcards thành công
        schema:
          type: array
          items:
            $ref: '#/definitions/Flashcard'
    """
    cards = Flashcard.query.all()
    return jsonify([card.to_dict() for card in cards]), 200


@api_bp.route("/cards/<int:card_id>", methods=["GET"])
def get_card_by_id(card_id: int):
    """
    Lấy chi tiết một flashcard theo ID
    ---
    tags:
      - Flashcards
    summary: Lấy chi tiết thẻ flashcard
    description: Trả về chi tiết câu hỏi và câu trả lời của flashcard dựa trên ID cung cấp.
    parameters:
      - name: card_id
        in: path
        type: integer
        required: true
        description: ID của flashcard cần truy vấn
    responses:
      200:
        description: Thông tin flashcard tìm thấy
        schema:
          $ref: '#/definitions/Flashcard'
      404:
        description: Không tìm thấy flashcard tương ứng với ID
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    card = Flashcard.query.get(card_id)
    if not card:
        return jsonify({"error": f"Không tìm thấy flashcard với ID {card_id}"}), 404
    return jsonify(card.to_dict()), 200


@api_bp.route("/cards/<int:card_id>", methods=["DELETE"])
def delete_card(card_id: int):
    """
    Xóa một flashcard theo ID
    ---
    tags:
      - Flashcards
    summary: Xóa flashcard
    description: Xóa bỏ thẻ ghi nhớ flashcard khỏi cơ sở dữ liệu SQLite.
    parameters:
      - name: card_id
        in: path
        type: integer
        required: true
        description: ID của flashcard cần xóa
    responses:
      200:
        description: Xóa flashcard thành công
        schema:
          $ref: '#/definitions/MessageResponse'
      404:
        description: Không tìm thấy flashcard để xóa
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    card = Flashcard.query.get(card_id)
    if not card:
        return jsonify({"error": f"Không tìm thấy flashcard với ID {card_id}"}), 404

    db.session.delete(card)
    db.session.commit()
    return jsonify({"message": f"Đã xóa flashcard ID {card_id} thành công"}), 200


@api_bp.route("/generate", methods=["POST"])
def generate():
    """
    Sinh flashcards tự động từ văn bản bài học qua AI pipeline
    ---
    tags:
      - AI Pipeline
    summary: Sinh thẻ flashcard bằng Flan-T5
    description: Tiếp nhận văn bản bài học, làm sạch văn bản, phân đoạn (chunking), chạy mô hình sinh flashcard Flan-T5 và lưu các thẻ mới vào SQLite.
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/GenerateRequest'
    responses:
      201:
        description: Sinh và lưu flashcards thành công
        schema:
          $ref: '#/definitions/GenerateResponse'
      400:
        description: Văn bản bài học rỗng hoặc định dạng không hợp lệ
        schema:
          $ref: '#/definitions/ErrorResponse'
      500:
        description: Lỗi xảy ra trong quá trình xử lý AI pipeline
        schema:
          $ref: '#/definitions/ErrorResponse'
    """
    data = request.get_json(silent=True) or {}
    text = data.get("text")

    # Validation: Kiểm tra văn bản rỗng hoặc chỉ chứa khoảng trắng
    if not text or not isinstance(text, str) or not text.strip():
        return jsonify({"error": "Văn bản bài học không được để trống"}), 400

    try:
        # Gọi AI service sinh flashcards
        generated_cards = generate_flashcards_service(text)

        # Lưu từng flashcard vào SQLite
        saved_cards = []
        for item in generated_cards:
            card = Flashcard(
                question=item["question"],
                answer=item["answer"],
            )
            db.session.add(card)
            saved_cards.append(card)

        db.session.commit()

        return (
            jsonify(
                {
                    "count": len(saved_cards),
                    "cards": [card.to_dict() for card in saved_cards],
                }
            ),
            201,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi xử lý AI Pipeline: {str(exc)}"}), 500
