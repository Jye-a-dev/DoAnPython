"""
handlers — Quản lý deck_actions cho trang decks.
"""
from __future__ import annotations

from .deck_actions import (
    delete_card_action,
    delete_deck_action,
    load_decks_overview,
    play_tts_speech,
    save_card_action,
    update_deck_title,
)

__all__ = [
    "load_decks_overview",
    "save_card_action",
    "delete_card_action",
    "delete_deck_action",
    "update_deck_title",
    "play_tts_speech",
]

