"""
deck_io.py — API Endpoints cho Xuất / Nhập Bộ Thẻ (Export & Import Deck).
POST /api/decks/<deck_id>/import
GET  /api/decks/<deck_id>/export?format=pdf|json|anki|csv
"""

from __future__ import annotations

import io
from flask import Blueprint, Response, jsonify, request, send_file
from app.core.database import db
from app.models.flashcard import Card, Deck
from app.models.study import StudyReview
from app.services.deck_exporter import (
    export_deck_anki,
    export_deck_csv,
    export_deck_json,
    export_deck_pdf_printable,
)
from app.services.deck_importer import (
    import_cards_from_file_data,
    parse_delimited_text,
)

deck_io_bp = Blueprint("deck_io", __name__, url_prefix="/api/decks")


@deck_io_bp.route("/<int:deck_id>/import", methods=["POST"])
def import_deck_cards(deck_id: int):
    """
    Nhập flashcards vào bộ thẻ từ file (CSV, XLSX, TXT) hoặc text thô (POST /api/decks/{deck_id}/import)
    ---
    tags:
      - Decks
    summary: Nhập hàng loạt flashcards vào một bộ thẻ
    parameters:
      - name: deck_id
        in: path
        type: integer
        required: true
        description: ID bộ thẻ đích
    responses:
      201:
        description: Đã nạp thành công các thẻ vào bộ thẻ
      400:
        description: Dữ liệu không hợp lệ hoặc không trích xuất được thẻ
      404:
        description: Không tìm thấy bộ thẻ
    """
    deck = db.session.get(Deck, deck_id)
    if not deck:
        return jsonify({"error": f"Không tìm thấy bộ thẻ với ID {deck_id}"}), 404

    parsed_cards = []

    # 1. Kiểm tra tải file qua multipart form-data
    if "file" in request.files:
        f = request.files["file"]
        if f.filename:
            raw_bytes = f.read()
            parsed_cards = import_cards_from_file_data(f.filename, raw_bytes)

    # 2. Hoặc kiểm tra tải text thô qua JSON body hoặc form data
    if not parsed_cards:
        data = request.get_json(silent=True) or {}
        raw_text = (
            data.get("text")
            or data.get("content")
            or request.form.get("text")
            or request.form.get("content")
            or ""
        )
        if raw_text:
            parsed_cards = parse_delimited_text(raw_text)

    if not parsed_cards:
        return (
            jsonify(
                {
                    "error": "Không trích xuất được flashcard nào từ dữ liệu nạp vào. "
                    "Vui lòng kiểm tra định dạng CSV, XLSX hoặc dán các dòng Tab-separated (Front \\t Back)."
                }
            ),
            400,
        )

    new_cards: list[Card] = []
    for c in parsed_cards:
        q = str(c.get("question", "")).strip()
        a = str(c.get("answer", "")).strip()
        if not q or not a:
            continue
        new_cards.append(
            Card(
                deck_id=deck_id,
                question=q,
                answer=a,
                explanation=c.get("explanation"),
                difficulty=c.get("difficulty", "medium"),
                personal_notes=c.get("personal_notes"),
            )
        )

    if not new_cards:
        return (
            jsonify({"error": "Không có câu hỏi hoặc đáp án hợp lệ trong danh sách"}),
            400,
        )

    try:
        db.session.add_all(new_cards)
        db.session.commit()
        return (
            jsonify(
                {
                    "message": f"Đã nhập thành công {len(new_cards)} flashcards vào bộ thẻ '{deck.title}'",
                    "deck_id": deck_id,
                    "created_count": len(new_cards),
                    "cards": [c.to_dict() for c in new_cards],
                }
            ),
            201,
        )
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi lưu trữ dữ liệu nạp: {str(exc)}"}), 500


@deck_io_bp.route("/<int:deck_id>/export", methods=["GET"])
def export_deck_endpoint(deck_id: int):
    """
    Kết xuất bộ thẻ ra file (GET /api/decks/{deck_id}/export?format=pdf|json|anki|csv)
    ---
    tags:
      - Decks
    summary: Kết xuất flashcards kèm metadata SM-2 hoặc bản in A4 2 mặt
    parameters:
      - name: deck_id
        in: path
        type: integer
        required: true
        description: ID bộ thẻ
      - name: format
        in: query
        type: string
        enum: [pdf, json, anki, csv]
        default: pdf
        description: Định dạng kết xuất
    responses:
      200:
        description: Trả về file tải xuống
      404:
        description: Không tìm thấy bộ thẻ
    """
    deck = db.session.get(Deck, deck_id)
    if not deck:
        return jsonify({"error": f"Không tìm thấy bộ thẻ với ID {deck_id}"}), 404

    export_fmt = (request.args.get("format") or "pdf").lower().strip()
    cards_query = (
        Card.query.filter_by(deck_id=deck_id).order_by(Card.created_at.asc()).all()
    )

    # Thu thập metadata SM-2 gần nhất cho từng thẻ
    card_ids = [c.id for c in cards_query]
    reviews_map = {}
    if card_ids:
        latest_revs = (
            StudyReview.query.filter(StudyReview.card_id.in_(card_ids))
            .order_by(StudyReview.reviewed_at.desc())
            .all()
        )
        for r in latest_revs:
            if r.card_id not in reviews_map:
                reviews_map[r.card_id] = r

    cards_data = []
    for c in cards_query:
        cd = c.to_dict()
        rev = reviews_map.get(c.id)
        if rev:
            cd["ease_factor"] = rev.ease_factor
            cd["interval_days"] = rev.interval_days
            cd["repetitions"] = rev.repetitions
            cd["next_review_date"] = (
                rev.next_review_date.isoformat() if rev.next_review_date else None
            )
        else:
            cd["ease_factor"] = 2.5
            cd["interval_days"] = 1
            cd["repetitions"] = 0
            cd["next_review_date"] = None
        cards_data.append(cd)

    safe_title = (
        "".join(ch if ch.isalnum() or ch in ("-", "_") else "_" for ch in deck.title)
        or f"deck_{deck_id}"
    )

    if export_fmt == "csv":
        csv_str = export_deck_csv(deck.title, cards_data)
        return Response(
            csv_str,
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={safe_title}.csv"},
        )

    if export_fmt in ("anki", "txt"):
        anki_str = export_deck_anki(deck.title, cards_data)
        return Response(
            anki_str,
            mimetype="text/plain; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename={safe_title}_anki.txt"
            },
        )

    if export_fmt == "json":
        json_data = export_deck_json(deck.to_dict(), cards_data)
        return jsonify(json_data), 200

    # Mặc định: PDF Printable A4 2 mặt cắt rời
    pdf_bytes = export_deck_pdf_printable(deck.title, cards_data)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{safe_title}_printable.pdf",
    )
