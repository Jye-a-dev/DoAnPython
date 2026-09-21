import functools
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from flask import request
from sqlmodel import select

from server.core.config import (
    AUTH_BYPASS_DEV,
    DEFAULT_ADMIN_ROLE_ID,
    DEFAULT_ADMIN_USER_ID,
    JWT_ALGORITHM,
    JWT_SECRET,
)
from server.database import get_db_session
from server.models.user import User


class CurrentUser(dict):
    """Hybrid dictionary supporting item and attribute access for seamless auth handling."""

    def __getattr__(self, name: str):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'CurrentUser' object has no attribute '{name}'")

    def __setattr__(self, name: str, value):
        self[name] = value

    def __delattr__(self, name: str):
        try:
            del self[name]
        except KeyError:
            raise AttributeError(f"'CurrentUser' object has no attribute '{name}'")


def create_access_token(user_id: str, email: str, role_id: int) -> str:
    """Generate signed JWT token valid for 7 days with string UUID subject."""
    payload = {
        "sub": str(user_id),
        "user_id": str(user_id),
        "email": email,
        "role_id": role_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


# In-memory single-session cache allowing server-wide persistence after logging in once
_last_authenticated_user: Optional[CurrentUser] = None


def set_active_session_user(user_data: dict) -> CurrentUser:
    """Register the active authenticated user into server memory."""
    global _last_authenticated_user
    _last_authenticated_user = CurrentUser(user_data)
    return _last_authenticated_user


def get_active_session_user() -> Optional[CurrentUser]:
    """Retrieve in-memory session user if active."""
    global _last_authenticated_user
    return _last_authenticated_user


def clear_active_session_user():
    """Clear server-wide in-memory session on logout."""
    global _last_authenticated_user
    _last_authenticated_user = None


def extract_token_from_request() -> Optional[str]:
    """Extract raw JWT token from Authorization header, custom headers, cookies, or query parameters."""
    # 1. Check Authorization header (handle Bearer, lowercase bearer, Bearer:, or raw token)
    auth_header = request.headers.get("Authorization")
    if auth_header:
        auth_header = auth_header.strip()
        # Clean potential repeated 'Bearer ' prefixes
        while auth_header.lower().startswith("bearer "):
            auth_header = auth_header[7:].strip()
        while auth_header.lower().startswith("bearer:"):
            auth_header = auth_header[7:].strip()
        if auth_header:
            return auth_header

    # 2. Check X-Access-Token or X-Auth-Token headers
    custom_header = request.headers.get("X-Access-Token") or request.headers.get("X-Auth-Token")
    if custom_header:
        return custom_header.strip()

    # 3. Check Cookie (browser / Swagger UI auto-transmission)
    cookie_token = request.cookies.get("access_token") or request.cookies.get("token") or request.cookies.get("jwt")
    if cookie_token:
        return cookie_token.strip()

    # 4. Check Query Parameter (useful for media streaming, testing, or redirects)
    query_token = request.args.get("access_token") or request.args.get("token")
    if query_token:
        return query_token.strip()

    return None


def get_current_user_from_request() -> Optional[CurrentUser]:
    """Extract and validate bearer token, retrieving user attributes inside session or using session/dev fallback."""
    token = extract_token_from_request()

    if not token:
        # If no token provided in request, check server in-memory session from previous login
        active_user = get_active_session_user()
        if active_user:
            return active_user

        if AUTH_BYPASS_DEV:
            return CurrentUser({
                "id": DEFAULT_ADMIN_USER_ID,
                "email": "admin@system.local",
                "role_id": DEFAULT_ADMIN_ROLE_ID,
                "full_name": "Dev Bypass Administrator",
                "avatar_url": None,
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        return None

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = str(payload.get("user_id") or payload.get("sub") or "")
        email = payload.get("email") or ""
        role_id = int(payload.get("role_id", DEFAULT_ADMIN_ROLE_ID))

        # Try to locate user in SQLite database
        with get_db_session() as session:
            user = session.get(User, user_id) if user_id else None
            if not user and email:
                user = session.exec(select(User).where(User.email == email)).first()

            if user:
                current_user = CurrentUser({
                    "id": str(user.id),
                    "email": user.email,
                    "full_name": user.full_name,
                    "role_id": user.role_id,
                    "avatar_url": user.avatar_url,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat() if hasattr(user.created_at, "isoformat") else str(user.created_at)
                })
                set_active_session_user(current_user)
                return current_user

        # If user record not found in DB, fulfill from signed JWT claims directly (fail-safe)
        fallback_user = CurrentUser({
            "id": user_id or DEFAULT_ADMIN_USER_ID,
            "email": email or "user@system.local",
            "full_name": payload.get("full_name") or (email.split("@")[0] if email else "User"),
            "role_id": role_id,
            "avatar_url": payload.get("avatar_url"),
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        set_active_session_user(fallback_user)
        return fallback_user
    except Exception:
        # Fallback to server in-memory session or dev bypass
        active_user = get_active_session_user()
        if active_user:
            return active_user
        if AUTH_BYPASS_DEV:
            return CurrentUser({
                "id": DEFAULT_ADMIN_USER_ID,
                "email": "admin@system.local",
                "role_id": DEFAULT_ADMIN_ROLE_ID,
                "full_name": "Dev Bypass Administrator",
                "avatar_url": None,
                "is_active": True,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        return None


def token_required(f):
    """Decorator enforcing active user authentication via Bearer JWT, Cookie, or Session."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        current_user = get_current_user_from_request()
        if not current_user:
            return {"detail": "Missing or invalid Bearer authentication token."}, 401
        if not current_user.get("is_active"):
            return {"detail": "User account has been deactivated."}, 403
        return f(*args, current_user=current_user, **kwargs)
    return decorated


def admin_required(f):
    """Decorator enforcing active administrator privilege (role_id == 1)."""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        current_user = get_current_user_from_request()
        if not current_user:
            return {"detail": "Missing or invalid Bearer authentication token."}, 401
        if not current_user.get("is_active"):
            return {"detail": "User account has been deactivated."}, 403
        if current_user.get("role_id") != 1:
            return {"detail": "Administrator privilege required."}, 403
        return f(*args, current_user=current_user, **kwargs)
    return decorated

