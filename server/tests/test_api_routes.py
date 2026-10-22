import io
import os
import sys
from pathlib import Path

_TEST_DIR = Path(__file__).resolve().parent
_SERVER_DIR = _TEST_DIR.parent
_ROOT_DIR = _SERVER_DIR.parent
for _p in [str(_SERVER_DIR), str(_ROOT_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pypdf
import pytest
from app.main import create_app
from app.core.database import db
from app.models.user import User


@pytest.fixture
def app_instance():
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.app_context():
        db.create_all()
        user = User(
            id=1,
            username="test_suite_user",
            email="test_suite@flashcard.ai",
            password_hash="argon2_mock_hash",
            role="user",
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def test_client(app_instance):
    return app_instance.test_client()


def test_system_health_and_pipeline_route(test_client):
    res = test_client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["database"] == "connected"
    assert "ai_pipeline" in data


def test_zero_local_storage_document_upload(test_client):
    files_before = set(os.listdir("."))

    pdf_buffer = io.BytesIO()
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(pdf_buffer)
    pdf_bytes = pdf_buffer.getvalue()

    upload_data = {
        "user_id": "1",
        "file": (io.BytesIO(pdf_bytes), "test_blob.pdf", "application/pdf"),
    }

    res_upload = test_client.post(
        "/api/documents/upload",
        data=upload_data,
        content_type="multipart/form-data",
    )
    assert res_upload.status_code in [200, 201]

    files_after = set(os.listdir("."))
    new_files = (
        files_after - files_before - {"instance", "test_schema.db", ".pytest_cache"}
    )
    assert not new_files, f"Leaked local files: {new_files}"


def test_crud_cards_and_decks(test_client):
    res_deck = test_client.post("/api/decks", json={"title": "Test Deck", "user_id": 1})
    assert res_deck.status_code == 201
    deck_id = res_deck.get_json().get("id")

    res_card = test_client.post(
        "/api/cards",
        json={
            "deck_id": deck_id,
            "question": "What is REST?",
            "answer": "Representational State Transfer",
        },
    )
    assert res_card.status_code in [200, 201]
    card_id = res_card.get_json().get("id")

    res_put = test_client.put(
        f"/api/cards/{card_id}", json={"answer": "Standard REST API"}
    )
    assert res_put.status_code == 200

    res_get = test_client.get("/api/cards")
    assert res_get.status_code == 200
    assert len(res_get.get_json()) >= 1


def test_study_session_and_sm2_review(test_client):
    res_deck = test_client.post("/api/decks", json={"title": "SM2 Deck", "user_id": 1})
    deck_id = res_deck.get_json().get("id")

    res_card = test_client.post(
        "/api/cards",
        json={"deck_id": deck_id, "question": "Q?", "answer": "A"},
    )
    card_id = res_card.get_json().get("id")

    res_session = test_client.post(
        "/api/study/sessions", json={"user_id": 1, "deck_id": deck_id}
    )
    assert res_session.status_code == 201
    session_id = res_session.get_json().get("session_id")

    res_review = test_client.post(
        "/api/study/review",
        json={"session_id": session_id, "card_id": card_id, "review_rating": 3},
    )
    assert res_review.status_code == 200
    review_data = res_review.get_json()
    assert "interval_days" in review_data and "ease_factor" in review_data
    assert review_data["interval_days"] == 1
    assert review_data["ease_factor"] == 2.5
