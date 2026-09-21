import os
import sys
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVER_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from server.app import ensure_startup_initialized, flask_app
from server.core.config import DEFAULT_ADMIN_USER_ID, DEFAULT_USER_USER_ID
from server.core.security import clear_active_session_user, create_access_token

ensure_startup_initialized()
client = flask_app.test_client()

admin_token = create_access_token(DEFAULT_ADMIN_USER_ID, "admin@system.local", 1)
user_token = create_access_token(DEFAULT_USER_USER_ID, "user@system.local", 2)


def test_auth_flexibility_and_session_persistence():
    print("=== [A] Testing Auth Flexibility & Persistent Single-Login Session ===")
    clear_active_session_user()

    # 1. Test Raw JWT in Authorization header (without Bearer prefix)
    res = client.get("/api/v1/auth/me", headers={"Authorization": admin_token})
    assert res.status_code == 200, f"Raw JWT header failed: {res.text}"
    assert res.get_json()["email"] == "admin@system.local"
    print("  [OK] Raw JWT header (no 'Bearer ' prefix) authenticated successfully.")

    # 2. Test Lowercase 'bearer <token>'
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"bearer {admin_token}"})
    assert res.status_code == 200, f"Lowercase bearer failed: {res.text}"
    print("  [OK] Lowercase 'bearer <token>' authenticated successfully.")

    # 3. Test Double 'Bearer Bearer <token>'
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer Bearer {admin_token}"})
    assert res.status_code == 200, f"Double Bearer failed: {res.text}"
    print("  [OK] Double 'Bearer Bearer <token>' handled gracefully.")

    # 4. Test X-Access-Token header
    res = client.get("/api/v1/auth/me", headers={"X-Access-Token": admin_token})
    assert res.status_code == 200, f"X-Access-Token failed: {res.text}"
    print("  [OK] X-Access-Token header authenticated successfully.")

    # 5. Test Query Parameter ?token=
    res = client.get(f"/api/v1/auth/me?token={admin_token}")
    assert res.status_code == 200, f"Query parameter auth failed: {res.text}"
    print("  [OK] Query parameter ?token= authenticated successfully.")

    # 6. Test Single Login -> Cross-route access via Cookie & in-memory session
    clear_active_session_user()
    # Log in once via /api/v1/auth/login
    login_res = client.post("/api/v1/auth/login", json={"email": "operator@test.local", "role_id": 1, "full_name": "Test Operator"})
    assert login_res.status_code == 200, login_res.text
    cookies = login_res.headers.getlist("Set-Cookie")
    assert any("access_token=" in c for c in cookies), "Cookie access_token was not set!"
    print("  [OK] Logged in once via /auth/login; 'access_token' cookie set.")

    # Call protected routes with NO Authorization header, relying on session/cookie
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 200, f"Cross-route session failed: {res.text}"
    assert res.get_json()["email"] == "operator@test.local"
    print("  [OK] Cross-route call to /auth/me succeeded with 0 headers ('log 1 lần là dùng tất cả route dc').")

    res = client.get("/api/v1/users/stats")
    assert res.status_code == 200, f"Protected admin route failed with session: {res.text}"
    print("  [OK] Protected admin route /users/stats accessed without Authorization header.")


def test_patch_routes_and_enriched_endpoints():
    print("\n=== [B] Testing All PATCH Routes & Enriched Endpoints ===")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # 1. Categories CRUD + PATCH + Relations
    print("  Testing Categories...")
    cat_res = client.post("/api/v1/categories", json={"name": "Sách & Văn phòng phẩm", "description": "Sách vở"}, headers=admin_headers)
    assert cat_res.status_code in (201, 400)
    if cat_res.status_code == 201:
        cat_id = cat_res.get_json()["id"]
    else:
        cat_id = client.get("/api/v1/categories?search=Sách").get_json()[0]["id"]

    patch_cat = client.patch(f"/api/v1/categories/{cat_id}", json={"description": "Sách kỹ thuật và văn phòng phẩm"}, headers=admin_headers)
    assert patch_cat.status_code == 200
    assert patch_cat.get_json()["description"] == "Sách kỹ thuật và văn phòng phẩm"

    cat_prods = client.get(f"/api/v1/categories/{cat_id}/products")
    assert cat_prods.status_code == 200
    print("    [OK] Categories CRUD, PATCH, and /products relation passed.")

    # 2. Products PATCH + Stock PATCH + Availability PATCH + Stats
    print("  Testing Products...")
    prod_res = client.post("/api/v1/products", json={
        "name": "Bút ký cao cấp",
        "category_id": cat_id,
        "price": 120000.0,
        "stock_quantity": 10,
        "sku": f"PEN-LUX-{os.urandom(2).hex()}"
    }, headers=admin_headers)
    assert prod_res.status_code == 201, prod_res.text
    prod_id = prod_res.get_json()["id"]

    # PATCH product details
    patch_p = client.patch(f"/api/v1/products/{prod_id}", json={"price": 135000.0, "description": "Bút máy cao cấp"}, headers=admin_headers)
    assert patch_p.status_code == 200
    assert patch_p.get_json()["price"] == 135000.0

    # PATCH product stock (increment)
    stock_p = client.patch(f"/api/v1/products/{prod_id}/stock", json={"stock_quantity": 5, "mode": "increment"}, headers=admin_headers)
    assert stock_p.status_code == 200
    assert stock_p.get_json()["stock_quantity"] == 15

    # PATCH product availability
    avail_p = client.patch(f"/api/v1/products/{prod_id}/availability", json={"is_available": False}, headers=admin_headers)
    assert avail_p.status_code == 200
    assert avail_p.get_json()["is_available"] is False

    # GET product stats
    p_stats = client.get("/api/v1/products/stats")
    assert p_stats.status_code == 200
    assert "total_inventory_value" in p_stats.get_json()
    print("    [OK] Products PATCH, /stock PATCH, /availability PATCH, and /stats passed.")

    # 3. Roles PATCH + Users relation
    print("  Testing Roles...")
    role_res = client.post("/api/v1/roles", json={"name": f"auditor_{os.urandom(2).hex()}", "description": "Auditor"}, headers=admin_headers)
    assert role_res.status_code == 201
    role_id = role_res.get_json()["id"]

    patch_role = client.patch(f"/api/v1/roles/{role_id}", json={"description": "Lead Quality Auditor"}, headers=admin_headers)
    assert patch_role.status_code == 200
    assert patch_role.get_json()["description"] == "Lead Quality Auditor"

    role_users = client.get(f"/api/v1/roles/{role_id}/users")
    assert role_users.status_code == 200
    print("    [OK] Roles PATCH and /users relation passed.")

    # 4. Users PATCH + Status PATCH + Stats
    print("  Testing Users...")
    u_res = client.post("/api/v1/users", json={"email": f"worker_{os.urandom(2).hex()}@test.local", "full_name": "Worker One"}, headers=admin_headers)
    assert u_res.status_code == 201
    u_id = u_res.get_json()["id"]

    patch_u = client.patch(f"/api/v1/users/{u_id}", json={"full_name": "Worker Super"}, headers=admin_headers)
    assert patch_u.status_code == 200
    assert patch_u.get_json()["full_name"] == "Worker Super"

    patch_u_status = client.patch(f"/api/v1/users/{u_id}/status", json={"is_active": False}, headers=admin_headers)
    assert patch_u_status.status_code == 200
    assert patch_u_status.get_json()["is_active"] is False

    u_stats = client.get("/api/v1/users/stats", headers=admin_headers)
    assert u_stats.status_code == 200
    print("    [OK] Users PATCH, /status PATCH, and /stats passed.")

    # 5. Cart PATCH + Summary
    print("  Testing Cart...")
    client.patch(f"/api/v1/products/{prod_id}/availability", json={"is_available": True}, headers=admin_headers)
    add_c = client.post("/api/v1/cart/items", json={"product_id": prod_id, "quantity": 1}, headers=user_headers)
    assert add_c.status_code == 201
    cart_item_id = add_c.get_json()["id"]

    # PATCH cart item delta (+2)
    patch_c = client.patch(f"/api/v1/cart/items/{cart_item_id}", json={"delta": 2}, headers=user_headers)
    assert patch_c.status_code == 200
    assert patch_c.get_json()["quantity"] == 3

    cart_sum = client.get("/api/v1/cart/summary", headers=user_headers)
    assert cart_sum.status_code == 200
    assert cart_sum.get_json()["total_items"] >= 3
    print("    [OK] Cart /items PATCH and /summary passed.")

    # 6. Orders Checkout + PATCH + Status PATCH + Count + Stats
    print("  Testing Orders...")
    order_res = client.post("/api/v1/orders/checkout", json={
        "shipping_address": "456 Tran Phu, Da Nang",
        "phone_number": "0912345678"
    }, headers=user_headers)
    assert order_res.status_code == 201
    order_id = order_res.get_json()["id"]

    # PATCH order details
    patch_o = client.patch(f"/api/v1/orders/{order_id}", json={"phone_number": "0988888888"}, headers=user_headers)
    assert patch_o.status_code == 200
    assert patch_o.get_json()["phone_number"] == "0988888888"

    # PATCH order status
    patch_o_st = client.patch(f"/api/v1/orders/{order_id}/status", json={"status": "paid"}, headers=admin_headers)
    assert patch_o_st.status_code == 200
    assert patch_o_st.get_json()["status"] == "paid"

    # Count & Stats
    o_count = client.get("/api/v1/orders/count", headers=user_headers)
    assert o_count.status_code == 200
    o_stats = client.get("/api/v1/orders/stats", headers=user_headers)
    assert o_stats.status_code == 200
    print("    [OK] Orders Checkout, PATCH, /status PATCH, /count, and /stats passed.")

    # 7. OCR Records PATCH + Status PATCH + Stats
    print("  Testing OCR Records...")
    rec_res = client.post("/api/v1/ocr-records", json={
        "raw_detected_text": "Phát hiện chai nước",
        "ocr_json_data": [{"name": "bottle", "confidence": 0.95}],
        "status": "pending"
    }, headers=admin_headers)
    assert rec_res.status_code == 201
    rec_id = rec_res.get_json()["id"]

    patch_rec = client.patch(f"/api/v1/ocr-records/{rec_id}", json={"raw_detected_text": "Phát hiện chai nước Lavie"}, headers=admin_headers)
    assert patch_rec.status_code == 200
    assert patch_rec.get_json()["raw_detected_text"] == "Phát hiện chai nước Lavie"

    patch_rec_st = client.patch(f"/api/v1/ocr-records/{rec_id}/status", json={"status": "approved"}, headers=admin_headers)
    assert patch_rec_st.status_code == 200
    assert patch_rec_st.get_json()["status"] == "approved"

    rec_stats = client.get("/api/v1/ocr-records/stats")
    assert rec_stats.status_code == 200
    print("    [OK] OCR Records PATCH, /status PATCH, and /stats passed.")

    # 8. OCR Reviews PATCH + Stats
    print("  Testing OCR Reviews...")
    rev_res = client.post("/api/v1/ocr-reviews", json={
        "record_id": rec_id,
        "corrected_text": "Chai nước khoáng Lavie 500ml",
        "accuracy_score": 0.95,
        "review_notes": "Chính xác cao"
    }, headers=admin_headers)
    assert rev_res.status_code == 200
    rev_id = rev_res.get_json()["id"]

    patch_rev = client.patch(f"/api/v1/ocr-reviews/{rev_id}", json={"review_notes": "Đã kiểm duyệt hoàn tất"}, headers=admin_headers)
    assert patch_rev.status_code == 200
    assert patch_rev.get_json()["review_notes"] == "Đã kiểm duyệt hoàn tất"

    rev_stats = client.get("/api/v1/ocr-reviews/stats")
    assert rev_stats.status_code == 200
    print("    [OK] OCR Reviews PATCH and /stats passed.")

    # 9. Auth PATCH /me
    print("  Testing Auth PATCH /me...")
    patch_me = client.patch("/api/v1/auth/me", json={"full_name": "Admin Root Updated"}, headers=admin_headers)
    assert patch_me.status_code == 200
    assert patch_me.get_json()["full_name"] == "Admin Root Updated"
    print("    [OK] Auth PATCH /me passed.")

    print("\n>>> ALL TESTS COMPLETED AND VERIFIED 100% SUCCEEDED! [OK]")


if __name__ == "__main__":
    test_auth_flexibility_and_session_persistence()
    test_patch_routes_and_enriched_endpoints()
