from __future__ import annotations

"""Tầng dịch vụ API Client kết nối Backend RESTful (Port 3000).

Refactored thành kiến trúc module hóa:
- api_base: Connection pool AsyncClient, Error handling, Server config
- api_users: Users, Auth, User Profiles
- api_decks: Categories, Folders, Decks, Favorites
- api_cards: Cards, Tags, Card-Tag associations, AI Generation Gateway
- api_study: Documents, AI Logs, Study Sessions, SRS Reviews, Health check
"""

# 1. Base client, config & error handlers
from services.api_base import (
    BACKEND_API_URL,
    DEFAULT_TIMEOUT,
    HOST,
    PORT,
    _handle_http_error,
    close_client,
    get_client,
    is_connection_error,
)

# 2. Users & Profiles
from services.api_users import (
    auth_login,
    auth_register,
    create_profile,
    create_user,
    delete_profile,
    delete_user,
    get_profile_by_id,
    get_profiles,
    get_user_by_id,
    get_user_profile,
    get_users,
    login_user,
    update_profile,
    update_user,
)

# 3. Categories, Folders, Decks & Favorites
from services.api_decks import (
    add_favorite,
    create_category,
    create_deck,
    create_folder,
    delete_category,
    delete_deck,
    delete_favorite,
    delete_folder,
    get_categories,
    get_category_by_id,
    get_deck_by_id,
    get_decks,
    get_favorite_by_id,
    get_favorites,
    get_folder_by_id,
    get_folders,
    update_category,
    update_deck,
    update_folder,
)

# 4. Cards, Tags & Generation Gateway
from services.api_cards import (
    add_card_tag,
    create_card,
    create_cards_batch,
    create_tag,
    delete_all_cards,
    delete_card,
    delete_tag,
    generate_cards,
    generate_flashcards,
    get_card_by_id,
    get_card_tags,
    get_cards,
    get_tag_by_id,
    get_tags,
    get_tags_for_card,
    remove_card_tag,
    transcribe_audio,
    update_card,
    update_tag,
)

# 5. Documents, AI Logs, Study Sessions, Reviews & System Health
from services.api_study import (
    check_system_health,
    create_ai_log,
    create_study_session,
    delete_ai_log,
    delete_document,
    delete_study_review,
    delete_study_session,
    end_study_session,
    get_ai_log_by_id,
    get_ai_logs,
    get_document_by_id,
    get_documents,
    get_study_review_by_id,
    get_study_reviews,
    get_study_session_by_id,
    get_study_sessions,
    submit_srs_review,
    update_ai_log,
    update_document,
    upload_doc,
)

__all__ = [
    "BACKEND_API_URL",
    "DEFAULT_TIMEOUT",
    "HOST",
    "PORT",
    "get_client",
    "close_client",
    "_handle_http_error",
    "is_connection_error",
    # Users
    "get_users",
    "get_user_by_id",
    "create_user",
    "login_user",
    "auth_login",
    "auth_register",
    "update_user",
    "delete_user",
    # Profiles
    "get_profiles",
    "get_profile_by_id",
    "get_user_profile",
    "create_profile",
    "update_profile",
    "delete_profile",
    # Categories
    "get_categories",
    "get_category_by_id",
    "create_category",
    "update_category",
    "delete_category",
    # Folders
    "get_folders",
    "get_folder_by_id",
    "create_folder",
    "update_folder",
    "delete_folder",
    # Documents
    "upload_doc",
    "get_documents",
    "get_document_by_id",
    "update_document",
    "delete_document",
    # Decks
    "get_decks",
    "get_deck_by_id",
    "create_deck",
    "update_deck",
    "delete_deck",
    # Cards
    "get_cards",
    "get_card_by_id",
    "create_card",
    "create_cards_batch",
    "update_card",
    "delete_card",
    "delete_all_cards",
    # Tags & Card-Tags
    "get_tags",
    "get_tag_by_id",
    "create_tag",
    "update_tag",
    "delete_tag",
    "get_card_tags",
    "add_card_tag",
    "remove_card_tag",
    "get_tags_for_card",
    # AI Logs
    "get_ai_logs",
    "get_ai_log_by_id",
    "create_ai_log",
    "update_ai_log",
    "delete_ai_log",
    # Study Sessions & Reviews
    "get_study_sessions",
    "get_study_session_by_id",
    "create_study_session",
    "end_study_session",
    "delete_study_session",
    "get_study_reviews",
    "get_study_review_by_id",
    "submit_srs_review",
    "delete_study_review",
    # Favorites
    "get_favorites",
    "get_favorite_by_id",
    "add_favorite",
    "delete_favorite",
    # Generation & Health
    "generate_cards",
    "transcribe_audio",
    "generate_flashcards",
    "check_system_health",
]
