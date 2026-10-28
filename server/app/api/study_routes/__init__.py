"""
study_routes package — Modular route handlers for Study Sessions and SRS Reviews.
"""

from __future__ import annotations

from app.api.study_routes.session_routes import (
    delete_study_session_by_id,
    end_study_session,
    get_study_session_by_id,
    list_study_sessions,
    register_session_routes,
    start_study_session,
)
from app.api.study_routes.review_routes import (
    delete_study_review_by_id,
    get_study_review_by_id,
    list_study_reviews,
    register_review_routes,
    submit_study_review,
)

__all__ = [
    "start_study_session",
    "get_study_session_by_id",
    "end_study_session",
    "list_study_sessions",
    "delete_study_session_by_id",
    "register_session_routes",
    "submit_study_review",
    "list_study_reviews",
    "get_study_review_by_id",
    "delete_study_review_by_id",
    "register_review_routes",
]

