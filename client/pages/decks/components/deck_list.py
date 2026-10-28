"""
deck_list.py — Grid display of decks with tabs, stats, and detail manager opening.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from components.deck_grid import render_decks_grid_section


def render_deck_list_section(
    decks_list: List[Dict[str, Any]],
    cards_by_deck: Dict[int, List[Dict[str, Any]]],
    categories_map: Dict[Any, Any],
    folders_map: Dict[Any, Any],
    deck_fav_map: Dict[Any, int],
    filter_state: Dict[str, Any],
    active_user_id: int,
    on_filter_tab: Callable[[str], Any],
    on_clear_sidebar_filter: Callable[[], Any],
    on_open_detail: Callable[[int], Any],
    on_reload: Callable[[], Any],
) -> None:
    """Render phần danh sách lưới bộ thẻ học tập (Decks Grid Section)."""
    render_decks_grid_section(
        decks_list=decks_list,
        cards_by_deck=cards_by_deck,
        categories_map=categories_map,
        folders_map=folders_map,
        deck_fav_map=deck_fav_map,
        filter_state=filter_state,
        active_user_id=active_user_id,
        on_filter_tab=on_filter_tab,
        on_clear_sidebar_filter=on_clear_sidebar_filter,
        on_open_detail=on_open_detail,
        on_reload=on_reload,
    )
