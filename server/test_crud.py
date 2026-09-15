import os
import sys
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVER_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from fastapi.testclient import TestClient
from server.app import app
from server.database import init_db

# Initialize database schema and seeds
init_db()
client = TestClient(app)


def test_full_crud_and_count():
    print("[1] Testing Roles module...")
    # Count initial roles
    res = client.get("/api/v1/roles/count")
    assert res.status_code == 200, res.text
    initial_role_count = res.json()["count"]
    print(f"    Initial role count: {initial_role_count}")
    assert initial_role_count >= 2

    # Create new role - verifies sqlite_sequence sync (should not collide with id 1 or 2)
    role_payload = {"name": "test_auditor", "description": "Audits accuracy logs"}
    res = client.post("/api/v1/roles", json=role_payload)
    assert res.status_code == 201, res.text
    new_role = res.json()
    role_id = new_role["id"]
    print(f"    Created role ID: {role_id}, name: {new_role['name']}")
    assert role_id > 2

    # Verify count incremented
    res = client.get("/api/v1/roles/count")
    assert res.json()["count"] == initial_role_count + 1

    # Read role by ID
    res = client.get(f"/api/v1/roles/{role_id}")
    assert res.status_code == 200
    assert res.json()["name"] == "test_auditor"

    # Update role
    res = client.put(f"/api/v1/roles/{role_id}", json={"description": "Updated auditor description"})
    assert res.status_code == 200
    assert res.json()["description"] == "Updated auditor description"

    # Delete role
    res = client.delete(f"/api/v1/roles/{role_id}")
    assert res.status_code == 204

    # Verify count decremented
    res = client.get("/api/v1/roles/count")
    assert res.json()["count"] == initial_role_count

    print("[2] Testing Users module...")
    # Count users
    res = client.get("/api/v1/users/count")
    assert res.status_code == 200
    initial_user_count = res.json()["count"]

    # Test FK failure: non-existent role_id
    res = client.post("/api/v1/users", json={
        "email": "invalid_role@example.com",
        "full_name": "Invalid Role User",
        "role_id": 99999
    })
    assert res.status_code == 400
    print("    FK validation correctly blocked user creation with invalid role_id.")

    # Create admin user (role_id = 1)
    admin_payload = {
        "google_id": "google_admin_123",
        "email": "admin_test@example.com",
        "full_name": "Test Admin",
        "role_id": 1,
        "is_active": True
    }
    res = client.post("/api/v1/users", json=admin_payload)
    assert res.status_code == 201, res.text
    admin_user = res.json()
    admin_id = admin_user["id"]
    print(f"    Created Admin user ID: {admin_id}, created_at: {admin_user['created_at']}")

    # Create regular user (role_id = 2)
    user_payload = {
        "google_id": "google_user_456",
        "email": "user_test@example.com",
        "full_name": "Test Regular User",
        "role_id": 2,
        "is_active": True
    }
    res = client.post("/api/v1/users", json=user_payload)
    assert res.status_code == 201, res.text
    regular_user = res.json()
    user_id = regular_user["id"]
    print(f"    Created Regular user ID: {user_id}")

    # Count filtered by role_id
    res = client.get("/api/v1/users/count?role_id=1")
    assert res.json()["count"] >= 1

    # Update user
    res = client.put(f"/api/v1/users/{user_id}", json={"full_name": "Updated User Name"})
    assert res.status_code == 200
    assert res.json()["full_name"] == "Updated User Name"

    print("[3] Testing OCR Records module...")
    # Initial count
    res = client.get(f"/api/v1/ocr-records/count?user_id={user_id}")
    assert res.status_code == 200
    assert res.json()["count"] == 0

    # Create record
    ocr_payload = {
        "user_id": user_id,
        "image_url": "/static/uploads/test_frame.jpg",
        "raw_detected_text": "Cà phê sữa đá",
        "ocr_json_data": '{"boxes": [[10, 20, 100, 200]], "label": "coffee"}',
        "audio_url": "/static/audio/test_audio.mp3",
        "status": "pending"
    }
    res = client.post("/api/v1/ocr-records", json=ocr_payload)
    assert res.status_code == 201, res.text
    ocr_record = res.json()
    record_id = ocr_record["id"]
    print(f"    Created OCR record ID: {record_id}, status: {ocr_record['status']}")

    # Count with status filter
    res = client.get("/api/v1/ocr-records/count?status=pending")
    assert res.json()["count"] >= 1

    # Read OCR record
    res = client.get(f"/api/v1/ocr-records/{record_id}")
    assert res.status_code == 200
    assert res.json()["raw_detected_text"] == "Cà phê sữa đá"

    # Update OCR record status
    res = client.put(f"/api/v1/ocr-records/{record_id}", json={"status": "approved"})
    assert res.status_code == 200
    assert res.json()["status"] == "approved"

    print("[4] Testing OCR Reviews module...")
    # Initial count
    res = client.get(f"/api/v1/ocr-reviews/count?admin_id={admin_id}")
    assert res.status_code == 200
    initial_review_count = res.json()["count"]

    # Create review
    review_payload = {
        "record_id": record_id,
        "admin_id": admin_id,
        "corrected_text": "Cà phê sữa đá Sài Gòn",
        "corrected_audio_url": "/static/audio/test_corrected_audio.mp3",
        "accuracy_score": 0.95,
        "review_notes": "Bổ sung chuẩn vị từ ngữ"
    }
    res = client.post("/api/v1/ocr-reviews", json=review_payload)
    assert res.status_code == 201, res.text
    review = res.json()
    review_id = review["id"]
    print(f"    Created OCR review ID: {review_id}, accuracy: {review['accuracy_score']}")

    # Duplicate review on same record_id must fail (unique constraint)
    res = client.post("/api/v1/ocr-reviews", json=review_payload)
    assert res.status_code == 409
    print("    Uniqueness validation blocked duplicate review for same record_id.")

    # Count reviews
    res = client.get(f"/api/v1/ocr-reviews/count?admin_id={admin_id}")
    assert res.json()["count"] == initial_review_count + 1

    # Update review
    res = client.put(f"/api/v1/ocr-reviews/{review_id}", json={"accuracy_score": 0.98})
    assert res.status_code == 200
    assert res.json()["accuracy_score"] == 0.98

    # Delete review
    res = client.delete(f"/api/v1/ocr-reviews/{review_id}")
    assert res.status_code == 204

    # Clean up test users and records
    res = client.delete(f"/api/v1/users/{user_id}")
    assert res.status_code == 204
    res = client.delete(f"/api/v1/users/{admin_id}")
    assert res.status_code == 204

    # Verify cascade delete: ocr_record should be gone
    res = client.get(f"/api/v1/ocr-records/{record_id}")
    assert res.status_code == 404
    print("    Cascade delete verified: record removed when user was deleted.")

    print("\n[SUCCESS] All CRUD + Count endpoints and SQLite integrity checks passed cleanly!")


if __name__ == "__main__":
    test_full_crud_and_count()

