"""
tests/test_all_crud_routes.py — Comprehensive test suite for all 13 tables CRUD and Gateway endpoints.
"""

from __future__ import annotations

import io
import pytest
from app.main import create_app
from app.core.database import db


@pytest.fixture
def app():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


# ==============================================================================
# 1. TAG: System
# ==============================================================================
def test_system_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["database"] == "connected"


def test_system_status(client):
    res = client.get("/api/system/status")
    assert res.status_code == 200
    data = res.get_json()
    assert "server" in data
    assert "hardware" in data
    assert "microservices" in data


# ==============================================================================
# 2. TAG: Auth & Users & Profiles
# ==============================================================================
def test_auth_and_users_profiles_crud(client):
    # Register user
    reg_payload = {
        "username": "tester01",
        "email": "tester01@eduflash.ai",
        "password": "secret_pass_123",
        "display_name": "Tester Alpha",
        "full_name": "Tester Alpha Full",
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    user = reg_res.get_json()
    user_id = user["id"]
    assert user["username"] == "tester01"
    assert "password_hash" not in user

    # Login
    login_res = client.post(
        "/api/auth/login",
        json={"login": "tester01@eduflash.ai", "password": "secret_pass_123"},
    )
    assert login_res.status_code == 200
    login_data = login_res.get_json()
    assert login_data["success"] is True

    # List users (pagination)
    list_res = client.get("/api/users?page=1&limit=20&role=user")
    assert list_res.status_code == 200
    users_list = list_res.get_json()
    assert any(u["id"] == user_id for u in users_list)
    assert "password_hash" not in users_list[0]

    # Get user by id with profile
    detail_res = client.get(f"/api/users/{user_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.get_json()
    assert "profile" in detail_data
    assert detail_data["profile"]["display_name"] == "Tester Alpha"

    # Put user
    put_res = client.put(
        f"/api/users/{user_id}",
        json={
            "email": "updated_tester01@eduflash.ai",
            "is_active": True,
            "role": "admin",
        },
    )
    assert put_res.status_code == 200
    assert put_res.get_json()["email"] == "updated_tester01@eduflash.ai"

    # Get user profile
    prof_res = client.get(f"/api/users/{user_id}/profile")
    assert prof_res.status_code == 200
    assert prof_res.get_json()["daily_card_goal"] == 20

    # Put user profile
    prof_put = client.put(
        f"/api/users/{user_id}/profile",
        json={
            "bio": "Love studying",
            "daily_card_goal": 50,
            "timezone": "Asia/Bangkok",
        },
    )
    assert prof_put.status_code == 200
    assert prof_put.get_json()["daily_card_goal"] == 50
    assert prof_put.get_json()["bio"] == "Love studying"


# ==============================================================================
# 3. TAG: Categories
# ==============================================================================
def test_categories_crud(client):
    # Setup user first to satisfy foreign key constraint
    u_id = client.post(
        "/api/auth/register",
        json={"username": "catuser", "email": "catuser@edu.ai", "password": "p"},
    ).get_json()["id"]

    # Create category
    cat_res = client.post(
        "/api/categories",
        json={
            "user_id": u_id,
            "name": "Toán Học",
            "description": "Các bộ thẻ đại số và giải tích",
            "color_code": "#EF4444",
        },
    )
    assert cat_res.status_code == 201
    cat = cat_res.get_json()
    cat_id = cat["id"]

    # List categories
    list_res = client.get(f"/api/categories?user_id={u_id}")
    assert list_res.status_code == 200
    assert len(list_res.get_json()) >= 1

    # Get detail
    det_res = client.get(f"/api/categories/{cat_id}")
    assert det_res.status_code == 200
    assert det_res.get_json()["name"] == "Toán Học"

    # Update
    put_res = client.put(
        f"/api/categories/{cat_id}",
        json={"name": "Toán Học Nâng Cao", "color_code": "#10B981"},
    )
    assert put_res.status_code == 200
    assert put_res.get_json()["name"] == "Toán Học Nâng Cao"

    # Delete
    del_res = client.delete(f"/api/categories/{cat_id}")
    assert del_res.status_code == 200
    assert client.get(f"/api/categories/{cat_id}").status_code == 404


# ==============================================================================
# 4. TAG: Folders
# ==============================================================================
def test_folders_crud(client):
    # Setup user
    reg = client.post(
        "/api/auth/register",
        json={"username": "fuser", "email": "fuser@edu.ai", "password": "p"},
    ).get_json()
    u_id = reg["id"]

    # Create root folder
    f1 = client.post(
        "/api/folders",
        json={"user_id": u_id, "name": "Thư mục gốc", "description": "Root folder"},
    ).get_json()
    f1_id = f1["id"]

    # Create subfolder
    f2 = client.post(
        "/api/folders",
        json={"user_id": u_id, "name": "Thư mục con", "parent_id": f1_id},
    ).get_json()
    f2_id = f2["id"]

    # List folders
    list_res = client.get(f"/api/folders?user_id={u_id}")
    assert list_res.status_code == 200
    assert len(list_res.get_json()) == 2

    # Get folder detail with subfolders
    det = client.get(f"/api/folders/{f1_id}").get_json()
    assert len(det["subfolders"]) == 1
    assert det["subfolders"][0]["id"] == f2_id

    # Update folder
    up = client.put(f"/api/folders/{f2_id}", json={"name": "Thư mục con cập nhật"})
    assert up.status_code == 200
    assert up.get_json()["name"] == "Thư mục con cập nhật"

    # Delete root folder (cascade delete subfolder)
    del_res = client.delete(f"/api/folders/{f1_id}")
    assert del_res.status_code == 200
    assert client.get(f"/api/folders/{f2_id}").status_code == 404


# ==============================================================================
# 5. TAG: Documents
# ==============================================================================
def test_documents_crud_and_blob_stream(client):
    # Setup user
    u_id = client.post(
        "/api/auth/register",
        json={"username": "docuser", "email": "docuser@edu.ai", "password": "p"},
    ).get_json()["id"]

    # Upload TXT file
    file_content = b"Hoc Python can co su kien tri va thuc hanh thuong xuyen."
    data = {
        "file": (io.BytesIO(file_content), "python_guide.txt"),
        "user_id": str(u_id),
    }
    up_res = client.post(
        "/api/documents/upload",
        data=data,
        content_type="multipart/form-data",
    )
    assert up_res.status_code == 201
    doc = up_res.get_json()
    doc_id = doc["id"]
    assert doc["filename"] == "python_guide.txt"
    assert doc["extracted_text"] == file_content.decode()

    # Conflict test: duplicate upload must return 409
    dup_res = client.post(
        "/api/documents/upload",
        data={
            "file": (io.BytesIO(file_content), "python_guide.txt"),
            "user_id": str(u_id),
        },
        content_type="multipart/form-data",
    )
    assert dup_res.status_code == 409

    # List documents (file_blob not loaded in response)
    list_res = client.get(f"/api/documents?user_id={u_id}")
    assert list_res.status_code == 200
    docs = list_res.get_json()
    assert len(docs) >= 1
    assert "file_blob" not in docs[0]

    # Get detail
    det = client.get(f"/api/documents/{doc_id}").get_json()
    assert det["extracted_text"] == file_content.decode()

    # Download blob stream
    dl_res = client.get(f"/api/documents/{doc_id}/download")
    assert dl_res.status_code == 200
    assert dl_res.data == file_content

    # Delete document
    del_res = client.delete(f"/api/documents/{doc_id}")
    assert del_res.status_code == 200
    assert client.get(f"/api/documents/{doc_id}").status_code == 404


# ==============================================================================
# 6. TAG: Decks & Cards & Tags
# ==============================================================================
def test_decks_cards_tags_crud(client):
    u_id = client.post(
        "/api/auth/register",
        json={"username": "deckuser", "email": "deckuser@edu.ai", "password": "p"},
    ).get_json()["id"]

    # Create Deck
    deck = client.post(
        "/api/decks",
        json={
            "user_id": u_id,
            "title": "English Vocab",
            "description": "Daily words",
            "is_public": True,
        },
    ).get_json()
    deck_id = deck["id"]

    # List Decks
    decks_res = client.get(f"/api/decks?user_id={u_id}")
    assert decks_res.status_code == 200
    assert decks_res.get_json()[0]["card_count"] == 0

    # Create Tag
    tag = client.post("/api/tags", json={"user_id": u_id, "name": "ielts"}).get_json()
    tag_id = tag["id"]

    # List Tags
    tags_res = client.get(f"/api/tags?user_id={u_id}")
    assert tags_res.status_code == 200

    # Create Card
    card = client.post(
        "/api/cards",
        json={
            "deck_id": deck_id,
            "question": "What is 'Serendipity'?",
            "answer": "Finding good things without looking for them",
            "difficulty": "medium",
        },
    ).get_json()
    card_id = card["id"]

    # Attach Tag to Card
    att_res = client.post(f"/api/cards/{card_id}/tags", json={"tag_id": tag_id})
    assert att_res.status_code in [200, 201]

    # Get Card Detail with Tags
    card_det = client.get(f"/api/cards/{card_id}").get_json()
    assert len(card_det["tags"]) >= 1

    # Filter Cards by tag_id
    filter_res = client.get(f"/api/cards?tag_id={tag_id}")
    assert filter_res.status_code == 200
    assert len(filter_res.get_json()) == 1

    # Detach Tag
    det_res = client.delete(f"/api/cards/{card_id}/tags/{tag_id}")
    assert det_res.status_code == 200

    # Check Deck card_count
    deck_det = client.get(f"/api/decks/{deck_id}").get_json()
    assert len(deck_det["cards"]) == 1

    # Update Card
    c_put = client.put(f"/api/cards/{card_id}", json={"difficulty": "hard"})
    assert c_put.status_code == 200
    assert c_put.get_json()["difficulty"] == "hard"

    # Delete Card
    c_del = client.delete(f"/api/cards/{card_id}")
    assert c_del.status_code == 200

    # Batch delete cards in deck
    c_batch = client.delete(f"/api/cards?deck_id={deck_id}")
    assert c_batch.status_code == 200

    # Delete Deck
    d_del = client.delete(f"/api/decks/{deck_id}")
    assert d_del.status_code == 200
    assert client.get(f"/api/decks/{deck_id}").status_code == 404

    # Delete Tag
    t_del = client.delete(f"/api/tags/{tag_id}")
    assert t_del.status_code == 200


# ==============================================================================
# 7. TAG: Study & SRS Reviews (SM-2)
# ==============================================================================
def test_study_sessions_and_srs_sm2(client):
    u_id = client.post(
        "/api/auth/register",
        json={"username": "studyuser", "email": "studyuser@edu.ai", "password": "p"},
    ).get_json()["id"]

    deck_id = client.post(
        "/api/decks",
        json={"user_id": u_id, "title": "SM-2 Deck"},
    ).get_json()["id"]

    card_id = client.post(
        "/api/cards",
        json={"deck_id": deck_id, "question": "SM-2 Test Q", "answer": "Test A"},
    ).get_json()["id"]

    # Start Session
    s_res = client.post(
        "/api/study/sessions", json={"user_id": u_id, "deck_id": deck_id}
    )
    assert s_res.status_code == 201
    session_id = s_res.get_json()["session_id"]

    # Submit Review (Rating 3: Good)
    rev1_res = client.post(
        "/api/study/review",
        json={
            "session_id": session_id,
            "card_id": card_id,
            "user_id": u_id,
            "review_rating": 3,
        },
    )
    assert rev1_res.status_code == 201
    rev1 = rev1_res.get_json()["review"]
    assert rev1["repetitions"] == 1
    assert rev1["interval_days"] == 1

    # Session total_reviewed should increment to 1
    s_det = client.get(f"/api/study/sessions/{session_id}").get_json()
    assert s_det["total_reviewed"] == 1

    # Submit Review 2 (Rating 4: Easy)
    rev2_res = client.post(
        "/api/study/review",
        json={
            "session_id": session_id,
            "card_id": card_id,
            "user_id": u_id,
            "review_rating": 4,
        },
    )
    assert rev2_res.status_code == 201
    rev2 = rev2_res.get_json()["review"]
    assert rev2["repetitions"] == 2
    assert rev2["interval_days"] >= 6

    # List reviews
    revs_list = client.get(f"/api/study/reviews?session_id={session_id}")
    assert revs_list.status_code == 200
    assert len(revs_list.get_json()) == 2

    # End Session
    end_res = client.put(f"/api/study/sessions/{session_id}/end")
    assert end_res.status_code == 200
    assert end_res.get_json()["session"]["ended_at"] is not None


# ==============================================================================
# 8. TAG: User Favorites
# ==============================================================================
def test_favorites_crud(client):
    u_id = client.post(
        "/api/auth/register",
        json={"username": "favuser", "email": "favuser@edu.ai", "password": "p"},
    ).get_json()["id"]

    deck_id = client.post(
        "/api/decks", json={"user_id": u_id, "title": "Fav Deck"}
    ).get_json()["id"]

    card_id = client.post(
        "/api/cards", json={"deck_id": deck_id, "question": "Q", "answer": "A"}
    ).get_json()["id"]

    # Add Favorite
    fav_res = client.post("/api/favorites", json={"user_id": u_id, "card_id": card_id})
    assert fav_res.status_code == 201
    fav_id = fav_res.get_json()["id"]

    # Conflict test: duplicate favorite must return 409
    dup_res = client.post("/api/favorites", json={"user_id": u_id, "card_id": card_id})
    assert dup_res.status_code == 409

    # List Favorites
    fav_list = client.get(f"/api/favorites?user_id={u_id}")
    assert fav_list.status_code == 200
    assert len(fav_list.get_json()) == 1

    # Delete Favorite by ID
    del1 = client.delete(f"/api/favorites/{fav_id}")
    assert del1.status_code == 200

    # Add again and delete via /favorites/card
    client.post("/api/favorites", json={"user_id": u_id, "card_id": card_id})
    del_card = client.delete(f"/api/favorites/card?user_id={u_id}&card_id={card_id}")
    assert del_card.status_code == 200
    assert len(client.get(f"/api/favorites?user_id={u_id}").get_json()) == 0


# ==============================================================================
# 9. TAG: AI Logs
# ==============================================================================
def test_ai_logs_crud(client):
    u_id = client.post(
        "/api/auth/register",
        json={"username": "loguser", "email": "loguser@edu.ai", "password": "p"},
    ).get_json()["id"]

    # Create log
    log = client.post(
        "/api/ai-logs",
        json={
            "user_id": u_id,
            "model_name": "qwen2.5-0.5b",
            "cards_generated": 4,
            "inference_time_seconds": 0.85,
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "status": "SUCCESS",
        },
    ).get_json()
    log_id = log["id"]

    # List logs
    logs_res = client.get(f"/api/ai-logs?user_id={u_id}&status=SUCCESS")
    assert logs_res.status_code == 200
    res_list = logs_res.get_json()
    assert len(res_list) >= 1
    assert res_list[0]["cards_generated"] == 4
    assert res_list[0]["inference_time_seconds"] == 0.85

    # Get detail
    det_res = client.get(f"/api/ai-logs/{log_id}")
    assert det_res.status_code == 200

    # Delete log
    del_res = client.delete(f"/api/ai-logs/{log_id}")
    assert del_res.status_code == 200
    assert client.get(f"/api/ai-logs/{log_id}").status_code == 404
