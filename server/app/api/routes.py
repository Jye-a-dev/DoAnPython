"""
routes.py — Unified API Router for Flashcard Backend Server (Port 3000).
Implements Document BLOB Storage, Full Decks/Cards CRUD, SM-2 SRS Study Engine,
and AI Pipeline Gateway forwarding.
"""

from __future__ import annotations

import io
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from flask import Blueprint, jsonify, request, send_file
from sqlalchemy import text

from app.core.database import db
from app.models.document import Document
from app.models.flashcard import Card, Deck
from app.models.study import StudyReview, StudySession
from app.models.user import User
from app.services.ai_service import (
    check_pipeline_health_service,
    generate_cards_from_document_id,
    generate_flashcards_service,
    transcribe_audio_service,
)
from app.services.document_service import (
    delete_document,
    get_document_by_id,
    list_documents,
    process_and_save_document,
)
from app.services.flashcard_service import (
    create_card,
    create_deck,
    delete_all_cards,
    delete_card,
    delete_deck,
    get_card_by_id,
    get_deck_by_id,
    list_cards,
    list_decks,
    update_card,
    update_deck,
)
from app.validators.card_validator import validate_card_payload
from app.validators.deck_validator import validate_deck_payload
from app.validators.document_validator import validate_document_upload
from app.validators.study_validator import (
    validate_study_review_payload,
    validate_study_session_payload,
)

# ---------------------------------------------------------------------------
# Blueprint Definitions
# ---------------------------------------------------------------------------
documents_bp = Blueprint("documents", __name__, url_prefix="/api/documents")
generator_bp = Blueprint("generator", __name__, url_prefix="/api")
decks_bp = Blueprint("decks", __name__, url_prefix="/api/decks")
cards_bp = Blueprint("cards", __name__, url_prefix="/api/cards")
study_bp = Blueprint("study", __name__, url_prefix="/api/study")
system_bp = Blueprint("system", __name__, url_prefix="/api")


# ===========================================================================
# 1. DOCUMENT & UPLOAD API
# ===========================================================================
@documents_bp.route("/upload", methods=["POST"])
def upload_document():
    """Upload và xử lý tài liệu (PDF / TXT) hoàn toàn trong RAM và lưu BLOB."""
    if "file" not in request.files:
        return (
            jsonify(
                {"error": "Không tìm thấy trường 'file' trong multipart/form-data"}
            ),
            400,
        )

    file_storage = request.files["file"]
    user_id_raw = request.form.get("user_id")

    if not user_id_raw:
        return jsonify({"error": "Trường 'user_id' là bắt buộc"}), 400

    try:
        user_id = int(user_id_raw)
        if user_id <= 0:
            return jsonify({"error": "Trường 'user_id' phải là số nguyên dương"}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Trường 'user_id' phải là số nguyên"}), 400

    is_valid, error_msg, _, _ = validate_document_upload(file_storage)
    if not is_valid:
        return jsonify({"error": error_msg}), 400

    try:
        document = process_and_save_document(user_id=user_id, file_storage=file_storage)
        doc_dict = document.to_dict()
        doc_dict["message"] = "Upload và xử lý tài liệu thành công"
        doc_dict["document"] = document.to_dict()
        return jsonify(doc_dict), 201
    except Exception as exc:
        return jsonify({"error": f"Lỗi xử lý tài liệu: {str(exc)}"}), 500


@documents_bp.route("/<int:doc_id>", methods=["GET"])
def get_document(doc_id: int):
    """Lấy metadata và text trích xuất (hoặc binary BLOB nếu ?download=true)."""
    document = get_document_by_id(doc_id)
    if not document:
        return jsonify({"error": f"Không tìm thấy tài liệu với ID {doc_id}"}), 404

    is_download = request.args.get("download", "").lower() in ["true", "1"]
    if is_download:
        mimetype = (
            "application/pdf"
            if document.file_type == "pdf"
            else "text/plain; charset=utf-8"
        )
        return send_file(
            io.BytesIO(document.file_blob),
            mimetype=mimetype,
            as_attachment=True,
            download_name=document.filename,
        )

    return jsonify(document.to_dict()), 200


@documents_bp.route("", methods=["GET"])
def get_all_documents():
    """Lấy danh sách các tài liệu đã upload."""
    user_id_raw = request.args.get("user_id")
    user_id = int(user_id_raw) if user_id_raw and user_id_raw.isdigit() else None
    documents = list_documents(user_id=user_id)
    return jsonify([doc.to_dict() for doc in documents]), 200


@documents_bp.route("/<int:doc_id>", methods=["DELETE"])
def remove_document(doc_id: int):
    """Xóa tài liệu theo ID."""
    success = delete_document(doc_id)
    if not success:
        return jsonify({"error": f"Không tìm thấy tài liệu với ID {doc_id}"}), 404
    return jsonify({"message": f"Đã xóa tài liệu ID {doc_id} thành công"}), 200


# ===========================================================================
# 2. AI GATEWAY ROUTES (Forward to AI Pipeline Microservice)
# ===========================================================================
@generator_bp.route("/transcribe", methods=["POST"])
def transcribe_audio_gateway():
    """Forward file audio sang AI Pipeline (POST /api/pi/transcribe)."""
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


@generator_bp.route("/generate-from-doc/<int:doc_id>", methods=["POST"])
def generate_from_doc_gateway(doc_id: int):
    """Đọc extracted_text từ DB -> Forward sang Pipeline -> Lưu cards và log."""
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
    user_id = int(user_id_raw) if user_id_raw is not None else document.user_id

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
def generate_raw_text_gateway():
    """Sinh thẻ trực tiếp từ chuỗi text truyền lên (Forward sang Pipeline)."""
    data = request.get_json(silent=True) or {}
    text_content = data.get("text")
    deck_id = data.get("deck_id")

    if (
        not text_content
        or not isinstance(text_content, str)
        or not text_content.strip()
    ):
        return jsonify({"error": "Văn bản bài học không được để trống"}), 400

    try:
        generated_pairs = generate_flashcards_service(text_content.strip())
        saved_cards: List[Card] = []
        for item in generated_pairs:
            card = Card(
                question=item.get("question", ""),
                answer=item.get("answer", ""),
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


@cards_bp.route("/generate", methods=["POST"])
def generate_cards_dual_mode():
    """Sinh thẻ linh hoạt từ text trực tiếp hoặc từ doc_id qua AI Pipeline."""
    data = request.get_json(silent=True) or {}
    text_content = data.get("text")
    doc_id_raw = data.get("doc_id") or data.get("document_id")

    # Nhánh 1: Sinh trực tiếp từ text
    if text_content and isinstance(text_content, str) and text_content.strip():
        deck_id = data.get("deck_id")
        try:
            generated_pairs = generate_flashcards_service(text_content.strip())
            saved_cards: List[Card] = []
            for item in generated_pairs:
                card = Card(
                    question=item.get("question", ""),
                    answer=item.get("answer", ""),
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

    # Nhánh 2: Sinh từ Document ID đã lưu trong cơ sở dữ liệu
    if doc_id_raw is not None:
        try:
            doc_id = int(doc_id_raw)
            if doc_id <= 0:
                return (
                    jsonify({"error": "Trường 'doc_id' phải là số nguyên dương"}),
                    400,
                )
        except (ValueError, TypeError):
            return jsonify({"error": "Trường 'doc_id' phải là số nguyên"}), 400

        document = db.session.get(Document, doc_id)
        if not document:
            return jsonify({"error": f"Không tìm thấy tài liệu với ID {doc_id}"}), 404

        user_id_raw = data.get("user_id")
        user_id = int(user_id_raw) if user_id_raw is not None else document.user_id

        deck_id_raw = data.get("deck_id")
        if deck_id_raw is not None:
            deck_id = int(deck_id_raw)
        else:
            deck = Deck.query.filter_by(user_id=user_id).first()
            if not deck:
                deck = Deck(user_id=user_id, title=f"AI Deck - {document.filename}")
                db.session.add(deck)
                db.session.commit()
            deck_id = deck.id

        try:
            result = generate_cards_from_document_id(
                doc_id=doc_id, deck_id=deck_id, user_id=user_id
            )
            return jsonify(result), 201
        except ValueError as val_err:
            return jsonify({"error": str(val_err)}), 400
        except Exception as exc:
            return jsonify({"error": f"Lỗi sinh thẻ AI: {str(exc)}"}), 500

    return jsonify({"error": "Cần truyền 'text' hoặc 'doc_id' trong JSON payload"}), 400


# ===========================================================================
# 3. FULL CRUD DECKS & CARDS
# ===========================================================================
@decks_bp.route("", methods=["GET"])
def get_all_decks():
    """Lấy danh sách các bộ thẻ (Decks)."""
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
    """Tạo mới một bộ thẻ (Deck)."""
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
    """Lấy thông tin chi tiết bộ thẻ kèm danh sách thẻ."""
    deck = get_deck_by_id(deck_id)
    if not deck:
        return jsonify({"error": f"Không tìm thấy bộ thẻ với ID {deck_id}"}), 404

    deck_dict = deck.to_dict()
    deck_dict["cards"] = [c.to_dict() for c in deck.cards] if deck.cards else []
    return jsonify(deck_dict), 200


@decks_bp.route("/<int:deck_id>", methods=["PUT"])
def update_deck_detail(deck_id: int):
    """Cập nhật thông tin bộ thẻ."""
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
    """Xóa bộ thẻ theo ID (Cascade xóa thẻ bên trong)."""
    success = delete_deck(deck_id)
    if not success:
        return jsonify({"error": f"Không tìm thấy bộ thẻ với ID {deck_id}"}), 404
    return jsonify({"message": f"Đã xóa bộ thẻ ID {deck_id} thành công"}), 200


@cards_bp.route("", methods=["GET"])
def get_all_cards():
    """Lấy danh sách các flashcards."""
    deck_id_raw = request.args.get("deck_id")
    document_id_raw = request.args.get("document_id")

    deck_id = int(deck_id_raw) if deck_id_raw and deck_id_raw.isdigit() else None
    document_id = (
        int(document_id_raw) if document_id_raw and document_id_raw.isdigit() else None
    )

    cards = list_cards(deck_id=deck_id, document_id=document_id)
    return jsonify([c.to_dict() for c in cards]), 200


@cards_bp.route("", methods=["POST"])
def create_new_card():
    """Tạo mới một flashcard thủ công."""
    data = request.get_json(silent=True) or {}
    is_valid, error_msg, cleaned_data = validate_card_payload(data, is_update=False)
    if not is_valid or cleaned_data is None:
        return jsonify({"error": error_msg}), 400

    try:
        card = create_card(cleaned_data)
        card_dict = card.to_dict()
        card_dict["message"] = "Tạo flashcard thành công"
        card_dict["card"] = card.to_dict()
        return jsonify(card_dict), 201
    except Exception as exc:
        return jsonify({"error": f"Lỗi tạo flashcard: {str(exc)}"}), 500


@cards_bp.route("/<int:card_id>", methods=["GET"])
def get_card_detail(card_id: int):
    """Lấy chi tiết một flashcard theo ID."""
    card = get_card_by_id(card_id)
    if not card:
        return jsonify({"error": f"Không tìm thấy flashcard với ID {card_id}"}), 404
    return jsonify(card.to_dict()), 200


@cards_bp.route("/<int:card_id>", methods=["PUT"])
def update_card_detail(card_id: int):
    """Cập nhật nội dung flashcard."""
    data = request.get_json(silent=True) or {}
    is_valid, error_msg, cleaned_data = validate_card_payload(data, is_update=True)
    if not is_valid or cleaned_data is None:
        return jsonify({"error": error_msg}), 400

    card = update_card(card_id, cleaned_data)
    if not card:
        return jsonify({"error": f"Không tìm thấy flashcard với ID {card_id}"}), 404

    card_dict = card.to_dict()
    card_dict["message"] = "Cập nhật flashcard thành công"
    card_dict["card"] = card.to_dict()
    return jsonify(card_dict), 200


@cards_bp.route("/<int:card_id>", methods=["DELETE"])
def delete_card_endpoint(card_id: int):
    """Xóa flashcard theo ID."""
    success = delete_card(card_id)
    if not success:
        return jsonify({"error": f"Không tìm thấy flashcard với ID {card_id}"}), 404
    return jsonify({"message": f"Đã xóa flashcard ID {card_id} thành công"}), 200


@cards_bp.route("", methods=["DELETE"])
def delete_all_cards_endpoint():
    """Xóa toàn bộ flashcards (hoặc lọc theo query param deck_id)."""
    deck_id_raw = request.args.get("deck_id")
    deck_id = int(deck_id_raw) if deck_id_raw and deck_id_raw.isdigit() else None
    count = delete_all_cards(deck_id=deck_id)
    return (
        jsonify(
            {
                "message": "Đã xóa toàn bộ flashcards thành công",
                "deleted_count": count,
            }
        ),
        200,
    )


# ===========================================================================
# 4. STUDY & REVIEW APIS (SM-2 SRS ALGORITHM)
# ===========================================================================
def calculate_sm2(
    review_rating: int,
    current_ef: float = 2.5,
    current_reps: int = 0,
    current_interval: int = 1,
) -> tuple[float, int, int]:
    """
    Thuật toán lặp lại ngắt quãng SM-2 (Spaced Repetition SM-2).
    review_rating: 1-Again, 2-Hard, 3-Good, 4-Easy.
    Trả về: (ease_factor_mới, interval_days_mới, repetitions_mới).
    """
    if review_rating == 1:
        # Again: Reset repetition count, chu kỳ 1 ngày, giảm ease factor
        repetitions = 0
        interval_days = 1
        new_ef = max(1.3, current_ef - 0.20)
    elif review_rating == 2:
        # Hard: Tăng nhẹ chu kỳ, giảm nhẹ ease factor
        repetitions = current_reps + 1
        if repetitions == 1:
            interval_days = 1
        elif repetitions == 2:
            interval_days = 3
        else:
            interval_days = max(1, int(round(current_interval * 1.2)))
        new_ef = max(1.3, current_ef - 0.15)
    elif review_rating == 3:
        # Good: SM-2 chuẩn
        repetitions = current_reps + 1
        if repetitions == 1:
            interval_days = 1
        elif repetitions == 2:
            interval_days = 6
        else:
            interval_days = max(1, int(round(current_interval * current_ef)))
        new_ef = max(1.3, current_ef)
    elif review_rating == 4:
        # Easy: Chu kỳ mở rộng nhanh, tăng ease factor
        repetitions = current_reps + 1
        if repetitions == 1:
            interval_days = 4
        elif repetitions == 2:
            interval_days = 10
        else:
            interval_days = max(1, int(round(current_interval * current_ef * 1.3)))
        new_ef = max(1.3, current_ef + 0.15)
    else:
        repetitions = current_reps + 1
        interval_days = max(1, current_interval)
        new_ef = max(1.3, current_ef)

    return round(new_ef, 2), interval_days, repetitions


@study_bp.route("/sessions", methods=["POST"])
def start_study_session():
    """Mở phiên học mới (Study Session)."""
    data = request.get_json(silent=True) or {}
    is_valid, error_msg, cleaned_data = validate_study_session_payload(data)
    if not is_valid or cleaned_data is None:
        return jsonify({"error": error_msg}), 400

    user_id = cleaned_data["user_id"]
    deck_id = cleaned_data["deck_id"]

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": f"Không tìm thấy người dùng với ID {user_id}"}), 404

    deck = db.session.get(Deck, deck_id)
    if not deck:
        return jsonify({"error": f"Không tìm thấy bộ thẻ với ID {deck_id}"}), 404

    session = StudySession(
        user_id=user_id,
        deck_id=deck_id,
        started_at=datetime.utcnow(),
        total_reviewed=0,
    )
    db.session.add(session)
    db.session.commit()

    session_dict = session.to_dict()
    session_dict["message"] = "Bắt đầu phiên học thành công"
    session_dict["session"] = session.to_dict()
    session_dict["session_id"] = session.id
    return jsonify(session_dict), 201


@study_bp.route("/sessions/<int:session_id>/end", methods=["PUT"])
def end_study_session(session_id: int):
    """Kết thúc một phiên học."""
    session = db.session.get(StudySession, session_id)
    if not session:
        return jsonify({"error": f"Không tìm thấy phiên học với ID {session_id}"}), 404

    session.ended_at = datetime.utcnow()
    db.session.commit()
    return (
        jsonify({"message": "Đã kết thúc phiên học", "session": session.to_dict()}),
        200,
    )


@study_bp.route("/review", methods=["POST"])
def submit_study_review():
    """Ghi nhận đánh giá (1-Again, 2-Hard, 3-Good, 4-Easy) & tính toán SM-2."""
    data = request.get_json(silent=True) or {}
    is_valid, error_msg, cleaned_data = validate_study_review_payload(data)
    if not is_valid or cleaned_data is None:
        return jsonify({"error": error_msg}), 400

    card_id = cleaned_data["card_id"]
    card = db.session.get(Card, card_id)
    if not card:
        return jsonify({"error": f"Không tìm thấy flashcard với ID {card_id}"}), 404

    session_id = cleaned_data.get("session_id")
    user_id = cleaned_data.get("user_id")

    if session_id:
        session = db.session.get(StudySession, session_id)
        if not session:
            return (
                jsonify({"error": f"Không tìm thấy phiên học với ID {session_id}"}),
                404,
            )
        if not user_id:
            user_id = session.user_id
        session.total_reviewed += 1

    if not user_id:
        if card.deck:
            user_id = card.deck.user_id
        else:
            return (
                jsonify({"error": "Không thể xác định user_id cho lượt đánh giá này"}),
                400,
            )

    rating = cleaned_data["review_rating"]

    # Truy vấn lượt review trước đó để lấy state SM-2
    prev_review = (
        StudyReview.query.filter_by(card_id=card_id, user_id=user_id)
        .order_by(StudyReview.reviewed_at.desc())
        .first()
    )

    base_ef = prev_review.ease_factor if prev_review else 2.5
    base_reps = prev_review.repetitions if prev_review else 0
    base_interval = prev_review.interval_days if prev_review else 1

    # Tính toán các chỉ số theo thuật toán SM-2
    new_ef, new_interval, new_reps = calculate_sm2(
        review_rating=rating,
        current_ef=base_ef,
        current_reps=base_reps,
        current_interval=base_interval,
    )

    next_review_date = datetime.utcnow() + timedelta(days=new_interval)

    review = StudyReview(
        session_id=session_id,
        card_id=card_id,
        user_id=user_id,
        review_rating=rating,
        ease_factor=new_ef,
        interval_days=new_interval,
        repetitions=new_reps,
        next_review_date=next_review_date,
        reviewed_at=datetime.utcnow(),
    )
    db.session.add(review)
    db.session.commit()

    review_dict = review.to_dict()
    review_dict["message"] = "Ghi nhận đánh giá ôn tập thành công"
    review_dict["review"] = review.to_dict()
    return jsonify(review_dict), 200


# ===========================================================================
# 5. SYSTEM HEALTH CHECK
# ===========================================================================
@system_bp.route("/health", methods=["GET"])
def health_check():
    """Kiểm tra trạng thái Server + SQLite DB + Ping Healthcheck Pipeline (/api/pi/health)."""
    db_status = "connected"
    try:
        db.session.execute(text("SELECT 1;")).scalar()
    except Exception as exc:
        db_status = f"error: {str(exc)}"

    pipeline_info = check_pipeline_health_service(timeout=2.0)
    pipeline_status = pipeline_info.get("status", "unreachable")
    is_ready = db_status == "connected"

    return (
        jsonify(
            {
                "status": "healthy" if is_ready else "degraded",
                "server": "online",
                "database": db_status,
                "ai_pipeline": pipeline_status,
                "pipeline_details": pipeline_info,
            }
        ),
        200,
    )
