from __future__ import annotations

from typing import Any, Optional
from services.api_base import _handle_http_error, get_client


# ===========================================================================
# 1. USERS API (Table 1: users)
# ===========================================================================
async def get_users(
    username: Optional[str] = None,
    email: Optional[str] = None,
    role: Optional[str] = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        params = {
            k: v
            for k, v in {"username": username, "email": email, "role": role}.items()
            if v
        }
        res = await client.get("/users", params=params)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy danh sách users")


async def get_user_by_id(user_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.get(f"/users/{user_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy thông tin user")


async def create_user(
    username: str, email: str, password: str = "default_pass", role: str = "user"
) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.post(
            "/users",
            json={
                "username": username,
                "email": email,
                "password": password,
                "role": role,
            },
        )
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "tạo user")


async def login_user(username_or_email: str, password: str = "") -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.post(
            "/users/login", json={"login": username_or_email, "password": password}
        )
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "đăng nhập user")


async def auth_login(login: str, password: str) -> dict[str, Any]:
    """Xác thực đăng nhập người dùng qua POST /api/auth/login."""
    try:
        client = get_client()
        payload = {"login": login, "username": login, "email": login, "password": password}
        try:
            res = await client.post("/auth/login", json=payload)
            if res.status_code == 404:
                res = await client.post("/users/login", json=payload)
        except Exception:
            res = await client.post("/users/login", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "đăng nhập")


async def auth_register(
    display_name: str,
    email: str,
    password: str,
    username: Optional[str] = None,
) -> dict[str, Any]:
    """Tạo mới tài khoản người dùng qua POST /api/auth/register."""
    try:
        client = get_client()
        uname = username or (email.split("@")[0] if "@" in email else email)
        payload = {
            "username": uname,
            "email": email,
            "password": password,
            "display_name": display_name,
            "full_name": display_name,
        }
        try:
            res = await client.post("/auth/register", json=payload)
            if res.status_code == 404:
                res = await client.post("/users", json=payload)
        except Exception:
            res = await client.post("/users", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "đăng ký")


async def update_user(user_id: int, **fields: Any) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.put(f"/users/{user_id}", json=fields)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "cập nhật user")


async def delete_user(user_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.delete(f"/users/{user_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "xóa user")


# ===========================================================================
# 2. USER PROFILES API (Table 2: user_profiles)
# ===========================================================================
async def get_profiles(
    user_id: Optional[int] = None,
) -> list[dict[str, Any]] | dict[str, Any]:
    try:
        client = get_client()
        params = {"user_id": user_id} if user_id else None
        res = await client.get("/profiles", params=params)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy danh sách profiles")


async def get_profile_by_id(profile_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.get(f"/profiles/{profile_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy chi tiết profile")


async def get_user_profile(user_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.get(f"/users/{user_id}/profile")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "lấy profile theo user_id")


async def create_profile(user_id: int, **fields: Any) -> dict[str, Any]:
    try:
        client = get_client()
        payload = {"user_id": user_id, **fields}
        res = await client.post("/profiles", json=payload)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "tạo profile")


async def update_profile(profile_id: int, **fields: Any) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.put(f"/profiles/{profile_id}", json=fields)
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "cập nhật profile")


async def delete_profile(profile_id: int) -> dict[str, Any]:
    try:
        client = get_client()
        res = await client.delete(f"/profiles/{profile_id}")
        res.raise_for_status()
        return res.json()
    except Exception as err:
        return _handle_http_error(err, "xóa profile")

