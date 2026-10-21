from flask import Blueprint, jsonify, request
from app.services.flashcard_service import (
    create_deck,
    get_deck_by_id,
    list_decks,
    update_deck,
    delete_deck,
)
from app.validators.deck_validator import validate_deck_payload

decks_bp = Blueprint("decks", __name__, url_prefix="/api/decks")


@decks_bp.route("", methods=["GET"])
def get_all_decks():
    """
    Lấy danh sách các bộ thẻ (Decks)
    ---
    tags:
      - Decks
    parameters:
      - name: user_id
        in: query
        type: integer
        required: false
        description: Lọc theo ID người dùng
      - name: is_public
        in: query
        type: boolean
        required: false
        description: Lọc theo trạng thái công khai
    responses:
      200:
        description: Danh sách bộ thẻ thành công
    """
    user_id_raw = request.args.get("user_id")
    is_public_raw = request.args.get("is_public")

    user_id = int(user_id_raw) if user_id_raw and user_id_raw.isdigit() else None
    is_public = (
        is_public_raw.lower() in ["true", "1"] if is_public_raw is not None else None
    )

    decks = list_decks(user_id=user_id, is_public=is_public)
    return jsonify([d.to_dict() for d in decks]), 200


@decks_bp.route("", methods=["POST"])
def create_new_deck():
    """
    Tạo mới một bộ thẻ (Deck)
    ---
    tags:
      - Decks
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - title
            - user_id
          properties:
            title:
              type: string
              example: "Lập trình Python"
            user_id:
              type: integer
              example: 1
            description:
              type: string
              example: "Bộ câu hỏi ôn thi môn Lập trình Python"
            is_public:
              type: boolean
              example: false
    responses:
      201:
        description: Tạo bộ thẻ thành công
      400:
        description: Dữ liệu không hợp lệ
    """
    data = request.get_json(silent=True) or {}
    is_valid, error_msg, cleaned_data = validate_deck_payload(data, is_update=False)
    if not is_valid or cleaned_data is None:
        return jsonify({"error": error_msg}), 400

    try:
        deck = create_deck(cleaned_data)
        deck_dict = deck.to_dict()
        deck_dict["message"] = "Tạo bộ thẻ thành công"
        deck_dict["deck"] = deck.to_dict()
        return jsonify(deck_dict), 201
    except Exception as exc:
        return jsonify({"error": f"Lỗi tạo bộ thẻ: {str(exc)}"}), 500


@decks_bp.route("/<int:deck_id>", methods=["GET"])
def get_deck_detail(deck_id: int):
    """Lấy chi tiết bộ thẻ kèm danh sách thẻ"""
    deck = get_deck_by_id(deck_id)
    if not deck:
        return jsonify({"error": f"Không tìm thấy bộ thẻ với ID {deck_id}"}), 404

    deck_dict = deck.to_dict()
    deck_dict["cards"] = [c.to_dict() for c in deck.cards] if deck.cards else []
    return jsonify(deck_dict), 200


@decks_bp.route("/<int:deck_id>", methods=["PUT"])
def update_deck_detail(deck_id: int):
    """Cập nhật thông tin bộ thẻ"""
    data = request.get_json(silent=True) or {}
    is_valid, error_msg, cleaned_data = validate_deck_payload(data, is_update=True)
    if not is_valid or cleaned_data is None:
        return jsonify({"error": error_msg}), 400

    deck = update_deck(deck_id, cleaned_data)
    if not deck:
        return jsonify({"error": f"Không tìm thấy bộ thẻ với ID {deck_id}"}), 404

    deck_dict = deck.to_dict()
    deck_dict["message"] = "Cập nhật bộ thẻ thành công"
    deck_dict["deck"] = deck.to_dict()
    return jsonify(deck_dict), 200


@decks_bp.route("/<int:deck_id>", methods=["DELETE"])
def delete_deck_endpoint(deck_id: int):
    """Xóa bộ thẻ"""
    success = delete_deck(deck_id)
    if not success:
        return jsonify({"error": f"Không tìm thấy bộ thẻ với ID {deck_id}"}), 404
    return jsonify({"message": f"Đã xóa bộ thẻ ID {deck_id} thành công"}), 200
