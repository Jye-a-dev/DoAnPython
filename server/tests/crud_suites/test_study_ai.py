"""
test_study_ai.py — Tests for Study Sessions, SM-2 Reviews, and AI Logs.
"""

from __future__ import annotations


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


def test_ai_logs_crud(client):
    u_id = client.post(
        "/api/auth/register",
        json={"username": "loguser", "email": "loguser@edu.ai", "password": "p"},
    ).get_json()["id"]

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

    logs_res = client.get(f"/api/ai-logs?user_id={u_id}&status=SUCCESS")
    assert logs_res.status_code == 200
    res_list = logs_res.get_json()
    assert len(res_list) >= 1
    assert res_list[0]["cards_generated"] == 4
    assert res_list[0]["inference_time_seconds"] == 0.85

    det_res = client.get(f"/api/ai-logs/{log_id}")
    assert det_res.status_code == 200

    del_res = client.delete(f"/api/ai-logs/{log_id}")
    assert del_res.status_code == 200
    assert client.get(f"/api/ai-logs/{log_id}").status_code == 404

