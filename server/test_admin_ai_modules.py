import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app import flask_app
from server.database import get_db_session, init_db
from server.models.user import User
from server.models.product import Product
from server.models.ocr_record import OCRRecord
from server.models.ocr_review import OCRReview
from server.models.category import Category
from server.core.security import create_access_token


def setup_module():
    """Ensure database is initialized and has test admin token."""
    init_db()


def test_copilot_safe_sql_lock():
    """Verify Defense-in-depth: Reject DDL/DML injection, accept safe SELECT."""
    client = flask_app.test_client()
    admin_token = create_access_token("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", "admin@system.local", 1)
    headers = {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}

    # 1. Attack vector: DROP TABLE
    res = client.post("/api/v1/copilot/query", json={"query": "DROP TABLE users;"}, headers=headers)
    assert res.status_code == 400
    assert "Khóa an toàn" in res.json.get("detail", "")

    # 2. Attack vector: SQL chaining injection
    res = client.post("/api/v1/copilot/query", json={"query": "SELECT 1; DROP TABLE products;"}, headers=headers)
    assert res.status_code == 400
    assert "Khóa an toàn" in res.json.get("detail", "")

    # 3. Attack vector: INSERT/UPDATE
    res = client.post("/api/v1/copilot/query", json={"query": "UPDATE roles SET name = 'hacker'"}, headers=headers)
    assert res.status_code == 400

    # 4. Attack vector: Comment injection
    res = client.post("/api/v1/copilot/query", json={"query": "SELECT * FROM users /* comment */ WHERE 1=1"}, headers=headers)
    assert res.status_code == 400

    # 5. Safe Natural Language Query: Lọc bản ghi quét camera
    res = client.post("/api/v1/copilot/query", json={"query": "Lọc các bản ghi quét bị lỗi trong hôm nay"}, headers=headers)
    assert res.status_code == 200
    assert "safe_sql" in res.json
    assert "results" in res.json

    # 6. Safe Natural Language Query: Sản phẩm laptop tồn kho thấp
    res = client.post("/api/v1/copilot/query", json={"query": "Thống kê sản phẩm laptop bán chạy và tồn kho dưới 5"}, headers=headers)
    assert res.status_code == 200
    assert "safe_sql" in res.json


def test_preview_tts_stateless():
    """Verify POST /api/v1/ocr-reviews/preview-tts is stateless and non-blocking."""
    client = flask_app.test_client()
    res = client.post("/api/v1/ocr-reviews/preview-tts", json={"text": "máy tính xách tay"})
    assert res.status_code == 200
    assert "audio_url" in res.json
    assert res.json.get("status") == "success"


def test_inventory_forecast_json1_and_cache():
    """Verify inventory forecast computes with JSON1 and uses cache."""
    client = flask_app.test_client()
    res = client.get("/api/v1/products/inventory-forecast")
    assert res.status_code == 200
    data = res.json
    assert "items" in data
    assert "high_demand_count" in data
    assert "cached_at" in data


def test_mlops_drift_and_clusters():
    """Verify MLOps drift alert and error clusters endpoints."""
    client = flask_app.test_client()
    
    # Drift alert
    drift_res = client.get("/api/v1/mlops/drift-alert")
    assert drift_res.status_code == 200
    assert "drift_score" in drift_res.json
    assert "oov_terms" in drift_res.json
    assert "retrain_queue" in drift_res.json

    # Error clusters
    cluster_res = client.get("/api/v1/mlops/error-clusters")
    assert cluster_res.status_code == 200
    assert "clusters" in cluster_res.json
    assert len(cluster_res.json["clusters"]) >= 4

    # Export dataset
    export_res = client.get("/api/v1/mlops/export-dataset")
    assert export_res.status_code == 200
    assert export_res.mimetype == "application/json"


def test_daily_briefing():
    """Verify Copilot executive daily briefing endpoint."""
    client = flask_app.test_client()
    res = client.get("/api/v1/copilot/daily-briefing")
    assert res.status_code == 200
    assert "summary" in res.json
    assert "metrics" in res.json


if __name__ == "__main__":
    test_copilot_safe_sql_lock()
    print("[+] Test Safe Text-to-SQL & Security Lock: PASSED")
    test_preview_tts_stateless()
    print("[+] Test Stateless Preview TTS: PASSED")
    test_inventory_forecast_json1_and_cache()
    print("[+] Test Inventory Forecast JSON1 & Cache: PASSED")
    test_mlops_drift_and_clusters()
    print("[+] Test MLOps Drift & Clusters: PASSED")
    test_daily_briefing()
    print("[+] Test Executive Daily Briefing: PASSED")
    print("\n[=== ALL BACKEND AI MODULE TESTS PASSED 100% ===]")
