import json
from datetime import datetime, timezone

from flask import request
from flask_restx import Namespace, Resource, fields
from sqlalchemy import func
from sqlalchemy.orm import defer
from sqlmodel import select

from server.core.common_models import count_model, message_model
from server.core.pipeline_client import fetch_media_bytes
from server.core.security import admin_required, token_required
from server.database import get_db_session
from server.models.ocr_record import OCRRecord

ns_records = Namespace("System Records CRUD & Stats", path="/api/v1/ocr-records", description="Full CRUD and stats for OCR records")
ns_records.add_model("CountResponse", count_model)
ns_records.add_model("MessageResponse", message_model)

record_create_model = ns_records.model("OCRRecordCreateRequest", {
    "user_id": fields.String(required=False, description="Owner user ID (optional, defaults to current user)"),
    "image_url": fields.String(required=False, description="Target image URI or URL"),
    "raw_detected_text": fields.String(required=True, description="Extracted detected text"),
    "ocr_json_data": fields.Raw(default=[], description="JSON serialized detection data or array of objects"),
    "audio_url": fields.String(default="", description="Synthesized audio URL"),
    "status": fields.String(default="pending", description="Status: pending, approved, rejected")
})

record_update_model = ns_records.model("OCRRecordUpdateRequest", {
    "raw_detected_text": fields.String(description="Detected text content"),
    "ocr_json_data": fields.Raw(description="JSON serialized detection data or array of objects"),
    "audio_url": fields.String(description="Synthesized audio URL"),
    "status": fields.String(description="Status: pending, approved, rejected")
})

record_patch_model = ns_records.model("OCRRecordPatchRequest", {
    "raw_detected_text": fields.String(description="Detected text content"),
    "ocr_json_data": fields.Raw(description="JSON serialized detection data or array of objects"),
    "audio_url": fields.String(description="Synthesized audio URL"),
    "status": fields.String(description="Status: pending, approved, rejected")
})

record_status_patch_model = ns_records.model("OCRRecordStatusPatchRequest", {
    "status": fields.String(required=True, description="Status: pending, approved, rejected")
})

record_stats_model = ns_records.model("OCRRecordStatsResponse", {
    "total_records": fields.Integer,
    "pending_records": fields.Integer,
    "approved_records": fields.Integer,
    "rejected_records": fields.Integer
})

record_model = ns_records.model("OCRRecordDetail", {
    "id": fields.String,
    "user_id": fields.String,
    "image_url": fields.String,
    "summary": fields.String,
    "raw_detected_text": fields.String,
    "objects": fields.Raw,
    "json_data": fields.Raw,
    "ocr_json_data": fields.Raw,
    "audio_url": fields.String,
    "status": fields.String,
    "created_at": fields.String
})


def serialize_ocr_record(r: OCRRecord) -> dict:
    """Standardized serializer ensuring parsed object array and streaming URLs from SQLite BLOB."""
    parsed_json = []
    if r.ocr_json_data:
        if isinstance(r.ocr_json_data, str):
            try:
                parsed_json = json.loads(r.ocr_json_data)
            except Exception:
                parsed_json = r.ocr_json_data
        else:
            parsed_json = r.ocr_json_data

    return {
        "id": r.id,
        "user_id": r.user_id,
        "image_url": f"/api/v1/media/records/{r.id}/image",
        "summary": r.raw_detected_text,
        "raw_detected_text": r.raw_detected_text,
        "objects": parsed_json,
        "json_data": parsed_json,
        "ocr_json_data": parsed_json,
        "audio_url": f"/api/v1/media/records/{r.id}/audio",
        "status": r.status,
        "created_at": r.created_at.isoformat() if hasattr(r.created_at, "isoformat") else str(r.created_at)
    }


@ns_records.route("/count")
class OCRRecordCount(Resource):
    @ns_records.doc("count_records", description="Count OCR detection records with optional status/user filtering")
    @ns_records.param("status", "Status filter (pending, approved, rejected)", type=str)
    @ns_records.param("user_id", "Filter by user ID", type=str)
    @ns_records.response(200, "Success", count_model)
    def get(self):
        status_filter = request.args.get("status")
        user_id = request.args.get("user_id", type=str)

        with get_db_session() as session:
            stmt = select(func.count(OCRRecord.id))
            if status_filter:
                stmt = stmt.where(OCRRecord.status == status_filter)
            if user_id:
                stmt = stmt.where(OCRRecord.user_id == user_id)
            count = session.exec(stmt).one()
            return {"count": count}, 200


@ns_records.route("/stats")
class OCRRecordStats(Resource):
    @ns_records.doc("get_record_stats", description="Get OCR record count statistics grouped by status")
    @ns_records.response(200, "Success", record_stats_model)
    def get(self):
        with get_db_session() as session:
            all_records = session.exec(select(OCRRecord.status)).all()
            total = len(all_records)
            pending = sum(1 for s in all_records if s == "pending")
            approved = sum(1 for s in all_records if s == "approved")
            rejected = sum(1 for s in all_records if s == "rejected")
            return {
                "total_records": total,
                "pending_records": pending,
                "approved_records": approved,
                "rejected_records": rejected
            }, 200


@ns_records.route("")
class OCRRecordListCreate(Resource):
    @ns_records.doc("list_records", description="Retrieve paginated OCR records with deferred BLOB loading")
    @ns_records.param("user_id", "Filter by user ID", type=str)
    @ns_records.param("status", "Filter by status", type=str)
    @ns_records.param("limit", "Page size", type=int, default=10)
    @ns_records.param("skip", "Offset", type=int, default=0)
    @ns_records.response(200, "Success", [record_model])
    def get(self):
        user_id = request.args.get("user_id", type=str)
        status_filter = request.args.get("status")
        limit = request.args.get("limit", default=10, type=int)
        skip = request.args.get("skip", default=0, type=int)

        with get_db_session() as session:
            # Defend against memory bloat by deferring large BLOB columns
            stmt = (
                select(OCRRecord)
                .options(
                    defer(OCRRecord.raw_image_data),
                    defer(OCRRecord.annotated_image_data),
                    defer(OCRRecord.audio_data)
                )
            )
            if user_id:
                stmt = stmt.where(OCRRecord.user_id == user_id)
            if status_filter:
                stmt = stmt.where(OCRRecord.status == status_filter)
            stmt = stmt.order_by(OCRRecord.id.desc()).offset(skip).limit(limit)

            records = session.exec(stmt).all()
            return [serialize_ocr_record(r) for r in records], 200

    @ns_records.doc("create_record", security="Bearer", description="Manually insert an OCR record")
    @ns_records.expect(record_create_model, validate=False)
    @ns_records.response(201, "Record created", record_model)
    @token_required
    def post(self, current_user: dict):
        data = request.json or {}
        raw_json_input = data.get("ocr_json_data", "[]")
        if not isinstance(raw_json_input, str):
            raw_json_input = json.dumps(raw_json_input, ensure_ascii=False)

        raw_img_bytes = b""
        if "raw_image_data" in data and data["raw_image_data"]:
            val = data["raw_image_data"]
            raw_img_bytes = val.encode("utf-8") if isinstance(val, str) else bytes(val)
        elif "image_url" in data and data["image_url"]:
            raw_img_bytes = fetch_media_bytes(data["image_url"])

        audio_bytes = b""
        if "audio_data" in data and data["audio_data"]:
            val = data["audio_data"]
            audio_bytes = val.encode("utf-8") if isinstance(val, str) else bytes(val)
        elif "audio_url" in data and data["audio_url"]:
            audio_bytes = fetch_media_bytes(data["audio_url"])

        with get_db_session() as session:
            record = OCRRecord(
                user_id=str(data.get("user_id") or current_user["id"]),
                raw_image_data=raw_img_bytes or b"\xff\xd8\xff\xe0" + b"\x00" * 32,
                raw_image_mime=data.get("raw_image_mime", "image/jpeg"),
                annotated_image_data=raw_img_bytes or None,
                annotated_image_mime=data.get("annotated_image_mime", "image/jpeg"),
                raw_detected_text=data.get("raw_detected_text", ""),
                ocr_json_data=raw_json_input,
                audio_data=audio_bytes or b"\x00" * 16,
                audio_mime=data.get("audio_mime", "audio/mpeg"),
                status=data.get("status", "pending"),
                created_at=datetime.now(timezone.utc)
            )
            session.add(record)
            session.commit()
            session.refresh(record)

            return serialize_ocr_record(record), 201


@ns_records.route("/<string:record_id>")
class OCRRecordDetail(Resource):
    @ns_records.doc("get_record", description="Get OCR record details by ID")
    @ns_records.response(200, "Success", record_model)
    @ns_records.response(404, "Record not found")
    def get(self, record_id: str):
        with get_db_session() as session:
            record = session.get(OCRRecord, record_id)
            if not record:
                return {"detail": f"Record ID {record_id} not found."}, 404
            return serialize_ocr_record(record), 200

    @ns_records.doc("update_record", security="Bearer", description="Update record text, audio, or status")
    @ns_records.expect(record_update_model, validate=False)
    @ns_records.response(200, "Record updated", record_model)
    @ns_records.response(404, "Record not found")
    @admin_required
    def put(self, record_id: str, current_user: dict):
        data = request.json or {}
        with get_db_session() as session:
            record = session.get(OCRRecord, record_id)
            if not record:
                return {"detail": f"Record ID {record_id} not found."}, 404

            if "raw_detected_text" in data and data["raw_detected_text"] is not None:
                record.raw_detected_text = data["raw_detected_text"]
            if "ocr_json_data" in data and data["ocr_json_data"] is not None:
                new_json = data["ocr_json_data"]
                record.ocr_json_data = new_json if isinstance(new_json, str) else json.dumps(new_json, ensure_ascii=False)
            if "audio_url" in data and data["audio_url"] is not None:
                record.audio_url = data["audio_url"]
            if "status" in data and data["status"] is not None:
                record.status = data["status"]

            session.commit()
            session.refresh(record)

            return serialize_ocr_record(record), 200

    @ns_records.doc("patch_record", security="Bearer", description="Partially update record text, status, or json")
    @ns_records.expect(record_patch_model, validate=False)
    @ns_records.response(200, "Record updated", record_model)
    @ns_records.response(404, "Record not found")
    @admin_required
    def patch(self, record_id: str, current_user: dict):
        data = request.json or {}
        with get_db_session() as session:
            record = session.get(OCRRecord, record_id)
            if not record:
                return {"detail": f"Record ID {record_id} not found."}, 404

            if "raw_detected_text" in data and data["raw_detected_text"] is not None:
                record.raw_detected_text = data["raw_detected_text"]
            if "ocr_json_data" in data and data["ocr_json_data"] is not None:
                new_json = data["ocr_json_data"]
                record.ocr_json_data = new_json if isinstance(new_json, str) else json.dumps(new_json, ensure_ascii=False)
            if "audio_url" in data and data["audio_url"] is not None:
                record.audio_url = data["audio_url"]
            if "status" in data and data["status"] is not None:
                record.status = data["status"]

            session.commit()
            session.refresh(record)

            return serialize_ocr_record(record), 200

    @ns_records.doc("delete_record", security="Bearer", description="Delete OCR record by ID")
    @ns_records.response(200, "Record deleted", message_model)
    @ns_records.response(404, "Record not found")
    @admin_required
    def delete(self, record_id: str, current_user: dict):
        with get_db_session() as session:
            record = session.get(OCRRecord, record_id)
            if not record:
                return {"detail": f"Record ID {record_id} not found."}, 404
            session.delete(record)
            session.commit()
            return {"message": f"Record ID {record_id} deleted successfully.", "success": True}, 200


@ns_records.route("/<string:record_id>/status")
class OCRRecordStatusResource(Resource):
    @ns_records.doc("patch_record_status", security="Bearer", description="Quickly update OCR record status (pending, approved, rejected)")
    @ns_records.expect(record_status_patch_model, validate=True)
    @ns_records.response(200, "Status updated", record_model)
    @ns_records.response(400, "Invalid status")
    @ns_records.response(404, "Record not found")
    @admin_required
    def patch(self, record_id: str, current_user: dict):
        data = request.json or {}
        new_status = data.get("status", "").strip().lower()
        if new_status not in ("pending", "approved", "rejected"):
            return {"detail": "Trạng thái chỉ có thể là: pending, approved, rejected."}, 400

        with get_db_session() as session:
            record = session.get(OCRRecord, record_id)
            if not record:
                return {"detail": f"Record ID {record_id} not found."}, 404

            record.status = new_status
            session.commit()
            session.refresh(record)
            return serialize_ocr_record(record), 200
