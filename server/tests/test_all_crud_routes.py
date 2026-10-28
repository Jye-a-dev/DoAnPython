"""
tests/test_all_crud_routes.py — Comprehensive test suite orchestrator for all 13 tables CRUD and Gateway endpoints.
"""

from __future__ import annotations

from tests.crud_suites.test_system_auth import (
    test_auth_and_users_profiles_crud,
    test_system_health,
    test_system_status,
)
from tests.crud_suites.test_resources import (
    test_categories_crud,
    test_decks_cards_tags_crud,
    test_documents_crud_and_blob_stream,
    test_favorites_crud,
    test_folders_crud,
)
from tests.crud_suites.test_study_ai import (
    test_ai_logs_crud,
    test_study_sessions_and_srs_sm2,
)

__all__ = [
    "test_system_health",
    "test_system_status",
    "test_auth_and_users_profiles_crud",
    "test_categories_crud",
    "test_folders_crud",
    "test_documents_crud_and_blob_stream",
    "test_decks_cards_tags_crud",
    "test_study_sessions_and_srs_sm2",
    "test_favorites_crud",
    "test_ai_logs_crud",
]
