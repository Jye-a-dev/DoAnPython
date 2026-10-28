"""
api_decks.py — CATEGORIES, FOLDERS, DECKS & FAVORITES API Client Services.
Orchestrator for modular sub-services in services.decks.
"""

from __future__ import annotations

from services.decks.categories_service import (
    create_category,
    delete_category,
    get_categories,
    get_category_by_id,
    update_category,
)
from services.decks.folders_service import (
    create_folder,
    delete_folder,
    get_folder_by_id,
    get_folders,
    update_folder,
)
from services.decks.decks_service import (
    create_deck,
    delete_deck,
    get_deck_by_id,
    get_decks,
    update_deck,
)
from services.decks.favorites_service import (
    add_favorite,
    delete_favorite,
    get_favorite_by_id,
    get_favorites,
)

__all__ = [
    "get_categories",
    "get_category_by_id",
    "create_category",
    "update_category",
    "delete_category",
    "get_folders",
    "get_folder_by_id",
    "create_folder",
    "update_folder",
    "delete_folder",
    "get_decks",
    "get_deck_by_id",
    "create_deck",
    "update_deck",
    "delete_deck",
    "get_favorites",
    "get_favorite_by_id",
    "add_favorite",
    "delete_favorite",
]
