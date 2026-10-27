from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional
from nicegui import ui

from components import (
    TOKENS,
    app_shell,
    network_error_banner,
    render_footer,
)
from components.deck_dialogs import (
    render_create_category_dialog,
    render_create_deck_dialog,
    render_create_folder_dialog,
)
from components.deck_grid import render_decks_grid_section
from components.deck_manager_dialog import open_deck_manager_dialog
from components.deck_sidebar import render_deck_sidebar
from components.deck_stats import render_deck_stats_cards
from services import api
from services.auth_guard import get_current_user


async def render_decks_page() -> None:
    """Trang Thư viện & Quản lý Deck (Flashcard Collections), Categories, Folders, Favorites."""
    with app_shell(active_tab="decks", title="EduFlash AI - Thư Viện Bộ Thẻ"):
        cur_user = get_current_user() or {}
        active_user_id = int(cur_user.get("id") or cur_user.get("user_id") or 1)

        filter_state: Dict[str, Any] = {
            "tab": "all",
            "category_id": None,
            "folder_id": None,
        }

        # Modals tạo danh mục, thư mục & deck mới
        cat_dialog_ref = render_create_category_dialog(
            active_user_id=active_user_id,
            on_created=lambda: load_decks_data(),
        )
        folder_dialog_ref = render_create_folder_dialog(
            active_user_id=active_user_id,
            on_created=lambda: load_decks_data(),
        )
        deck_dialog_ref = render_create_deck_dialog(
            active_user_id=active_user_id,
            on_created=lambda: load_decks_data(),
        )

        page_container = ui.column().classes("w-full gap-0")

        async def load_decks_data() -> None:
            """Tải dữ liệu decks, cards, categories, folders, favorites và render UI."""
            if getattr(ui.context.client, "is_deleted", False):
                return
            page_container.clear()
            with page_container:
                decks_resp = await api.get_decks(user_id=active_user_id)
                all_cards_resp = await api.get_cards(user_id=active_user_id)
                categories_resp = await api.get_categories(user_id=active_user_id)
                folders_resp = await api.get_folders(user_id=active_user_id)
                favorites_resp = await api.get_favorites(user_id=active_user_id)

                if getattr(ui.context.client, "is_deleted", False):
                    return

                if (
                    api.is_connection_error(decks_resp)
                    or api.is_connection_error(all_cards_resp)
                    or api.is_connection_error(categories_resp)
                    or api.is_connection_error(folders_resp)
                ):
                    network_error_banner(
                        on_retry=load_decks_data,
                        message="Không thể kết nối đến máy chủ Backend (Port 3000). Vui lòng kiểm tra lại tiến trình.",
                    )
                    return

                decks_list: List[Dict[str, Any]] = (
                    decks_resp if isinstance(decks_resp, list) else []
                )
                all_cards: List[Dict[str, Any]] = (
                    all_cards_resp if isinstance(all_cards_resp, list) else []
                )
                categories_list: List[Dict[str, Any]] = (
                    categories_resp if isinstance(categories_resp, list) else []
                )
                folders_list: List[Dict[str, Any]] = (
                    folders_resp if isinstance(folders_resp, list) else []
                )
                favorites_list: List[Dict[str, Any]] = (
                    favorites_resp if isinstance(favorites_resp, list) else []
                )

                # Cập nhật options cho các select trong Dialog tạo mới
                deck_dialog_ref["category_select"].options = {
                    None: "-- Chọn Danh mục (Tùy chọn) --"
                }
                deck_dialog_ref["category_select"].options.update(
                    {c["id"]: c.get("name", "") for c in categories_list if "id" in c}
                )
                deck_dialog_ref["category_select"].update()

                folder_dialog_ref["cat_select"].options = {
                    None: "-- Gắn vào Danh mục (Tùy chọn) --"
                }
                folder_dialog_ref["cat_select"].options.update(
                    {c["id"]: c.get("name", "") for c in categories_list if "id" in c}
                )
                folder_dialog_ref["cat_select"].update()

                deck_dialog_ref["folder_select"].options = {
                    None: "-- Chọn Thư mục (Tùy chọn) --"
                }
                deck_dialog_ref["folder_select"].options.update(
                    {f["id"]: f.get("name", "") for f in folders_list if "id" in f}
                )
                deck_dialog_ref["folder_select"].update()

                folder_dialog_ref["parent_select"].options = {
                    None: "-- Thư mục gốc (Không có cha) --"
                }
                folder_dialog_ref["parent_select"].options.update(
                    {f["id"]: f.get("name", "") for f in folders_list if "id" in f}
                )
                folder_dialog_ref["parent_select"].update()

                categories_map: Dict[Any, Any] = {
                    c["id"]: c for c in categories_list if "id" in c
                }
                folders_map: Dict[Any, Any] = {
                    f["id"]: f for f in folders_list if "id" in f
                }

                deck_fav_map: Dict[Any, int] = {}
                for fav in favorites_list:
                    d_id = fav.get("deck_id")
                    if d_id:
                        deck_fav_map[d_id] = fav.get("id", 0)

                cards_by_deck: Dict[int, List[Dict[str, Any]]] = {}
                for c in all_cards:
                    d_id = c.get("deck_id", 0)
                    cards_by_deck.setdefault(d_id, []).append(c)

                total_decks = len(decks_list)
                due_cards_count = sum(len(cards) for cards in cards_by_deck.values())

                # Xác định ID bộ thẻ ưu tiên cho widget tương tác Cần ôn tập
                primary_deck_id: Optional[int] = None
                for d in decks_list:
                    d_id = d.get("id")
                    if d_id and cards_by_deck.get(d_id):
                        primary_deck_id = d_id
                        break
                if primary_deck_id is None and decks_list:
                    primary_deck_id = decks_list[0].get("id")

                def handle_due_cards_click() -> None:
                    ui.navigate.to("/cards")

                # Header thư viện & Các nút tạo mới
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
                            f"bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold px-6 py-2.5 rounded-2xl "
                            "shadow-lg hover:shadow-indigo-500/25 transition duration-200 cursor-pointer"
                        )

                # 4 Thẻ KPI thống kê tổng quan
                render_deck_stats_cards(
                    category_count=len(categories_list),
                    folder_count=len(folders_list),
                    total_decks=total_decks,
                    fav_decks_count=len(deck_fav_map),
                    due_cards_count=due_cards_count,
                    on_due_click=handle_due_cards_click,
                )

                # Bố Cục Chính: Sidebar + Grid Bộ Thẻ
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

                    render_decks_grid_section(
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
                        on_open_detail=lambda did: open_deck_manager_dialog(
                            did, on_refresh=load_decks_data
                        ),
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


__all__ = ["render_decks_page", "open_deck_manager_dialog"]


__all__ = ["render_decks_page", "open_deck_manager_dialog"]
