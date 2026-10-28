"""
session_routes.py — Study Session endpoints (Table 11: study_sessions).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.flashcard import Deck
from app.models.study import StudySession
from app.models.user import User


def start_study_session():
    """
    Bắt đầu phiên học mới (POST /api/study/sessions)
    ---
    tags:
      - Study & SRS Reviews
    summary: Bắt đầu phiên học mới (deck_id, user_id)
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - deck_id
            - user_id
          properties:
            deck_id:
              type: integer
              example: 1
              description: ID bộ thẻ ôn tập
            user_id:
              type: integer
              example: 1
              description: ID người dùng tham gia học
    responses:
      201:
        description: Khởi tạo phiên học thành công
      400:
        description: Thiếu dữ liệu
      404:
        description: Không tìm thấy bộ thẻ hoặc người dùng
      500:
        description: Lỗi máy chủ
    """
    data: dict[str, Any] = request.get_json(silent=True) or {}
    deck_id = data.get("deck_id")
    user_id = data.get("user_id")

    if not deck_id or not user_id:
        return jsonify({"error": "Trường 'deck_id' và 'user_id' là bắt buộc"}), 400

    try:
        deck_id = int(deck_id)
        user_id = int(user_id)
    except (ValueError, TypeError):
        return jsonify({"error": "deck_id và user_id phải là số nguyên"}), 400

    deck = db.session.get(Deck, deck_id)
    if not deck:
        return jsonify({"error": f"Không tìm thấy bộ thẻ ID {deck_id}"}), 404

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": f"Không tìm thấy người dùng ID {user_id}"}), 404

    session = StudySession(
        deck_id=deck_id,
        user_id=user_id,
        started_at=datetime.now(timezone.utc).replace(tzinfo=None),
        total_reviewed=0,
    )

    try:
        db.session.add(session)
        db.session.commit()
        resp_data = session.to_dict()
        resp_data["session_id"] = session.id
        resp_data["session"] = session.to_dict()
        resp_data["message"] = "Bắt đầu phiên học thành công"
        return jsonify(resp_data), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi khởi tạo phiên học: {str(exc)}"}), 500


def get_study_session_by_id(session_id: int):
    """
    Lấy chi tiết một phiên học (GET /api/study/sessions/{session_id})
    ---
    tags:
      - Study & SRS Reviews
    summary: Lấy chi tiết phiên học theo ID
    parameters:
      - name: session_id
        in: path
        type: integer
        required: true
        description: ID phiên học
    responses:
      200:
        description: Thông tin chi tiết phiên học
      404:
        description: Không tìm thấy phiên học
    """
    session = db.session.get(StudySession, session_id)
    if not session:
        return jsonify({"error": f"Không tìm thấy phiên học với ID {session_id}"}), 404
    return jsonify(session.to_dict()), 200


def end_study_session(session_id: int):
    """
    Kết thúc phiên học (PUT /api/study/sessions/{session_id}/end)
    ---
    tags:
      - Study & SRS Reviews
    summary: Kết thúc phiên học (cập nhật ended_at và total_reviewed)
    parameters:
      - name: session_id
        in: path
        type: integer
        required: true
        description: ID phiên học
      - name: body
        in: body
        required: false
        schema:
          type: object
          properties:
            total_reviewed:
              type: integer
              example: 15
              description: Tổng số thẻ đã hoàn thành trong phiên học
    responses:
      200:
        description: Kết thúc phiên học thành công
      404:
        description: Không tìm thấy phiên học
      500:
        description: Lỗi máy chủ
    """
    session = db.session.get(StudySession, session_id)
    if not session:
        return jsonify({"error": f"Không tìm thấy phiên học với ID {session_id}"}), 404

    data = request.get_json(silent=True) or {}
    session.ended_at = datetime.now(timezone.utc).replace(tzinfo=None)
    if "total_reviewed" in data:
        try:
            session.total_reviewed = int(data["total_reviewed"])
        except (ValueError, TypeError):
            pass

    try:
        db.session.commit()
        resp_data = session.to_dict()
        resp_data["message"] = "Đã kết thúc phiên học"
        resp_data["session"] = session.to_dict()
        return jsonify(resp_data), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi cập nhật phiên học: {str(exc)}"}), 500


def list_study_sessions():
    """
    Danh sách các phiên học (GET /api/study/sessions)
    ---
    tags:
      - Study & SRS Reviews
    summary: Lấy danh sách lịch sử các phiên học (lọc theo ?user_id=, ?deck_id=)
    parameters:
      - name: user_id
        in: query
        type: integer
        required: false
        description: Lọc theo người dùng
      - name: deck_id
        in: query
        type: integer
        required: false
        description: Lọc theo bộ thẻ
    responses:
      200:
        description: Danh sách các phiên học
      500:
        description: Lỗi truy vấn
    """
    user_id = request.args.get("user_id", type=int)
    deck_id = request.args.get("deck_id", type=int)

    query = StudySession.query
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    if deck_id is not None:
        query = query.filter_by(deck_id=deck_id)

    sessions = query.order_by(StudySession.started_at.desc()).all()
    return jsonify([s.to_dict() for s in sessions]), 200


def delete_study_session_by_id(session_id: int):
    """
    Xóa phiên học (DELETE /api/study/sessions/{session_id})
    ---
    tags:
      - Study & SRS Reviews
    summary: Xóa một phiên học
    parameters:
      - name: session_id
        in: path
        type: integer
        required: true
        description: ID phiên học cần xóa
    responses:
      200:
        description: Xóa phiên học thành công
      404:
        description: Không tìm thấy phiên học
      500:
        description: Lỗi máy chủ
    """
    session = db.session.get(StudySession, session_id)
    if not session:
        return jsonify({"error": f"Không tìm thấy phiên học với ID {session_id}"}), 404

    try:
        db.session.delete(session)
        db.session.commit()
        return jsonify({"message": f"Đã xóa phiên học ID {session_id} thành công"}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi xóa phiên học: {str(exc)}"}), 500


def register_session_routes(bp: Blueprint) -> None:
    bp.add_url_rule("/sessions", view_func=start_study_session, methods=["POST"])
    bp.add_url_rule("/sessions/<int:session_id>", view_func=get_study_session_by_id, methods=["GET"])
    bp.add_url_rule("/sessions/<int:session_id>/end", view_func=end_study_session, methods=["PUT"])
    bp.add_url_rule("/sessions", view_func=list_study_sessions, methods=["GET"])
    bp.add_url_rule("/sessions/<int:session_id>", view_func=delete_study_session_by_id, methods=["DELETE"])
