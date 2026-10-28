"""
test_system_auth.py — Tests for System, Auth, Users, and Profiles endpoints.
"""

from __future__ import annotations


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


def test_auth_and_users_profiles_crud(client):
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

    login_res = client.post(
        "/api/auth/login",
        json={"login": "tester01@eduflash.ai", "password": "secret_pass_123"},
    )
    assert login_res.status_code == 200
    login_data = login_res.get_json()
    assert login_data["success"] is True

    list_res = client.get("/api/users?page=1&limit=20&role=user")
    assert list_res.status_code == 200
    users_list = list_res.get_json()
    assert any(u["id"] == user_id for u in users_list)
    assert "password_hash" not in users_list[0]

    detail_res = client.get(f"/api/users/{user_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.get_json()
    assert "profile" in detail_data
    assert detail_data["profile"]["display_name"] == "Tester Alpha"

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

    prof_res = client.get(f"/api/users/{user_id}/profile")
    assert prof_res.status_code == 200
    assert prof_res.get_json()["daily_card_goal"] == 20

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
