"""
__init__.py — API Blueprints module exports.
"""

from __future__ import annotations

from app.api.ai_gateway import ai_gateway_bp, generator_bp
from app.api.ai_logs import ai_logs_bp
from app.api.analytics import analytics_bp
from app.api.auth import auth_bp
from app.api.cards import cards_bp
from app.api.categories import categories_bp
from app.api.deck_io import deck_io_bp
from app.api.decks import decks_bp
from app.api.documents import documents_bp
from app.api.favorites import favorites_bp
from app.api.folders import folders_bp
from app.api.profiles import profiles_bp
from app.api.study import study_bp
from app.api.system import system_bp
from app.api.tags import card_tags_bp, tags_bp
from app.api.users import users_bp

__all__ = [
    "ai_gateway_bp",
    "generator_bp",
    "ai_logs_bp",
    "analytics_bp",
    "auth_bp",
    "system_bp",
    "users_bp",
    "profiles_bp",
    "categories_bp",
    "folders_bp",
    "documents_bp",
    "decks_bp",
    "deck_io_bp",
    "cards_bp",
    "tags_bp",
    "card_tags_bp",
    "study_bp",
    "favorites_bp",
]
