"""
test_resources.py — Tests for Categories, Folders, Documents, Decks, Cards, Tags, and Favorites.
"""

from __future__ import annotations

import io


def test_categories_crud(client):
    u_id = client.post(
        "/api/auth/register",
        json={"username": "catuser", "email": "catuser@edu.ai", "password": "p"},
    ).get_json()["id"]

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

    list_res = client.get(f"/api/categories?user_id={u_id}")
    assert list_res.status_code == 200
    assert len(list_res.get_json()) >= 1

    det_res = client.get(f"/api/categories/{cat_id}")
    assert det_res.status_code == 200
    assert det_res.get_json()["name"] == "Toán Học"

    put_res = client.put(
        f"/api/categories/{cat_id}",
        json={"name": "Toán Học Nâng Cao", "color_code": "#10B981"},
    )
    assert put_res.status_code == 200
    assert put_res.get_json()["name"] == "Toán Học Nâng Cao"

    del_res = client.delete(f"/api/categories/{cat_id}")
    assert del_res.status_code == 200
    assert client.get(f"/api/categories/{cat_id}").status_code == 404


def test_folders_crud(client):
    reg = client.post(
        "/api/auth/register",
        json={"username": "fuser", "email": "fuser@edu.ai", "password": "p"},
    ).get_json()
    u_id = reg["id"]

    f1 = client.post(
        "/api/folders",
        json={"user_id": u_id, "name": "Thư mục gốc", "description": "Root folder"},
    ).get_json()
    f1_id = f1["id"]

    f2 = client.post(
        "/api/folders",
        json={"user_id": u_id, "name": "Thư mục con", "parent_id": f1_id},
    ).get_json()
    f2_id = f2["id"]

    list_res = client.get(f"/api/folders?user_id={u_id}")
    assert list_res.status_code == 200
    assert len(list_res.get_json()) == 2

    det = client.get(f"/api/folders/{f1_id}").get_json()
    assert len(det["subfolders"]) == 1
    assert det["subfolders"][0]["id"] == f2_id

    up = client.put(f"/api/folders/{f2_id}", json={"name": "Thư mục con cập nhật"})
    assert up.status_code == 200
    assert up.get_json()["name"] == "Thư mục con cập nhật"

    del_res = client.delete(f"/api/folders/{f1_id}")
    assert del_res.status_code == 200
    assert client.get(f"/api/folders/{f2_id}").status_code == 404


def test_documents_crud_and_blob_stream(client):
    u_id = client.post(
        "/api/auth/register",
        json={"username": "docuser", "email": "docuser@edu.ai", "password": "p"},
    ).get_json()["id"]

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

    dup_res = client.post(
        "/api/documents/upload",
        data={
            "file": (io.BytesIO(file_content), "python_guide.txt"),
            "user_id": str(u_id),
        },
        content_type="multipart/form-data",
    )
    assert dup_res.status_code == 409

    list_res = client.get(f"/api/documents?user_id={u_id}")
    assert list_res.status_code == 200
    docs = list_res.get_json()
    assert len(docs) >= 1
    assert "file_blob" not in docs[0]

    det = client.get(f"/api/documents/{doc_id}").get_json()
    assert det["extracted_text"] == file_content.decode()

    dl_res = client.get(f"/api/documents/{doc_id}/download")
    assert dl_res.status_code == 200
    assert dl_res.data == file_content

    del_res = client.delete(f"/api/documents/{doc_id}")
    assert del_res.status_code == 200
    assert client.get(f"/api/documents/{doc_id}").status_code == 404


def test_decks_cards_tags_crud(client):
    u_id = client.post(
        "/api/auth/register",
        json={"username": "deckuser", "email": "deckuser@edu.ai", "password": "p"},
    ).get_json()["id"]

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

    decks_res = client.get(f"/api/decks?user_id={u_id}")
    assert decks_res.status_code == 200
    assert decks_res.get_json()[0]["card_count"] == 0

    tag = client.post("/api/tags", json={"user_id": u_id, "name": "ielts"}).get_json()
    tag_id = tag["id"]

    tags_res = client.get(f"/api/tags?user_id={u_id}")
    assert tags_res.status_code == 200

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

    att_res = client.post(f"/api/cards/{card_id}/tags", json={"tag_id": tag_id})
    assert att_res.status_code in [200, 201]

    card_det = client.get(f"/api/cards/{card_id}").get_json()
    assert len(card_det["tags"]) >= 1

    filter_res = client.get(f"/api/cards?tag_id={tag_id}")
    assert filter_res.status_code == 200
    assert len(filter_res.get_json()) == 1

    det_res = client.delete(f"/api/cards/{card_id}/tags/{tag_id}")
    assert det_res.status_code == 200

    deck_det = client.get(f"/api/decks/{deck_id}").get_json()
    assert len(deck_det["cards"]) == 1

    c_put = client.put(f"/api/cards/{card_id}", json={"difficulty": "hard"})
    assert c_put.status_code == 200
    assert c_put.get_json()["difficulty"] == "hard"

    c_del = client.delete(f"/api/cards/{card_id}")
    assert c_del.status_code == 200

    c_batch = client.delete(f"/api/cards?deck_id={deck_id}")
    assert c_batch.status_code == 200

    d_del = client.delete(f"/api/decks/{deck_id}")
    assert d_del.status_code == 200
    assert client.get(f"/api/decks/{deck_id}").status_code == 404

    t_del = client.delete(f"/api/tags/{tag_id}")
    assert t_del.status_code == 200


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

    fav_res = client.post("/api/favorites", json={"user_id": u_id, "card_id": card_id})
    assert fav_res.status_code == 201
    fav_id = fav_res.get_json()["id"]

    dup_res = client.post("/api/favorites", json={"user_id": u_id, "card_id": card_id})
    assert dup_res.status_code == 409

    fav_list = client.get(f"/api/favorites?user_id={u_id}")
    assert fav_list.status_code == 200
    assert len(fav_list.get_json()) == 1

    del1 = client.delete(f"/api/favorites/{fav_id}")
    assert del1.status_code == 200

    client.post("/api/favorites", json={"user_id": u_id, "card_id": card_id})
    del_card = client.delete(f"/api/favorites/card?user_id={u_id}&card_id={card_id}")
    assert del_card.status_code == 200
    assert len(client.get(f"/api/favorites?user_id={u_id}").get_json()) == 0
