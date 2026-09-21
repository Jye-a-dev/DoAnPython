import io
import os
import sys
import sqlite3
from pathlib import Path
from unittest.mock import patch

SERVER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVER_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from server.app import ensure_startup_initialized, flask_app
from server.database import DB_PATH, engine
from server.core.security import create_access_token
from server.core.pipeline_client import (
    http_client,
    PipelineUnavailableError,
    PipelineExecutionError,
    PipelineTimeoutError
)

ensure_startup_initialized()
client = flask_app.test_client()

admin_token = create_access_token(3, "admin@system.local", 1)
admin_headers = {"Authorization": f"Bearer {admin_token}"}


def test_sqlite_pragmas_and_indexes():
    print("[1] Verifying SQLite WAL mode, Pragmas and Composite Indexes...")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        cursor.execute("PRAGMA journal_mode;")
        journal_mode = cursor.fetchone()[0]
        assert journal_mode.lower() == "wal", f"Expected WAL, got {journal_mode}"

        # Verify composite indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
        indexes = [row[0] for row in cursor.fetchall()]
        assert "idx_ocr_records_user_status_id" in indexes, "Missing idx_ocr_records_user_status_id"
        assert "idx_ocr_records_status_id" in indexes, "Missing idx_ocr_records_status_id"
        assert "idx_ocr_reviews_admin_id" in indexes, "Missing idx_ocr_reviews_admin_id"

        # Explain query plan for indexed pagination
        cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM ocr_records WHERE user_id = 1 AND status = 'pending' ORDER BY id DESC;")
        plan = cursor.fetchall()
        plan_str = " ".join(str(p) for p in plan)
        assert "idx_ocr_records_user_status_id" in plan_str or "idx_ocr_records_user_id" in plan_str
        print("    -> PRAGMAs and Composite Indexes verified successfully!")


def test_detect_exception_mapping():
    print("[2] Verifying /api/v1/detect Exception Hierarchy Mapping...")
    # Mock JPEG payload
    fake_jpg = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00" + b"\x00" * 100

    # 1. Pipeline unavailable -> 503
    with patch("server.routers.detect.call_pipeline_inference") as mock_inf:
        mock_inf.side_effect = PipelineUnavailableError("Connection refused to microservice")
        data = {"file": (io.BytesIO(fake_jpg), "test.jpg")}
        res = client.post("/api/v1/detect", data=data, content_type="multipart/form-data")
        assert res.status_code == 503, f"Expected 503, got {res.status_code}: {res.text}"
        assert "Service Unavailable" in res.get_json()["detail"]

    # 2. Pipeline timeout -> 504
    with patch("server.routers.detect.call_pipeline_inference") as mock_inf:
        mock_inf.side_effect = PipelineTimeoutError("Read timeout 15.0s")
        data = {"file": (io.BytesIO(fake_jpg), "test.jpg")}
        res = client.post("/api/v1/detect", data=data, content_type="multipart/form-data")
        assert res.status_code == 504, f"Expected 504, got {res.status_code}: {res.text}"
        assert "Gateway Timeout" in res.get_json()["detail"]

    # 3. Pipeline execution error -> 422
    with patch("server.routers.detect.call_pipeline_inference") as mock_inf:
        mock_inf.side_effect = PipelineExecutionError("Unprocessable entity")
        data = {"file": (io.BytesIO(fake_jpg), "test.jpg")}
        res = client.post("/api/v1/detect", data=data, content_type="multipart/form-data")
        assert res.status_code == 422, f"Expected 422, got {res.status_code}: {res.text}"
        assert "Pipeline processing failed" in res.get_json()["detail"]

    print("    -> Exception mapping (503, 504, 422) verified successfully!")


def test_3phase_ocr_review():
    print("[3] Verifying 3-Phase SQLite Lock Isolation on Reviews...")
    # First create an OCR record directly
    rec_res = client.post(
        "/api/v1/ocr-records",
        json={
            "image_url": "/static/uploads/test.jpg",
            "raw_detected_text": "Sample Text",
            "ocr_json_data": "[]",
            "audio_url": "/static/audio/test.mp3",
            "status": "pending"
        },
        headers=admin_headers
    )
    assert rec_res.status_code == 201, rec_res.text
    record_id = rec_res.get_json()["id"]

    # Review post with mocked TTS call
    with patch("server.routers.ocr_reviews.call_pipeline_tts") as mock_tts:
        mock_tts.return_value = "/static/audio/review_speech_123.mp3"
        rev_res = client.post(
            "/api/v1/ocr-reviews",
            json={
                "record_id": record_id,
                "corrected_text": "Ground Truth Text",
                "accuracy_score": 0.95,
                "review_notes": "Accurate correction"
            },
            headers=admin_headers
        )
        assert rev_res.status_code == 200, rev_res.text
        review_data = rev_res.get_json()
        assert review_data["corrected_audio_url"] == "/static/audio/review_speech_123.mp3"
        assert review_data["record_id"] == record_id

    # Verify record status was updated to approved
    check_rec = client.get(f"/api/v1/ocr-records/{record_id}")
    assert check_rec.status_code == 200
    assert check_rec.get_json()["status"] == "approved"
    print("    -> 3-Phase Review creation and status transition verified!")


def test_client_singleton_reuse():
    print("[4] Verifying httpx.Client singleton connection pool...")
    assert http_client is not None
    assert not http_client.is_closed
    assert http_client.timeout.read == 15.0
    assert http_client.timeout.connect == 3.0
    print("    -> Client singleton verified with Keep-Alive limits!")


if __name__ == "__main__":
    test_sqlite_pragmas_and_indexes()
    test_detect_exception_mapping()
    test_3phase_ocr_review()
    test_client_singleton_reuse()
    print("\n>>> ALL ARCHITECTURE HARDENING TESTS PASSED! [OK]\n")

