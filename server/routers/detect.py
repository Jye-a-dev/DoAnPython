import json
from datetime import datetime, timezone

from flask import Response, request, send_from_directory
from flask_restx import Namespace, Resource, fields, reqparse
from sqlmodel import select
from werkzeug.datastructures import FileStorage

from server.core.config import AUDIO_DIR, PIPELINE_SERVICE_URL, UPLOADS_DIR
from server.core.pipeline_client import (
    PipelineExecutionError,
    PipelineTimeoutError,
    PipelineUnavailableError,
    call_pipeline_inference,
    http_client,
)
from server.database import get_db_session
from server.models.ocr_record import OCRRecord
from server.models.user import User

ns_detect = Namespace("Object Detection & History", path="/api/v1", description="Inference dispatch and logs")
ns_static = Namespace("Static Serving", path="/static", description="Direct asset delivery")

bounding_box_model = ns_detect.model("BoundingBox", {
    "xmin": fields.Float,
    "ymin": fields.Float,
    "xmax": fields.Float,
    "ymax": fields.Float
})

object_item_model = ns_detect.model("ObjectItem", {
    "name": fields.String,
    "label_vi": fields.String,
    "confidence": fields.Float,
    "box": fields.Nested(bounding_box_model)
})

detection_result_model = ns_detect.model("DetectionResult", {
    "id": fields.Integer,
    "user_id": fields.Integer,
    "summary": fields.String,
    "objects": fields.List(fields.Nested(object_item_model)),
    "image_url": fields.String,
    "audio_url": fields.String,
    "status": fields.String,
    "created_at": fields.String
})

record_model = ns_detect.model("OCRRecordItem", {
    "id": fields.Integer,
    "user_id": fields.Integer,
    "image_url": fields.String,
    "raw_detected_text": fields.String,
    "ocr_json_data": fields.String,
    "audio_url": fields.String,
    "status": fields.String,
    "created_at": fields.String
})

detect_parser = reqparse.RequestParser()
detect_parser.add_argument("file", location="files", type=FileStorage, required=False, help="Target image file (JPG, PNG, WEBP)")
detect_parser.add_argument("image", location="files", type=FileStorage, required=False, help="Alias image file")
detect_parser.add_argument("user_id", location="form", type=int, default=1, help="Associated User ID")


@ns_detect.route("/detect")
class DetectEndpoint(Resource):
    @ns_detect.doc("detect_objects", description="Upload image, verify magic bytes, dispatch directly to pipeline, and persist record")
    @ns_detect.expect(detect_parser)
    @ns_detect.response(200, "Detection successful", detection_result_model)
    @ns_detect.response(400, "Invalid image format")
    @ns_detect.response(422, "Pipeline unprocessable image entity")
    @ns_detect.response(503, "AI Pipeline unavailable")
    @ns_detect.response(504, "AI Pipeline timeout")
    def post(self):
        uploaded_file = request.files.get("file") or request.files.get("image")
        if not uploaded_file:
            return {"detail": "Vui lòng đính kèm tệp ảnh (form-data: 'file' hoặc 'image')."}, 400

        user_id = request.form.get("user_id", default=1, type=int)

        header = uploaded_file.read(12)
        uploaded_file.seek(0)
        is_valid_image = (
            header.startswith(b"\xff\xd8\xff") or
            header.startswith(b"\x89PNG\r\n\x1a\n") or
            (header.startswith(b"RIFF") and b"WEBP" in header)
        )
        if not is_valid_image:
            return {"detail": "Nội dung file không phải là ảnh hợp lệ (JPG, PNG, WEBP)."}, 400

        file_bytes = uploaded_file.read()
        filename = getattr(uploaded_file, "filename", "upload.jpg") or "upload.jpg"

        # Direct synchronous inference call with connection pooling & fine-grained timeouts
        try:
            pipeline_data = call_pipeline_inference(file_bytes, filename)
        except PipelineUnavailableError as pue:
            return {"detail": f"Service Unavailable: {str(pue)}"}, 503
        except PipelineTimeoutError as pte:
            return {"detail": f"Gateway Timeout: {str(pte)}"}, 504
        except PipelineExecutionError as pee:
            return {"detail": f"Pipeline processing failed: {str(pee)}"}, 422
        except Exception as ex:
            return {"detail": f"Internal server error: {str(ex)}"}, 500

        annotated_url = pipeline_data.get("annotated_image_url") or pipeline_data.get("image_url") or ""
        audio_url = pipeline_data.get("audio_url", "")
        summary = pipeline_data.get("summary", "")
        detected_objects = pipeline_data.get("objects", [])

        # SQLite Lock Isolation: DB transaction occurs post-inference only
        with get_db_session() as session:
            db_user = session.get(User, user_id)
            if not db_user:
                user_id = 1

            record = OCRRecord(
                user_id=user_id,
                image_url=annotated_url,
                raw_detected_text=summary,
                ocr_json_data=json.dumps(detected_objects, ensure_ascii=False),
                audio_url=audio_url,
                status="pending",
                created_at=datetime.now(timezone.utc)
            )
            session.add(record)
            session.commit()
            session.refresh(record)

            return {
                "id": record.id,
                "user_id": record.user_id,
                "summary": record.raw_detected_text,
                "objects": detected_objects,
                "image_url": record.image_url,
                "audio_url": record.audio_url,
                "status": record.status,
                "created_at": record.created_at.isoformat() if hasattr(record.created_at, "isoformat") else str(record.created_at)
            }, 200


@ns_detect.route("/history")
class DetectionHistory(Resource):
    @ns_detect.doc("get_history", description="Retrieve paginated detection history")
    @ns_detect.param("limit", "Number of records to fetch", type=int, default=10)
    @ns_detect.param("skip", "Number of records to skip", type=int, default=0)
    @ns_detect.response(200, "Success", [record_model])
    def get(self):
        limit = request.args.get("limit", default=10, type=int)
        skip = request.args.get("skip", default=0, type=int)
        with get_db_session() as session:
            statement = select(OCRRecord).order_by(OCRRecord.id.desc()).offset(skip).limit(limit)
            records = session.exec(statement).all()
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


@ns_static.route("/uploads/<path:filename>")
class ServeUploads(Resource):
    @ns_static.doc("serve_uploads", description="Serve raw and annotated images with pipeline fallback")
    def get(self, filename: str):
        local_path = UPLOADS_DIR / filename
        if local_path.is_file():
            return send_from_directory(str(UPLOADS_DIR), filename)

        # Fallback upstream proxy for multi-pod deployments without shared PV
        try:
            upstream_url = f"{PIPELINE_SERVICE_URL}/static/uploads/{filename}"
            resp = http_client.get(upstream_url)
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "image/jpeg")
                return Response(resp.content, content_type=content_type, status=200)
        except Exception:
            pass

        return {"detail": f"File '{filename}' not found."}, 404


@ns_static.route("/audio/<path:filename>")
class ServeAudio(Resource):
    @ns_static.doc("serve_audio", description="Stream synthesized MP3 speech files with pipeline fallback")
    def get(self, filename: str):
        local_path = AUDIO_DIR / filename
        if local_path.is_file():
            return send_from_directory(str(AUDIO_DIR), filename)

        # Fallback upstream proxy for multi-pod deployments without shared PV
        try:
            upstream_url = f"{PIPELINE_SERVICE_URL}/static/audio/{filename}"
            resp = http_client.get(upstream_url)
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "audio/mpeg")
                return Response(resp.content, content_type=content_type, status=200)
        except Exception:
            pass

        return {"detail": f"Audio file '{filename}' not found."}, 404


