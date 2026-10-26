"""
ai_logs.py — AI Generation Logs CRUD API endpoints (Table 10: ai_generation_logs).
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.study import AIGenerationLog

ai_logs_bp = Blueprint("ai_logs", __name__, url_prefix="/api/ai-logs")


@ai_logs_bp.route("", methods=["GET"])
def list_ai_logs():
    """Lấy danh sách nhật ký AI Pipeline"""
    user_id = request.args.get("user_id", type=int)
    document_id = request.args.get("document_id", type=int)
    deck_id = request.args.get("deck_id", type=int)
    status = request.args.get("status")
    query = AIGenerationLog.query
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    if document_id is not None:
        query = query.filter_by(document_id=document_id)
    if deck_id is not None:
        query = query.filter_by(deck_id=deck_id)
    if status is not None:
        query = query.filter_by(status=status)
    logs = query.order_by(AIGenerationLog.id.desc()).all()
    return jsonify([l.to_dict() for l in logs]), 200


@ai_logs_bp.route("", methods=["POST"])
def create_ai_log():
    """Tạo bản ghi nhật ký tiến trình sinh thẻ AI"""
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Trường 'user_id' là bắt buộc"}), 400
    log = AIGenerationLog(
        user_id=user_id,
        document_id=data.get("document_id"),
        deck_id=data.get("deck_id"),
        model_name=data.get("model_name", "qwen2.5-0.5b"),
        cards_generated=int(data.get("cards_generated", 0)),
        inference_time_seconds=float(data.get("inference_time_seconds", 0.0)),
        prompt_tokens=int(data.get("prompt_tokens", 0)),
        completion_tokens=int(data.get("completion_tokens", 0)),
        status=data.get("status", "SUCCESS"),
        error_message=data.get("error_message"),
    )
    db.session.add(log)
    db.session.commit()
    return jsonify(log.to_dict()), 201


@ai_logs_bp.route("/<int:log_id>", methods=["GET"])
def get_ai_log_by_id(log_id: int):
    """Lấy chi tiết một bản ghi nhật ký AI"""
    log = db.session.get(AIGenerationLog, log_id)
    if not log:
        return jsonify({"error": f"Không tìm thấy nhật ký AI ID {log_id}"}), 404
    return jsonify(log.to_dict()), 200


@ai_logs_bp.route("/<int:log_id>", methods=["PUT"])
def update_ai_log_by_id(log_id: int):
    """Cập nhật nhật ký AI"""
    log = db.session.get(AIGenerationLog, log_id)
    if not log:
        return jsonify({"error": f"Không tìm thấy nhật ký AI ID {log_id}"}), 404
    data = request.get_json(silent=True) or {}
    if "status" in data:
        log.status = data["status"]
    if "error_message" in data:
        log.error_message = data["error_message"]
    if "cards_generated" in data:
        log.cards_generated = int(data["cards_generated"])
    db.session.commit()
    return jsonify(log.to_dict()), 200


@ai_logs_bp.route("/<int:log_id>", methods=["DELETE"])
def delete_ai_log_by_id(log_id: int):
    """Xóa nhật ký AI"""
    log = db.session.get(AIGenerationLog, log_id)
    if not log:
        return jsonify({"error": f"Không tìm thấy nhật ký AI ID {log_id}"}), 404
    db.session.delete(log)
    db.session.commit()
    return jsonify({"message": f"Đã xóa nhật ký AI ID {log_id} thành công"}), 200
