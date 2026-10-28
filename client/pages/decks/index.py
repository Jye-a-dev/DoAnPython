"""
index.py — Route entry point and main layout for Decks Library page (/decks).
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from nicegui import ui

from components import TOKENS, app_shell, network_error_banner, render_footer
from components.deck_dialogs import (
    render_create_category_dialog,
    render_create_folder_dialog,
)
from components.deck_sidebar import render_deck_sidebar
from components.deck_stats import render_deck_stats_cards
from services.auth_guard import get_current_user

from .components.deck_create_dialog import render_create_deck_modal
from .components.deck_list import render_deck_list_section
from .handlers.deck_actions import load_decks_overview


def _update_select_options(
    sel: Any, placeholder: str, items: List[Dict[str, Any]]
) -> None:
    sel.options = {None: placeholder}
    sel.options.update(
        {item["id"]: item.get("name", "") for item in items if "id" in item}
    )
    sel.update()


async def render_decks_page() -> None:
    """Trang Thư viện & Quản lý Bộ Thẻ, Categories, Folders, Favorites."""
    with app_shell(active_tab="decks", title="EduFlash AI - Thư Viện Bộ Thẻ"):
        cur_user = get_current_user() or {}
        active_user_id = int(cur_user.get("id") or cur_user.get("user_id") or 1)
        filter_state: Dict[str, Any] = {
            "tab": "all",
            "category_id": None,
            "folder_id": None,
        }

        cat_dialog_ref = render_create_category_dialog(
            active_user_id=active_user_id, on_created=lambda: load_decks_data()
        )
        folder_dialog_ref = render_create_folder_dialog(
            active_user_id=active_user_id, on_created=lambda: load_decks_data()
        )
        deck_dialog_ref = render_create_deck_modal(
            active_user_id=active_user_id, on_created=lambda: load_decks_data()
        )

        page_container = ui.column().classes("w-full gap-0")

        async def load_decks_data() -> None:
            if getattr(ui.context.client, "is_deleted", False):
                return
            page_container.clear()
            with page_container:
                data = await load_decks_overview(active_user_id)
                if getattr(ui.context.client, "is_deleted", False):
                    return

                if data.get("error"):
                    network_error_banner(
                        on_retry=load_decks_data,
                        message="Không thể kết nối đến máy chủ Backend (Port 3000). Vui lòng thử lại.",
                    )
                    return

                decks_list: List[Dict[str, Any]] = data["decks"]
                all_cards: List[Dict[str, Any]] = data["cards"]
                categories_list: List[Dict[str, Any]] = data["categories"]
                folders_list: List[Dict[str, Any]] = data["folders"]
                favorites_list: List[Dict[str, Any]] = data["favorites"]

                _update_select_options(
                    deck_dialog_ref["category_select"],
                    "-- Chọn Danh mục (Tùy chọn) --",
                    categories_list,
                )
                _update_select_options(
                    deck_dialog_ref["folder_select"],
                    "-- Chọn Thư mục (Tùy chọn) --",
                    folders_list,
                )
                _update_select_options(
                    folder_dialog_ref["cat_select"],
                    "-- Gắn vào Danh mục (Tùy chọn) --",
                    categories_list,
                )
                _update_select_options(
                    folder_dialog_ref["parent_select"],
                    "-- Thư mục gốc (Không có cha) --",
                    folders_list,
                )

                categories_map: Dict[Any, Any] = {
                    c["id"]: c for c in categories_list if "id" in c
                }
                folders_map: Dict[Any, Any] = {
                    f["id"]: f for f in folders_list if "id" in f
                }
                deck_fav_map: Dict[Any, int] = {
                    fav.get("deck_id"): fav.get("id", 0)
                    for fav in favorites_list
                    if fav.get("deck_id")
                }

                cards_by_deck: Dict[int, List[Dict[str, Any]]] = {}
                for c in all_cards:
                    cards_by_deck.setdefault(c.get("deck_id", 0), []).append(c)

                # Header thư viện & Nút tạo mới
                with ui.row().classes(
                    "items-center justify-between w-full pb-6 border-b border-slate-200 flex-wrap gap-4"
                ):
                    with ui.column().classes("gap-1"):
                        ui.label("Thư Viện Bộ Thẻ Học Tập").classes(
                            f"text-3xl font-black text-{TOKENS['text_primary']} tracking-tight"
                        )
                        ui.label(
                            "Quản lý toàn bộ danh mục, thư mục phân cấp và các bộ thẻ ghi nhớ thông minh."
                        ).classes(f"text-sm text-{TOKENS['text_secondary']}")

                    with ui.row().classes("items-center gap-2 flex-wrap"):
                        ui.button(
                            "+ Danh mục",
                            icon="palette",
                            on_click=cat_dialog_ref["open"],
                        ).props("outline").classes(
                            f"text-{TOKENS['primary']} border-{TOKENS['primary']} font-bold px-4 py-2.5 rounded-2xl cursor-pointer"
                        )
                        ui.button(
                            "+ Thư mục",
                            icon="create_new_folder",
                            on_click=folder_dialog_ref["open"],
                        ).props("outline").classes(
                            "text-indigo-600 border-indigo-200 bg-indigo-50/50 font-bold px-4 py-2.5 rounded-2xl cursor-pointer"
                        )
                        ui.button(
                            "+ Tạo Deck Mới",
                            icon="add",
                            on_click=deck_dialog_ref["open"],
                        ).classes(
                            f"bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold px-6 py-2.5 rounded-2xl shadow-lg cursor-pointer"
                        )

                # KPI thống kê
                render_deck_stats_cards(
                    category_count=len(categories_list),
                    folder_count=len(folders_list),
                    total_decks=len(decks_list),
                    fav_decks_count=len(deck_fav_map),
                    due_cards_count=sum(len(cs) for cs in cards_by_deck.values()),
                    on_due_click=lambda: ui.navigate.to("/cards"),
                )

                async def open_detail_modal(did: int) -> None:
                    from components.deck_manager_dialog import open_deck_manager_dialog

                    await open_deck_manager_dialog(did, on_refresh=load_decks_data)

                # Bố cục chính: Sidebar + Grid
                with ui.row().classes("w-full gap-6 items-start flex-col lg:flex-row"):
                    render_deck_sidebar(
                        categories_list=categories_list,
                        folders_list=folders_list,
                        decks_list=decks_list,
                        filter_state=filter_state,
                        on_filter_change=apply_sidebar_filter,
                        on_create_category=cat_dialog_ref["open"],
                        on_create_folder=folder_dialog_ref["open"],
                    )
                    render_deck_list_section(
                        decks_list=decks_list,
                        cards_by_deck=cards_by_deck,
                        categories_map=categories_map,
                        folders_map=folders_map,
                        deck_fav_map=deck_fav_map,
                        filter_state=filter_state,
                        active_user_id=active_user_id,
                        on_filter_tab=apply_tab_filter,
                        on_clear_sidebar_filter=lambda: apply_sidebar_filter(
                            None, None
                        ),
                        on_open_detail=open_detail_modal,
                        on_reload=load_decks_data,
                    )

                render_footer()

        def apply_sidebar_filter(
            category_id: Optional[int], folder_id: Optional[int]
        ) -> None:
            filter_state["category_id"] = category_id
            filter_state["folder_id"] = folder_id
            filter_state["tab"] = "all"
            asyncio.ensure_future(load_decks_data())

        def apply_tab_filter(tab_name: str) -> None:
            filter_state["tab"] = tab_name
            asyncio.ensure_future(load_decks_data())

        try:
            asyncio.get_running_loop()
            if not ui.context.client.has_socket_connection:
                await ui.context.client.connected()
        except RuntimeError:
            pass

        await load_decks_data()
