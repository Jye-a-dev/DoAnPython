import os
import sys
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVER_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from server.app import ensure_startup_initialized, flask_app
from server.core.security import create_access_token

ensure_startup_initialized()
client = flask_app.test_client()

# Prepare auth headers
admin_token = create_access_token(3, "admin@system.local", 1)
user_token = create_access_token(1, "user@system.local", 2)
admin_headers = {"Authorization": f"Bearer {admin_token}"}
user_headers = {"Authorization": f"Bearer {user_token}"}


def test_full_crud_and_count():
    print("[1] Testing Roles module...")
    res = client.get("/api/v1/roles/count")
    assert res.status_code == 200, res.text
    initial_role_count = res.get_json()["count"]
    assert initial_role_count >= 2

    # Create new role
    role_payload = {"name": "test_auditor", "description": "Audits accuracy logs"}
    res = client.post("/api/v1/roles", json=role_payload, headers=admin_headers)
    assert res.status_code == 201, res.text
    new_role = res.get_json()
    role_id = new_role["id"]
    print(f"    Created role ID: {role_id}, name: {new_role['name']}")

    # Verify count incremented
    res = client.get("/api/v1/roles/count")
    assert res.get_json()["count"] == initial_role_count + 1

    # Read role by ID
    res = client.get(f"/api/v1/roles/{role_id}")
    assert res.status_code == 200
    assert res.get_json()["name"] == "test_auditor"

    # Update role
    res = client.put(f"/api/v1/roles/{role_id}", json={"description": "Updated auditor description"}, headers=admin_headers)
    assert res.status_code == 200
    assert res.get_json()["description"] == "Updated auditor description"

    # Delete role
    res = client.delete(f"/api/v1/roles/{role_id}", headers=admin_headers)
    assert res.status_code == 200

    # Verify count decremented
    res = client.get("/api/v1/roles/count")
    assert res.get_json()["count"] == initial_role_count

    print("[2] Testing Users module...")
    res = client.get("/api/v1/users/count")
    assert res.status_code == 200
    initial_user_count = res.get_json()["count"]

    # Create user
    user_payload = {
        "email": "test_member@example.com",
        "full_name": "Test Member",
        "role_id": 2,
        "is_active": True
    }
    res = client.post("/api/v1/users", json=user_payload, headers=admin_headers)
    assert res.status_code == 201, res.text
    created_user = res.get_json()
    test_user_id = created_user["id"]
    print(f"    Created User ID: {test_user_id}")

    # Verify user count
    res = client.get("/api/v1/users/count")
    assert res.get_json()["count"] == initial_user_count + 1

    # Delete test user
    res = client.delete(f"/api/v1/users/{test_user_id}", headers=admin_headers)
    assert res.status_code == 200

    print("[3] Testing Products & Visual Search module...")
    res = client.get("/api/v1/products/count")
    assert res.status_code == 200
    initial_product_count = res.get_json()["count"]

    # Create product
    prod_payload = {
        "name": "Apple Fresh 1kg",
        "class_name": "apple",
        "sku": "SKU-APPLE-01",
        "price": 45000.0,
        "stock_quantity": 25,
        "is_available": True
    }
    res = client.post("/api/v1/products", json=prod_payload, headers=admin_headers)
    assert res.status_code in (201, 400)
    if res.status_code == 201:
        prod_id = res.get_json()["id"]
    else:
        # Retrieve existing
        res = client.get("/api/v1/products?search=Apple")
        prod_id = res.get_json()[0]["id"]

    # Read product
    res = client.get(f"/api/v1/products/{prod_id}")
    assert res.status_code == 200
    assert res.get_json()["price"] == 45000.0

    print("[4] Testing Cart & Orders checkout module...")
    # Add to cart
    cart_add_payload = {"product_id": prod_id, "quantity": 2}
    res = client.post("/api/v1/cart/items", json=cart_add_payload, headers=user_headers)
    assert res.status_code == 201, res.text
    cart_item = res.get_json()
    item_id = cart_item["id"]
    print(f"    Added item to cart, item ID: {item_id}, quantity: {cart_item['quantity']}")

    # Get cart
    res = client.get("/api/v1/cart", headers=user_headers)
    assert res.status_code == 200
    assert res.get_json()["total_items"] >= 2

    # Checkout
    checkout_payload = {
        "shipping_address": "123 Nguyen Trai, Ha Noi",
        "phone_number": "0987654321"
    }
    res = client.post("/api/v1/orders/checkout", json=checkout_payload, headers=user_headers)
    assert res.status_code == 201, res.text
    order = res.get_json()
    print(f"    Checkout confirmed, Order ID: {order['id']}, total: {order['total_amount']}")

    # Verify cart is empty after checkout
    res = client.get("/api/v1/cart", headers=user_headers)
    assert res.status_code == 200
    assert res.get_json()["total_items"] == 0

    print("\n>>> ALL TESTS PASSED SUCCESSFULLY! [OK]")


if __name__ == "__main__":
    test_full_crud_and_count()
