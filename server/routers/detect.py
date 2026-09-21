import json
from datetime import datetime, timezone

from flask import Response, request, send_from_directory
from flask_restx import Namespace, Resource, fields, reqparse
from sqlalchemy import func
from sqlalchemy.orm import defer
from sqlmodel import select
from werkzeug.datastructures import FileStorage

from server.core.config import AUDIO_DIR, DEFAULT_USER_USER_ID, PIPELINE_SERVICE_URL, UPLOADS_DIR
from server.core.pipeline_client import (
    PipelineExecutionError,
    PipelineTimeoutError,
    PipelineUnavailableError,
    call_pipeline_inference,
    fetch_media_bytes,
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
    "id": fields.String,
    "user_id": fields.String,
    "summary": fields.String,
    "raw_detected_text": fields.String,
    "objects": fields.List(fields.Nested(object_item_model)),
    "json_data": fields.Raw,
    "ocr_json_data": fields.Raw,
    "image_url": fields.String,
    "annotated_image_url": fields.String,
    "audio_url": fields.String,
    "status": fields.String,
    "created_at": fields.String
})

record_model = ns_detect.model("OCRRecordItem", {
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

history_response_model = ns_detect.model("HistoryResponse", {
    "total": fields.Integer,
    "records": fields.List(fields.Nested(record_model))
})

detect_parser = reqparse.RequestParser()
detect_parser.add_argument("file", location="files", type=FileStorage, required=False, help="Target image file (JPG, PNG, WEBP)")
detect_parser.add_argument("image", location="files", type=FileStorage, required=False, help="Alias image file")
detect_parser.add_argument("user_id", location="form", type=str, default=DEFAULT_USER_USER_ID, help="Associated User ID")


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

        # Fetch binary media bytes from pipeline output for direct SQLite BLOB persistence
        annotated_image_bytes = fetch_media_bytes(annotated_url) if annotated_url else file_bytes
        audio_bytes = fetch_media_bytes(audio_url) if audio_url else b""
        mime_type = getattr(uploaded_file, "mimetype", "image/jpeg") or "image/jpeg"

        # SQLite Lock Isolation: DB transaction occurs post-inference only
        with get_db_session() as session:
            user_id_val = str(user_id) if user_id else DEFAULT_USER_USER_ID
            db_user = session.get(User, user_id_val)
            if not db_user:
                user_id_val = DEFAULT_USER_USER_ID

            record = OCRRecord(
                user_id=user_id_val,
                raw_image_data=file_bytes,
                raw_image_mime=mime_type,
                annotated_image_data=annotated_image_bytes,
                annotated_image_mime="image/jpeg",
                raw_detected_text=summary,
                ocr_json_data=json.dumps(detected_objects, ensure_ascii=False),
                audio_data=audio_bytes,
                audio_mime="audio/mpeg",
                status="pending",
                created_at=datetime.now(timezone.utc)
            )
            session.add(record)
            session.commit()
            session.refresh(record)

            stream_image_url = f"/api/v1/media/records/{record.id}/image"
            stream_audio_url = f"/api/v1/media/records/{record.id}/audio"

            return {
                "id": record.id,
                "user_id": record.user_id,
                "summary": record.raw_detected_text,
                "raw_detected_text": record.raw_detected_text,
                "objects": detected_objects,
                "json_data": detected_objects,
                "ocr_json_data": detected_objects,
                "image_url": stream_image_url,
                "annotated_image_url": stream_image_url,
                "audio_url": stream_audio_url,
                "status": record.status,
                "created_at": record.created_at.isoformat() if hasattr(record.created_at, "isoformat") else str(record.created_at)
            }, 200


@ns_detect.route("/history")
class DetectionHistory(Resource):
    @ns_detect.doc("get_history", description="Retrieve paginated detection history with deferred BLOB loading")
    @ns_detect.param("limit", "Number of records to fetch", type=int, default=10)
    @ns_detect.param("skip", "Number of records to skip", type=int, default=0)
    @ns_detect.response(200, "Success", history_response_model)
    def get(self):
        limit = request.args.get("limit", default=10, type=int)
        skip = request.args.get("skip", default=0, type=int)
        with get_db_session() as session:
            total_count = session.exec(select(func.count(OCRRecord.id))).one()

            # Prevent OOM / RAM overload by strictly deferring large BLOB binary columns
            statement = (
                select(OCRRecord)
                .options(
                    defer(OCRRecord.raw_image_data),
                    defer(OCRRecord.annotated_image_data),
                    defer(OCRRecord.audio_data)
                )
                .order_by(OCRRecord.id.desc())
                .offset(skip)
                .limit(limit)
            )
            records = session.exec(statement).all()

            output = []
            for r in records:
                parsed_json = []
                if r.ocr_json_data:
                    try:
                        parsed_json = json.loads(r.ocr_json_data)
                    except Exception:
                        parsed_json = r.ocr_json_data

                output.append({
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
                })

            return {
                "total": total_count,
                "records": output
            }, 200


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


