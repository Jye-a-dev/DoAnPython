"""
study.py — Study Sessions & Spaced Repetition (SM-2) Reviews API endpoints.
Orchestrator for modular route handlers in app.api.study_routes.
"""

from __future__ import annotations

from flask import Blueprint
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

study_bp = Blueprint("study", __name__, url_prefix="/api/study")

# Register all modular handlers on study_bp
register_session_routes(study_bp)
register_review_routes(study_bp)

__all__ = [
    "study_bp",
    "start_study_session",
    "get_study_session_by_id",
    "end_study_session",
    "list_study_sessions",
    "delete_study_session_by_id",
    "submit_study_review",
    "list_study_reviews",
    "get_study_review_by_id",
    "delete_study_review_by_id",
]
