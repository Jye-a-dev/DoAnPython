"""
components — Subcomponents for decks page.
"""
from __future__ import annotations

from .card_dialog import open_card_dialog, open_card_editor_dialog
from .card_item import render_card_item
from .deck_create_dialog import render_create_deck_modal
from .deck_list import render_deck_list_section

__all__ = [
    "open_card_dialog",
    "open_card_editor_dialog",
    "render_card_item",
    "render_create_deck_modal",
    "render_deck_list_section",
]

