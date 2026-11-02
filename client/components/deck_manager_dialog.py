"""
deck_manager_dialog.py — Re-export facade for Deck Detail & Card Manager Dialog.
"""

from __future__ import annotations

from components.deck_detail_dialog import (
    build_category_options,
    build_folder_options,
    open_deck_detail_dialog,
    open_deck_manager_dialog,
)

__all__ = [
    "open_deck_manager_dialog",
    "open_deck_detail_dialog",
    "build_category_options",
    "build_folder_options",
]
