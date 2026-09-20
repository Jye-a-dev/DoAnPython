import functools
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from flask import request

from server.core.config import JWT_ALGORITHM, JWT_SECRET
from server.database import get_db_session
from server.models.user import User


def create_access_token(user_id: int, email: str, role_id: int) -> str:
    """Generate signed JWT token valid for 7 days."""
    payload = {
        "sub": str(user_id),
        "user_id": user_id,
        "email": email,
        "role_id": role_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user_from_request() -> Optional[dict]:
    """Extract and validate bearer token, retrieving user attributes inside session."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("user_id") or payload.get("sub"))
        with get_db_session() as session:
            user = session.get(User, user_id)
            if not user:
                return None
            return {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "role_id": user.role_id,
                "avatar_url": user.avatar_url,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if hasattr(user.created_at, "isoformat") else str(user.created_at)
            }
    except Exception:
        return None


def token_required(f):
    """Decorator enforcing active user authentication via Bearer JWT."""
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

