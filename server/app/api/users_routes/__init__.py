"""
users_routes package — Modular route handlers for Users, Profiles, and Auth.
"""

from __future__ import annotations

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

__all__ = [
    "list_users",
    "create_user",
    "get_user_by_id",
    "update_user_by_id",
    "delete_user_by_id",
    "register_user_crud_routes",
    "get_user_profile_by_user_id",
    "update_user_profile_by_user_id",
    "register_user_profile_routes",
    "login_user_legacy",
    "register_user_auth_routes",
]

