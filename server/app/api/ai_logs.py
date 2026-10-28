"""
ai_logs.py — AI Generation Logs CRUD API endpoints (Tag: AI Logs).
Quản lý thực thể: ai_generation_logs (Table 10).
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from app.core.database import db
from app.models.study import AIGenerationLog

ai_logs_bp = Blueprint("ai_logs", __name__, url_prefix="/api/ai-logs")


@ai_logs_bp.route("", methods=["GET"])
def list_ai_logs():
    """
    Xem lịch sử sinh thẻ từ AI Pipeline (GET /api/ai-logs)
    ---
    tags:
      - AI Logs
    summary: Xem lịch sử sinh thẻ từ AI (lọc theo ?user_id=, ?document_id=, ?deck_id=, ?status=SUCCESS|FAILED)
    description: Hiển thị đầy đủ metrics inference_time_seconds, prompt_tokens, completion_tokens, cards_generated
    parameters:
      - name: user_id
        in: query
        type: integer
        required: false
        description: Lọc theo ID người dùng
      - name: document_id
        in: query
        type: integer
        required: false
        description: Lọc theo ID tài liệu nguồn
      - name: deck_id
        in: query
        type: integer
        required: false
        description: Lọc theo ID bộ thẻ đích
      - name: status
        in: query
        type: string
        required: false
        description: Lọc theo trạng thái (SUCCESS, FAILED)
    responses:
      200:
        description: Danh sách telemetry logs sinh thẻ từ AI
      500:
        description: Lỗi máy chủ
    """
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


@ai_logs_bp.route("/<int:log_id>", methods=["GET"])
def get_ai_log_by_id(log_id: int):
    """
    Xem chi tiết một log sinh thẻ (GET /api/ai-logs/{id})
    ---
    tags:
      - AI Logs
    summary: Xem chi tiết một log sinh thẻ (kèm error_message nếu có)
    parameters:
      - name: log_id
        in: path
        type: integer
        required: true
        description: ID bản ghi log
    responses:
      200:
        description: Chi tiết log sinh thẻ
      404:
        description: Không tìm thấy log
    """
    log = db.session.get(AIGenerationLog, log_id)
    if not log:
        return jsonify({"error": f"Không tìm thấy nhật ký AI ID {log_id}"}), 404
    return jsonify(log.to_dict()), 200


@ai_logs_bp.route("/<int:log_id>", methods=["DELETE"])
def delete_ai_log_by_id(log_id: int):
    """
    Xóa một bản ghi nhật ký AI (DELETE /api/ai-logs/{id})
    ---
    tags:
      - AI Logs
    summary: Xóa log bản ghi AI
    parameters:
      - name: log_id
        in: path
        type: integer
        required: true
        description: ID log cần xóa
    responses:
      200:
        description: Đã xóa log bản ghi thành công
      404:
        description: Không tìm thấy log
      500:
        description: Lỗi xóa
    """
    log = db.session.get(AIGenerationLog, log_id)
    if not log:
        return jsonify({"error": f"Không tìm thấy nhật ký AI ID {log_id}"}), 404

    try:
        db.session.delete(log)
        db.session.commit()
        return jsonify({"message": f"Đã xóa nhật ký AI ID {log_id} thành công"}), 200
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi xóa nhật ký AI: {str(exc)}"}), 500


@ai_logs_bp.route("", methods=["POST"])
def create_ai_log():
    """
    Tạo thủ công một bản ghi telemetry AI Log (POST /api/ai-logs)
    ---
    tags:
      - AI Logs
    summary: Ghi nhận nhật ký tiến trình sinh thẻ AI
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - user_id
          properties:
            user_id:
              type: integer
              example: 1
            document_id:
              type: integer
              example: 1
            deck_id:
              type: integer
              example: 1
            model_name:
              type: string
              example: "flan-t5-base"
            cards_generated:
              type: integer
              example: 5
            inference_time_seconds:
              type: number
              example: 1.25
            prompt_tokens:
              type: integer
              example: 120
            completion_tokens:
              type: integer
              example: 45
            status:
              type: string
              example: "SUCCESS"
            error_message:
              type: string
              example: null
    responses:
      201:
        description: Tạo log thành công
      400:
        description: Thiếu user_id
      500:
        description: Lỗi máy chủ
    """
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Trường 'user_id' là bắt buộc"}), 400

    try:
        user_id = int(user_id)
        doc_id = int(data["document_id"]) if data.get("document_id") else None
        deck_id = int(data["deck_id"]) if data.get("deck_id") else None
    except (ValueError, TypeError):
        return jsonify({"error": "ID phải là số nguyên"}), 400

    log = AIGenerationLog(
        user_id=user_id,
        document_id=doc_id,
        deck_id=deck_id,
        model_name=data.get("model_name", "flan-t5-base"),
        cards_generated=int(data.get("cards_generated", 0)),
        inference_time_seconds=float(data.get("inference_time_seconds", 0.0)),
        prompt_tokens=int(data.get("prompt_tokens", 0)),
        completion_tokens=int(data.get("completion_tokens", 0)),
        status=data.get("status", "SUCCESS"),
        error_message=data.get("error_message"),
    )
    try:
        db.session.add(log)
        db.session.commit()
        return jsonify(log.to_dict()), 201
    except Exception as exc:
        db.session.rollback()
        return jsonify({"error": f"Lỗi tạo nhật ký AI: {str(exc)}"}), 500
