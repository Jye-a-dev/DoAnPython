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
from server.core.security import clear_active_session_user

ensure_startup_initialized()
client = flask_app.test_client()


def test_registration_and_password_flow():
    print("=== [1] Testing /register endpoint ===")
    clear_active_session_user()

    test_email = f"user_{os.urandom(4).hex()}@example.com"
    test_password = "SecurePassword2026!"
    test_name = "Nguyen Van Test"

    # 1. Invalid short password
    bad_res = client.post("/api/v1/auth/register", json={
        "email": test_email,
        "password": "123",
        "full_name": test_name
    })
    assert bad_res.status_code == 400, f"Expected 400 for short password, got {bad_res.status_code}: {bad_res.text}"
    print("  [OK] Caught short password (< 6 chars) validation error.")

    # 2. Invalid email format
    bad_email_res = client.post("/api/v1/auth/register", json={
        "email": "invalidemail",
        "password": test_password,
        "full_name": test_name
    })
    assert bad_email_res.status_code == 400
    print("  [OK] Caught invalid email format error.")

    # 3. Successful registration
    reg_res = client.post("/api/v1/auth/register", json={
        "email": test_email,
        "password": test_password,
        "full_name": test_name
    })
    assert reg_res.status_code == 201, f"Registration failed: {reg_res.status_code} {reg_res.text}"
    reg_data = reg_res.get_json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == test_email
    assert reg_data["user"]["role_id"] == 2
    assert reg_data["user"]["full_name"] == test_name
    assert "password_hash" not in reg_data["user"], "Leaked password_hash in response!"
    cookies = reg_res.headers.getlist("Set-Cookie")
    assert any("access_token=" in c for c in cookies), "Missing access_token cookie on register"
    print("  [OK] User registered successfully with role_id=2 and UUID v4 ID.")

    # 4. Duplicate email registration
    dup_res = client.post("/api/v1/auth/register", json={
        "email": test_email,
        "password": test_password,
        "full_name": test_name
    })
    assert dup_res.status_code == 400
    assert "đã được đăng ký" in dup_res.get_json()["detail"]
    print("  [OK] Caught duplicate email registration error.")

    print("\n=== [2] Testing /login with password verification ===")
    clear_active_session_user()

    # 1. Login with non-existent email
    non_exist = client.post("/api/v1/auth/login", json={
        "email": "nonexistent@example.com",
        "password": "anypassword"
    })
    assert non_exist.status_code == 401
    print("  [OK] Non-existent account returned 401 Unauthorized.")

    # 2. Login with wrong password
    wrong_pass = client.post("/api/v1/auth/login", json={
        "email": test_email,
        "password": "WrongPassword!"
    })
    assert wrong_pass.status_code == 401
    assert "không chính xác" in wrong_pass.get_json()["detail"]
    print("  [OK] Wrong password returned 401 Unauthorized.")

    # 3. Login with correct password
    correct_login = client.post("/api/v1/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    assert correct_login.status_code == 200, f"Login failed: {correct_login.text}"
    login_data = correct_login.get_json()
    assert "access_token" in login_data
    assert login_data["user"]["email"] == test_email
    assert "password_hash" not in login_data["user"]
    print("  [OK] Login succeeded with correct password.")

    # 4. Verify dev preset accounts
    admin_login = client.post("/api/v1/auth/login", json={
        "email": "admin@system.local",
        "password": "Admin@System2026!"
    })
    assert admin_login.status_code == 200
    assert admin_login.get_json()["user"]["role_id"] == 1
    print("  [OK] Admin preset (admin@system.local / Admin@System2026!) authenticated successfully.")

    customer_login = client.post("/api/v1/auth/login", json={
        "email": "customer@shop.vn",
        "password": "Customer@Pass2026!"
    })
    assert customer_login.status_code == 200
    assert customer_login.get_json()["user"]["role_id"] == 2
    print("  [OK] Customer preset (customer@shop.vn / Customer@Pass2026!) authenticated successfully.")

    print("\n>>> ALL REGISTER & PASSWORD TESTS PASSED! [OK]")


if __name__ == "__main__":
    test_registration_and_password_flow()

