from flask import Blueprint, Response, abort
from flask_restx import Namespace, Resource
from server.database import get_db_session
from server.models.ocr_record import OCRRecord
from server.models.ocr_review import OCRReview

media_bp = Blueprint("media", __name__, url_prefix="/api/v1/media")
ns_media = Namespace("Binary Media Streaming", path="/api/v1/media", description="Direct SQLite BLOB binary streaming")


@media_bp.route("/records/<string:record_id>/audio", methods=["GET"])
def stream_record_audio(record_id: str):
    """Client gọi route này để gắn trực tiếp vào thẻ HTML5 Audio."""
    with get_db_session() as session:
        record = session.get(OCRRecord, record_id)
        if not record or not record.audio_data:
            abort(404, description="Audio not found")

        return Response(
            record.audio_data,
            mimetype=record.audio_mime or "audio/mpeg",
            headers={"Content-Disposition": f"inline; filename=speech_{record_id}.mp3"}
        )


@media_bp.route("/records/<string:record_id>/image", methods=["GET"])
def stream_record_image(record_id: str):
    """Client gọi route này để gắn trực tiếp vào thẻ <img>."""
    with get_db_session() as session:
        record = session.get(OCRRecord, record_id)
        if not record:
            abort(404, description="Image not found")

        data = record.annotated_image_data or record.raw_image_data
        mime = record.annotated_image_mime or record.raw_image_mime or "image/jpeg"
        if not data:
            abort(404, description="Image content is empty")

        return Response(
            data,
            mimetype=mime,
            headers={"Content-Disposition": f"inline; filename=image_{record_id}.jpg"}
        )


@media_bp.route("/records/<string:record_id>/raw-image", methods=["GET"])
def stream_record_raw_image(record_id: str):
    """Stream ảnh thô gốc camera trước khi inference."""
    with get_db_session() as session:
        record = session.get(OCRRecord, record_id)
        if not record or not record.raw_image_data:
            abort(404, description="Raw image not found")

        return Response(
            record.raw_image_data,
            mimetype=record.raw_image_mime or "image/jpeg",
            headers={"Content-Disposition": f"inline; filename=raw_{record_id}.jpg"}
        )


@media_bp.route("/reviews/<string:review_id>/audio", methods=["GET"])
def stream_review_audio(review_id: str):
    """Stream audio tổng hợp sau thẩm định của admin từ BLOB."""
    with get_db_session() as session:
        review = session.get(OCRReview, review_id)
        if not review or not review.corrected_audio_data:
            abort(404, description="Review audio not found")

        return Response(
            review.corrected_audio_data,
            mimetype=review.corrected_audio_mime or "audio/mpeg",
            headers={"Content-Disposition": f"inline; filename=review_speech_{review_id}.mp3"}
        )


@ns_media.route("/records/<string:record_id>/image")
class SwaggerMediaImage(Resource):
    @ns_media.doc("stream_image", description="Stream JPEG/PNG annotated image directly from SQLite BLOB")
    def get(self, record_id: str):
        return stream_record_image(record_id)


@ns_media.route("/records/<string:record_id>/audio")
class SwaggerMediaAudio(Resource):
    @ns_media.doc("stream_audio", description="Stream MP3 audio synthesized speech directly from SQLite BLOB")
    def get(self, record_id: str):
        return stream_record_audio(record_id)


@ns_media.route("/reviews/<string:review_id>/audio")
class SwaggerReviewMediaAudio(Resource):
    @ns_media.doc("stream_review_audio", description="Stream verified review speech MP3 from SQLite BLOB")
    def get(self, review_id: str):
        return stream_review_audio(review_id)
