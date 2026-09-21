import os
import sys
from pathlib import Path
from unittest.mock import patch

SERVER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVER_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from server.app import ensure_startup_initialized, flask_app
from server.core.config import (
    DEFAULT_ADMIN_ROLE_ID,
    DEFAULT_ADMIN_USER_ID,
    DEFAULT_ELECTRONICS_CATEGORY_ID,
    DEFAULT_FOOD_CATEGORY_ID,
    DEFAULT_USER_ROLE_ID,
    DEFAULT_USER_USER_ID,
)
from server.core.security import CurrentUser, create_access_token, get_current_user_from_request
from server.database import get_db_session
from server.models.category import Category
from server.models.product import Product
from server.models.user import User

ensure_startup_initialized()
client = flask_app.test_client()

admin_token = create_access_token(DEFAULT_ADMIN_USER_ID, "admin@system.local", DEFAULT_ADMIN_ROLE_ID)
user_token = create_access_token(DEFAULT_USER_USER_ID, "user@system.local", DEFAULT_USER_ROLE_ID)
admin_headers = {"Authorization": f"Bearer {admin_token}"}
user_headers = {"Authorization": f"Bearer {user_token}"}


def test_seed_data_synchronization():
    """Verify that seed users, categories, and products have exact deterministic UUID v4 strings."""
    with get_db_session() as session:
        admin = session.get(User, DEFAULT_ADMIN_USER_ID)
        assert admin is not None, f"Admin user {DEFAULT_ADMIN_USER_ID} not found"
        assert admin.role_id == DEFAULT_ADMIN_ROLE_ID
        assert admin.email == "admin@system.local"

        user = session.get(User, DEFAULT_USER_USER_ID)
        assert user is not None, f"User {DEFAULT_USER_USER_ID} not found"
        assert user.role_id == DEFAULT_USER_ROLE_ID
        assert user.email == "user@system.local"

        cat_elec = session.get(Category, DEFAULT_ELECTRONICS_CATEGORY_ID)
        assert cat_elec is not None
        assert cat_elec.slug == "thiet-bi-dien-tu"

        cat_food = session.get(Category, DEFAULT_FOOD_CATEGORY_ID)
        assert cat_food is not None
        assert cat_food.slug == "do-uong-thuc-pham"

        laptop = session.get(Product, "dddddddd-dddd-4ddd-8ddd-dddddddddddd")
        assert laptop is not None
        assert laptop.category_id == DEFAULT_ELECTRONICS_CATEGORY_ID
        assert laptop.class_name == "laptop"


def test_auth_bypass_dev_and_current_user():
    """Verify CurrentUser supports dual item and attribute access and AUTH_BYPASS_DEV functions."""
    cu = CurrentUser({
        "id": DEFAULT_ADMIN_USER_ID,
        "email": "admin@system.local",
        "role_id": DEFAULT_ADMIN_ROLE_ID,
        "full_name": "Dev Bypass Administrator",
        "is_active": True
    })
    # Both dict indexing and attribute access must work seamlessly
    assert cu["id"] == DEFAULT_ADMIN_USER_ID
    assert cu.get("id") == DEFAULT_ADMIN_USER_ID
    assert cu.id == DEFAULT_ADMIN_USER_ID
    assert cu.email == "admin@system.local"
    assert cu.role_id == 1
    assert cu.is_active is True

    # Test get_current_user_from_request with AUTH_BYPASS_DEV mocked to True
    with patch("server.core.security.AUTH_BYPASS_DEV", True):
        with flask_app.test_request_context("/", headers={}):
            bypassed = get_current_user_from_request()
            assert bypassed is not None
            assert bypassed.id == DEFAULT_ADMIN_USER_ID
            assert bypassed["id"] == DEFAULT_ADMIN_USER_ID
            assert bypassed.role_id == DEFAULT_ADMIN_ROLE_ID


def test_order_checkout_tts_short_uuid():
    """Verify Order checkout generates TTS message with 8-character uppercase UUID prefix."""
    # Ensure product stock exists
    prod_id = "dddddddd-dddd-4ddd-8ddd-ddddddddddde"  # Lavie bottle
    # Add to cart
    add_res = client.post("/api/v1/cart/items", json={"product_id": prod_id, "quantity": 1}, headers=user_headers)
    assert add_res.status_code in (201, 200), add_res.text

    captured_messages = []

    def mock_tts(msg):
        captured_messages.append(msg)
        return "/static/audio/tts_test.mp3"

    with patch("server.routers.orders.call_pipeline_tts", side_effect=mock_tts):
        checkout_res = client.post(
            "/api/v1/orders/checkout",
            json={"shipping_address": "789 Cau Giay, Ha Noi", "phone_number": "0912345678"},
            headers=user_headers
        )
        assert checkout_res.status_code == 201, checkout_res.text
        order_data = checkout_res.get_json()
        order_id = str(order_data["id"])
        expected_prefix = order_id[:8].upper()

        # Check that TTS message received the short prefix
        import time
        time.sleep(0.5)  # Let background executor run
        assert len(captured_messages) > 0, "TTS was not triggered"
        assert expected_prefix in captured_messages[0], f"Expected {expected_prefix} in {captured_messages[0]}"
        assert f"Đơn hàng mã số {expected_prefix}" in captured_messages[0]


def test_flask_restx_routing_order():
    """Verify that static endpoints (/count, /match-from-scan, /items) are not intercepted by dynamic <string:id>."""
    # 1. Roles /count
    res = client.get("/api/v1/roles/count")
    assert res.status_code == 200
    assert "count" in res.get_json()

    # 2. Users /count
    res = client.get("/api/v1/users/count")
    assert res.status_code == 200
    assert "count" in res.get_json()

    # 3. Products /count
    res = client.get("/api/v1/products/count")
    assert res.status_code == 200
    assert "count" in res.get_json()

    # 4. Products /match-from-scan
    res = client.post("/api/v1/products/match-from-scan", json={"record_id": "nonexistent-record-id"})
    assert res.status_code == 404
    assert "Không tìm thấy" in res.get_json().get("detail", "")

    # 5. OCR Records /count
    res = client.get("/api/v1/ocr-records/count")
    assert res.status_code == 200
    assert "count" in res.get_json()

    # 6. OCR Reviews /count
    res = client.get("/api/v1/ocr-reviews/count")
    assert res.status_code == 200
    assert "count" in res.get_json()

    # 7. Cart root GET and DELETE
    res = client.get("/api/v1/cart", headers=user_headers)
    assert res.status_code == 200
    assert "items" in res.get_json()

    res = client.delete("/api/v1/cart", headers=user_headers)
    assert res.status_code == 200
    assert res.get_json().get("success") is True

    # 8. Cart /items POST
    res = client.post("/api/v1/cart/items", json={"product_id": "dddddddd-dddd-4ddd-8ddd-dddddddddddd", "quantity": 1}, headers=user_headers)
    assert res.status_code == 201
    item_id = res.get_json()["id"]

    # 9. Cart /items/<string:item_id> PUT and DELETE
    res = client.put(f"/api/v1/cart/items/{item_id}", json={"quantity": 2}, headers=user_headers)
    assert res.status_code == 200
    assert res.get_json()["quantity"] == 2

    res = client.delete(f"/api/v1/cart/items/{item_id}", headers=user_headers)
    assert res.status_code == 200


if __name__ == "__main__":
    test_seed_data_synchronization()
    test_auth_bypass_dev_and_current_user()
    test_order_checkout_tts_short_uuid()
    test_flask_restx_routing_order()
    print("\n>>> ALL UUID MIGRATION AND CONFLICT RESOLUTION TESTS PASSED! [OK]\n")

