"""
study — Module quản lý chế độ ôn tập Lặp lại Ngắt quãng (SM-2) và Deck Picker.
"""

from __future__ import annotations

from pages.study.index import render_deck_picker, render_study_page

# Tương thích ngược với các import cũ nếu có
_category_icon = None
_run_random_two_level_selection = None
_show_category_selection_modal = None

__all__ = [
    "render_deck_picker",
    "render_study_page",
    "_category_icon",
    "_run_random_two_level_selection",
    "_show_category_selection_modal",
]
