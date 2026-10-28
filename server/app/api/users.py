"""
users.py — Users & User Profiles CRUD API endpoints (Tag: Users & Profiles).
Orchestrator for modular route handlers in app.api.users_routes.
"""

from __future__ import annotations

from flask import Blueprint
from app.api.users_routes.user_crud import (
    create_user,
    delete_user_by_id,
    get_user_by_id,
    list_users,
    register_user_crud_routes,
    update_user_by_id,
)
from app.api.users_routes.user_profile import (
    get_user_profile_by_user_id,
    register_user_profile_routes,
    update_user_profile_by_user_id,
)
from app.api.users_routes.user_auth import (
    login_user_legacy,
    register_user_auth_routes,
)

users_bp = Blueprint("users", __name__, url_prefix="/api/users")

# Register all modular route handlers on users_bp
register_user_crud_routes(users_bp)
register_user_profile_routes(users_bp)
register_user_auth_routes(users_bp)

__all__ = [
    "users_bp",
    "list_users",
    "create_user",
    "get_user_by_id",
    "update_user_by_id",
    "delete_user_by_id",
    "get_user_profile_by_user_id",
    "update_user_profile_by_user_id",
    "login_user_legacy",
]
