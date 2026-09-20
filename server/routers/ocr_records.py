from datetime import datetime, timezone

from flask import request
from flask_restx import Namespace, Resource, fields
from sqlalchemy import func
from sqlmodel import select

from server.core.common_models import count_model, message_model
from server.core.security import admin_required, token_required
from server.database import get_db_session
from server.models.ocr_record import OCRRecord

ns_records = Namespace("System Records CRUD & Stats", path="/api/v1/ocr-records", description="Full CRUD and stats for OCR records")
ns_records.add_model("CountResponse", count_model)
ns_records.add_model("MessageResponse", message_model)

record_create_model = ns_records.model("OCRRecordCreateRequest", {
    "user_id": fields.Integer(required=False, description="Owner user ID (optional, defaults to current user)"),
    "image_url": fields.String(required=True, description="Target image URI"),
    "raw_detected_text": fields.String(required=True, description="Extracted detected text"),
    "ocr_json_data": fields.String(default="[]", description="JSON serialized detection data"),
    "audio_url": fields.String(default="", description="Synthesized audio URL"),
    "status": fields.String(default="pending", description="Status: pending, approved, rejected")
})

record_update_model = ns_records.model("OCRRecordUpdateRequest", {
    "raw_detected_text": fields.String(description="Detected text content"),
    "audio_url": fields.String(description="Synthesized audio URL"),
    "status": fields.String(description="Status: pending, approved, rejected")
})

record_model = ns_records.model("OCRRecordDetail", {
    "id": fields.Integer,
    "user_id": fields.Integer,
    "image_url": fields.String,
    "raw_detected_text": fields.String,
    "ocr_json_data": fields.String,
    "audio_url": fields.String,
    "status": fields.String,
    "created_at": fields.String
})


@ns_records.route("/count")
class OCRRecordCount(Resource):
    @ns_records.doc("count_records", description="Count OCR detection records with optional status/user filtering")
    @ns_records.param("status", "Status filter (pending, approved, rejected)", type=str)
    @ns_records.param("user_id", "Filter by user ID", type=int)
    @ns_records.response(200, "Success", count_model)
    def get(self):
        status_filter = request.args.get("status")
        user_id = request.args.get("user_id", type=int)

        with get_db_session() as session:
            stmt = select(func.count(OCRRecord.id))
            if status_filter:
                stmt = stmt.where(OCRRecord.status == status_filter)
            if user_id:
                stmt = stmt.where(OCRRecord.user_id == user_id)
            count = session.exec(stmt).one()
            return {"count": count}, 200


@ns_records.route("")
class OCRRecordListCreate(Resource):
    @ns_records.doc("list_records", description="Retrieve paginated OCR records")
    @ns_records.param("user_id", "Filter by user ID", type=int)
    @ns_records.param("status", "Filter by status", type=str)
    @ns_records.param("limit", "Page size", type=int, default=10)
    @ns_records.param("skip", "Offset", type=int, default=0)
    @ns_records.response(200, "Success", [record_model])
    def get(self):
        user_id = request.args.get("user_id", type=int)
        status_filter = request.args.get("status")
        limit = request.args.get("limit", default=10, type=int)
        skip = request.args.get("skip", default=0, type=int)

        with get_db_session() as session:
            stmt = select(OCRRecord)
            if user_id:
                stmt = stmt.where(OCRRecord.user_id == user_id)
            if status_filter:
                stmt = stmt.where(OCRRecord.status == status_filter)
            stmt = stmt.order_by(OCRRecord.id.desc()).offset(skip).limit(limit)

            records = session.exec(stmt).all()
            return [
                {
                    "id": r.id,
                    "user_id": r.user_id,
                    "image_url": r.image_url,
                    "raw_detected_text": r.raw_detected_text,
                    "ocr_json_data": r.ocr_json_data,
                    "audio_url": r.audio_url,
                    "status": r.status,
                    "created_at": r.created_at.isoformat() if hasattr(r.created_at, "isoformat") else str(r.created_at)
                } for r in records
            ], 200

    @ns_records.doc("create_record", security="Bearer", description="Manually insert an OCR record")
    @ns_records.expect(record_create_model, validate=True)
    @ns_records.response(201, "Record created", record_model)
    @token_required
    def post(self, current_user: dict):
        data = request.json or {}
        with get_db_session() as session:
            record = OCRRecord(
                user_id=int(data.get("user_id", current_user["id"])),
                image_url=data["image_url"],
                raw_detected_text=data["raw_detected_text"],
                ocr_json_data=data.get("ocr_json_data", "[]"),
                audio_url=data.get("audio_url", ""),
                status=data.get("status", "pending"),
                created_at=datetime.now(timezone.utc)
            )
            session.add(record)
            session.commit()
            session.refresh(record)

            return {
                "id": record.id,
                "user_id": record.user_id,
                "image_url": record.image_url,
                "raw_detected_text": record.raw_detected_text,
                "ocr_json_data": record.ocr_json_data,
                "audio_url": record.audio_url,
                "status": record.status,
                "created_at": record.created_at.isoformat() if hasattr(record.created_at, "isoformat") else str(record.created_at)
            }, 201


@ns_records.route("/<int:record_id>")
class OCRRecordDetail(Resource):
    @ns_records.doc("get_record", description="Get OCR record details by ID")
    @ns_records.response(200, "Success", record_model)
    @ns_records.response(404, "Record not found")
    def get(self, record_id: int):
        with get_db_session() as session:
            record = session.get(OCRRecord, record_id)
            if not record:
                return {"detail": f"Record ID {record_id} not found."}, 404
            return {
                "id": record.id,
                "user_id": record.user_id,
                "image_url": record.image_url,
                "raw_detected_text": record.raw_detected_text,
                "ocr_json_data": record.ocr_json_data,
                "audio_url": record.audio_url,
                "status": record.status,
                "created_at": record.created_at.isoformat() if hasattr(record.created_at, "isoformat") else str(record.created_at)
            }, 200

    @ns_records.doc("update_record", security="Bearer", description="Update record text, audio, or status")
    @ns_records.expect(record_update_model, validate=True)
    @ns_records.response(200, "Record updated", record_model)
    @ns_records.response(404, "Record not found")
    @admin_required
    def put(self, record_id: int, current_user: dict):
        data = request.json or {}
        with get_db_session() as session:
            record = session.get(OCRRecord, record_id)
            if not record:
                return {"detail": f"Record ID {record_id} not found."}, 404

            if "raw_detected_text" in data and data["raw_detected_text"] is not None:
                record.raw_detected_text = data["raw_detected_text"]
            if "audio_url" in data and data["audio_url"] is not None:
                record.audio_url = data["audio_url"]
            if "status" in data and data["status"] is not None:
                record.status = data["status"]

            session.commit()
            session.refresh(record)

            return {
                "id": record.id,
                "user_id": record.user_id,
                "image_url": record.image_url,
                "raw_detected_text": record.raw_detected_text,
                "ocr_json_data": record.ocr_json_data,
                "audio_url": record.audio_url,
                "status": record.status,
                "created_at": record.created_at.isoformat() if hasattr(record.created_at, "isoformat") else str(record.created_at)
            }, 200

    @ns_records.doc("delete_record", security="Bearer", description="Delete OCR record by ID")
    @ns_records.response(200, "Record deleted", message_model)
    @ns_records.response(404, "Record not found")
    @admin_required
    def delete(self, record_id: int, current_user: dict):
        with get_db_session() as session:
            record = session.get(OCRRecord, record_id)
            if not record:
                return {"detail": f"Record ID {record_id} not found."}, 404
            session.delete(record)
            session.commit()
            return {"message": f"Record ID {record_id} deleted successfully.", "success": True}, 200
