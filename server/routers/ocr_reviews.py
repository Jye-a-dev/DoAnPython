from datetime import datetime, timezone

from flask import request
from flask_restx import Namespace, Resource, fields
from sqlalchemy import func
from sqlalchemy.orm import defer
from sqlmodel import select

from server.core.common_models import count_model, message_model
from server.core.pipeline_client import call_pipeline_tts, fetch_media_bytes
from server.core.security import admin_required
from server.database import get_db_session
from server.models.ocr_record import OCRRecord
from server.models.ocr_review import OCRReview

ns_reviews = Namespace("OCR Reviews (Admin Ground Truth)", path="/api/v1/ocr-reviews", description="Full CRUD for review validation")
ns_reviews.add_model("CountResponse", count_model)
ns_reviews.add_model("MessageResponse", message_model)

review_create_model = ns_reviews.model("OCRReviewCreateRequest", {
    "record_id": fields.String(required=True, description="Target OCR Record ID"),
    "corrected_text": fields.String(required=True, description="Ground truth corrected text"),
    "accuracy_score": fields.Float(required=True, min=0.0, max=1.0, description="Accuracy score (0.0 to 1.0)"),
    "review_notes": fields.String(required=False, description="Review remarks")
})

review_update_model = ns_reviews.model("OCRReviewUpdateRequest", {
    "corrected_text": fields.String(description="Ground truth corrected text"),
    "accuracy_score": fields.Float(min=0.0, max=1.0, description="Accuracy score (0.0 to 1.0)"),
    "review_notes": fields.String(description="Review remarks")
})

review_patch_model = ns_reviews.model("OCRReviewPatchRequest", {
    "corrected_text": fields.String(description="Ground truth corrected text"),
    "accuracy_score": fields.Float(min=0.0, max=1.0, description="Accuracy score (0.0 to 1.0)"),
    "review_notes": fields.String(description="Review remarks")
})

review_stats_model = ns_reviews.model("OCRReviewStatsResponse", {
    "total_reviews": fields.Integer,
    "average_accuracy": fields.Float,
    "approved_count": fields.Integer,
    "rejected_count": fields.Integer
})

preview_tts_request_model = ns_reviews.model("OCRReviewPreviewTTSRequest", {
    "text": fields.String(required=True, description="Text string to synthesize for preview")
})

preview_tts_response_model = ns_reviews.model("OCRReviewPreviewTTSResponse", {
    "audio_url": fields.String(description="Synthesized audio URL"),
    "status": fields.String(default="success")
})

review_model = ns_reviews.model("OCRReview", {
    "id": fields.String,
    "record_id": fields.String,
    "admin_id": fields.String,
    "corrected_text": fields.String,
    "corrected_audio_url": fields.String,
    "accuracy_score": fields.Float,
    "review_notes": fields.String,
    "reviewed_at": fields.String
})


@ns_reviews.route("/count")
class OCRReviewCount(Resource):
    @ns_reviews.doc("count_reviews", description="Count total verified reviews")
    @ns_reviews.response(200, "Success", count_model)
    def get(self):
        with get_db_session() as session:
            count = session.exec(select(func.count(OCRReview.id))).one()
            return {"count": count}, 200


@ns_reviews.route("/stats")
class OCRReviewStats(Resource):
    @ns_reviews.doc("get_review_stats", description="Aggregated statistics for admin reviews")
    @ns_reviews.response(200, "Success", review_stats_model)
    def get(self):
        with get_db_session() as session:
            reviews = session.exec(select(OCRReview)).all()
            total = len(reviews)
            avg_acc = (sum(r.accuracy_score for r in reviews) / total) if total > 0 else 0.0
            approved = sum(1 for r in reviews if r.accuracy_score >= 0.8)
            rejected = total - approved
            return {
                "total_reviews": total,
                "average_accuracy": round(avg_acc, 3),
                "approved_count": approved,
                "rejected_count": rejected
            }, 200


@ns_reviews.route("/preview-tts")
class OCRReviewPreviewTTS(Resource):
    @ns_reviews.doc("preview_tts", description="Stateless TTS preview generation without saving to database")
    @ns_reviews.expect(preview_tts_request_model, validate=True)
    @ns_reviews.response(200, "Success", preview_tts_response_model)
    def post(self):
        data = request.json or {}
        text = (data.get("text") or "").strip()
        if not text:
            return {"detail": "Text cannot be empty."}, 400
        audio_url = call_pipeline_tts(text)
        return {"audio_url": audio_url, "status": "success"}, 200


@ns_reviews.route("")
class OCRReviewListCreate(Resource):
    @ns_reviews.doc("create_review", security="Bearer", description="Submit admin review, synthesize corrected speech, and update status")
    @ns_reviews.expect(review_create_model, validate=True)
    @ns_reviews.response(200, "Review saved", review_model)
    @ns_reviews.response(400, "Validation error")
    @ns_reviews.response(404, "OCR Record not found")
    @admin_required
    def post(self, current_user: dict):
        data = request.json or {}
        record_id = data.get("record_id")
        corrected_text = data.get("corrected_text", "").strip()
        accuracy_score = float(data.get("accuracy_score", 1.0))
        review_notes = data.get("review_notes", "")

        if not record_id or not corrected_text:
            return {"detail": "Thiếu record_id hoặc corrected_text."}, 400

        # Phase 1: Read & Validate Record existence
        with get_db_session() as session:
            record = session.get(OCRRecord, record_id)
            if not record:
                return {"detail": f"Không tìm thấy OCR record ID {record_id}."}, 404

        # Phase 2: HTTP Network I/O (Executed outside any database transaction/lock)
        corrected_audio_url = call_pipeline_tts(corrected_text)
        corrected_audio_bytes = fetch_media_bytes(corrected_audio_url) if corrected_audio_url else b""
        new_status = "approved" if accuracy_score >= 0.8 else "rejected"

        # Phase 3: Defensive Check & Atomic Write
        with get_db_session() as session:
            rec = session.get(OCRRecord, record_id)
            if not rec:
                return {"detail": f"OCR record ID {record_id} không còn tồn tại hoặc đã bị xóa."}, 404

            rec.status = new_status

            existing_review = session.exec(select(OCRReview).where(OCRReview.record_id == record_id)).first()
            if existing_review:
                existing_review.admin_id = current_user["id"]
                existing_review.corrected_text = corrected_text
                if corrected_audio_bytes:
                    existing_review.corrected_audio_data = corrected_audio_bytes
                    existing_review.corrected_audio_mime = "audio/mpeg"
                existing_review.accuracy_score = accuracy_score
                existing_review.review_notes = review_notes
                existing_review.reviewed_at = datetime.now(timezone.utc)
                review_obj = existing_review
            else:
                review_obj = OCRReview(
                    record_id=record_id,
                    admin_id=current_user["id"],
                    corrected_text=corrected_text,
                    corrected_audio_data=corrected_audio_bytes or b"\x00" * 16,
                    corrected_audio_mime="audio/mpeg",
                    accuracy_score=accuracy_score,
                    review_notes=review_notes,
                    reviewed_at=datetime.now(timezone.utc)
                )
                session.add(review_obj)

            session.commit()
            session.refresh(review_obj)

            return {
                "id": review_obj.id,
                "record_id": review_obj.record_id,
                "admin_id": review_obj.admin_id,
                "corrected_text": review_obj.corrected_text,
                "corrected_audio_url": f"/api/v1/media/reviews/{review_obj.id}/audio",
                "accuracy_score": review_obj.accuracy_score,
                "review_notes": review_obj.review_notes,
                "reviewed_at": review_obj.reviewed_at.isoformat() if hasattr(review_obj.reviewed_at, "isoformat") else str(review_obj.reviewed_at)
            }, 200

    @ns_reviews.doc("list_reviews", description="List reviews with optional admin_id/record_id filtering and deferred BLOB loading")
    @ns_reviews.param("admin_id", "Filter by admin ID", type=str)
    @ns_reviews.param("record_id", "Filter by record ID", type=str)
    @ns_reviews.param("limit", "Number of items", type=int, default=10)
    @ns_reviews.param("skip", "Number of items to skip", type=int, default=0)
    @ns_reviews.response(200, "Success", [review_model])
    def get(self):
        admin_id = request.args.get("admin_id", type=str)
        record_id = request.args.get("record_id", type=str)
        limit = request.args.get("limit", default=10, type=int)
        skip = request.args.get("skip", default=0, type=int)

        with get_db_session() as session:
            stmt = select(OCRReview).options(defer(OCRReview.corrected_audio_data))
            if admin_id:
                stmt = stmt.where(OCRReview.admin_id == admin_id)
            if record_id:
                stmt = stmt.where(OCRReview.record_id == record_id)
            stmt = stmt.order_by(OCRReview.id.desc()).offset(skip).limit(limit)

            reviews = session.exec(stmt).all()
            return [
                {
                    "id": r.id,
                    "record_id": r.record_id,
                    "admin_id": r.admin_id,
                    "corrected_text": r.corrected_text,
                    "corrected_audio_url": f"/api/v1/media/reviews/{r.id}/audio",
                    "accuracy_score": r.accuracy_score,
                    "review_notes": r.review_notes,
                    "reviewed_at": r.reviewed_at.isoformat() if hasattr(r.reviewed_at, "isoformat") else str(r.reviewed_at)
                } for r in reviews
            ], 200


@ns_reviews.route("/<string:review_id>")
class OCRReviewDetail(Resource):
    @ns_reviews.doc("get_review_detail", description="Get review record details by ID")
    @ns_reviews.response(200, "Success", review_model)
    @ns_reviews.response(404, "Not Found")
    def get(self, review_id: str):
        with get_db_session() as session:
            review = session.get(OCRReview, review_id)
            if not review:
                return {"detail": f"Review ID {review_id} not found."}, 404
            return {
                "id": review.id,
                "record_id": review.record_id,
                "admin_id": review.admin_id,
                "corrected_text": review.corrected_text,
                "corrected_audio_url": f"/api/v1/media/reviews/{review.id}/audio",
                "accuracy_score": review.accuracy_score,
                "review_notes": review.review_notes,
                "reviewed_at": review.reviewed_at.isoformat() if hasattr(review.reviewed_at, "isoformat") else str(review.reviewed_at)
            }, 200

    @ns_reviews.doc("update_review", security="Bearer", description="Update an existing review record")
    @ns_reviews.expect(review_update_model, validate=True)
    @ns_reviews.response(200, "Review updated", review_model)
    @ns_reviews.response(404, "Review not found")
    @admin_required
    def put(self, review_id: str, current_user: dict):
        return self._handle_update(review_id, current_user)

    @ns_reviews.doc("patch_review", security="Bearer", description="Partially update an existing review record")
    @ns_reviews.expect(review_patch_model, validate=False)
    @ns_reviews.response(200, "Review updated", review_model)
    @ns_reviews.response(404, "Review not found")
    @admin_required
    def patch(self, review_id: str, current_user: dict):
        return self._handle_update(review_id, current_user)

    def _handle_update(self, review_id: str, current_user: dict):
        data = request.json or {}

        # Phase 1: Read & Validate Review existence
        with get_db_session() as session:
            review = session.get(OCRReview, review_id)
            if not review:
                return {"detail": f"Review ID {review_id} not found."}, 404

        # Phase 2: HTTP Network I/O outside DB session
        corrected_audio_bytes = None
        if "corrected_text" in data and data["corrected_text"]:
            new_text = data["corrected_text"].strip()
            tts_url = call_pipeline_tts(new_text)
            if tts_url:
                corrected_audio_bytes = fetch_media_bytes(tts_url)

        # Phase 3: Defensive Check & Atomic Write
        with get_db_session() as session:
            review = session.get(OCRReview, review_id)
            if not review:
                return {"detail": f"Review ID {review_id} not found."}, 404

            if "corrected_text" in data and data["corrected_text"]:
                review.corrected_text = data["corrected_text"].strip()
                if corrected_audio_bytes:
                    review.corrected_audio_data = corrected_audio_bytes
                    review.corrected_audio_mime = "audio/mpeg"
            if "accuracy_score" in data and data["accuracy_score"] is not None:
                review.accuracy_score = float(data["accuracy_score"])
                rec = session.get(OCRRecord, review.record_id)
                if rec:
                    rec.status = "approved" if review.accuracy_score >= 0.8 else "rejected"
            if "review_notes" in data and data["review_notes"] is not None:
                review.review_notes = data["review_notes"]

            review.admin_id = current_user["id"]
            review.reviewed_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(review)

            return {
                "id": review.id,
                "record_id": review.record_id,
                "admin_id": review.admin_id,
                "corrected_text": review.corrected_text,
                "corrected_audio_url": f"/api/v1/media/reviews/{review.id}/audio",
                "accuracy_score": review.accuracy_score,
                "review_notes": review.review_notes,
                "reviewed_at": review.reviewed_at.isoformat() if hasattr(review.reviewed_at, "isoformat") else str(review.reviewed_at)
            }, 200

    @ns_reviews.doc("delete_review", security="Bearer", description="Delete a review record by ID")
    @ns_reviews.response(200, "Review deleted", message_model)
    @ns_reviews.response(404, "Review not found")
    @admin_required
    def delete(self, review_id: str, current_user: dict):
        with get_db_session() as session:
            review = session.get(OCRReview, review_id)
            if not review:
                return {"detail": f"Review ID {review_id} not found."}, 404
            session.delete(review)
            session.commit()
            return {"message": f"Review ID {review_id} deleted successfully.", "success": True}, 200
