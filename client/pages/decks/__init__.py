"""
decks — Module quản lý Thư viện Bộ thẻ, Categories, Folders và Flashcard CRUD với TTS.
"""

from __future__ import annotations

from pages.decks.components.card_dialog import open_card_dialog, open_card_editor_dialog


async def render_decks_page() -> None:
    """Entry point trang Decks với lazy import chống Circular Dependency."""
    from pages.decks.index import render_decks_page as _render_page

    await _render_page()


__all__ = [
    "render_decks_page",
    "open_card_dialog",
    "open_card_editor_dialog",
]
