"""
decks.py — Route entry point and reactive layout for Decks Library page (/decks).
Manages Categories, Folders, Deck Grid, and Real-time Favorites filtering.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional
from nicegui import ui

from components import TOKENS, app_shell, network_error_banner, render_footer
from components.deck_card import render_deck_card
from components.deck_detail_dialog import (
    build_category_options,
    build_folder_options,
    open_deck_detail_dialog,
)
from components.deck_dialogs import (
    render_create_category_dialog,
    render_create_folder_dialog,
)
from components.deck_sidebar import render_deck_sidebar
from components.deck_stats import render_deck_stats_cards
from components.feedback_states import empty_deck_state
from components.layout import show_toast
from services import api
from services.auth_guard import get_current_user

BTN_ACTIVE = "bg-indigo-600 text-white font-bold rounded-2xl px-5 py-2 shadow-sm transition-all duration-200 cursor-pointer"
BTN_INACTIVE = "text-indigo-600 hover:bg-indigo-50 font-semibold px-4 py-2 rounded-2xl transition-all duration-200 cursor-pointer"


def _set_select_options(select_elem: Any, options: Dict[Any, str]) -> None:
    """Cập nhật tùy chọn dropdown động cho ui.select."""
    if select_elem:
        select_elem.options = options
        select_elem.update()


async def render_decks_page() -> None:
    """Trang Thư viện & Quản lý Bộ Thẻ, Categories, Folders, Favorites."""
    with app_shell(active_tab="decks", title="EduFlash AI - Thư Viện Bộ Thẻ"):
        cur_user = get_current_user() or {}
        active_user_id = int(cur_user.get("id") or cur_user.get("user_id") or 1)

        try:
            page_client = ui.context.client
        except (RuntimeError, AttributeError):
            page_client = None

        filter_mode: str = "all"
        sidebar_category_id: Optional[int] = None
        sidebar_folder_id: Optional[int] = None

        decks_list: List[Dict[str, Any]] = []
        all_cards: List[Dict[str, Any]] = []
        categories_list: List[Dict[str, Any]] = []
        folders_list: List[Dict[str, Any]] = []
        favorites_list: List[Dict[str, Any]] = []
        deck_fav_map: Dict[int, int] = {}
        cards_by_deck: Dict[int, List[Dict[str, Any]]] = {}
        categories_map: Dict[Any, Any] = {}
        folders_map: Dict[Any, Any] = {}

        cat_dialog_ref = render_create_category_dialog(
            active_user_id=active_user_id,
            on_created=lambda: load_decks_data(),
        )
        folder_dialog_ref = render_create_folder_dialog(
            active_user_id=active_user_id,
            on_created=lambda: load_decks_data(),
        )

        try:
            from pages.decks.components.deck_create_dialog import render_create_deck_modal

            deck_dialog_ref = render_create_deck_modal(
                active_user_id=active_user_id,
                on_created=lambda: load_decks_data(),
            )
        except ImportError:
            from components.deck_dialogs import render_create_deck_dialog

            deck_dialog_ref = render_create_deck_dialog(
                active_user_id=active_user_id,
                on_created=lambda: load_decks_data(),
            )

        page_container = ui.column().classes("w-full gap-0")

        def refresh_decks_view() -> None:
            refresh_fn = getattr(render_decks_toolbar_and_content, "refresh", None)
            if callable(refresh_fn):
                refresh_fn()

        async def toggle_fav_handler(deck: Dict[str, Any]) -> None:
            did = deck.get("id")
            if not did:
                return
            is_currently_fav = (did in deck_fav_map) or bool(deck.get("is_favorite"))
            fid = deck_fav_map.get(did)
            dname = deck.get("title", f"Bộ thẻ #{did}")

            if hasattr(api, "toggle_favorite"):
                res = await api.toggle_favorite(
                    user_id=active_user_id,
                    deck_id=did,
                    fav_id=fid if is_currently_fav else None,
                )
            elif is_currently_fav and fid:
                res = await api.delete_favorite(fid)
            else:
                res = await api.add_favorite(user_id=active_user_id, deck_id=did)

            if isinstance(res, dict) and res.get("error"):
                show_toast(res.get("message", "Lỗi cập nhật yêu thích"), "negative")
                return

            if is_currently_fav:
                deck_fav_map.pop(did, None)
                deck["is_favorite"] = False
                show_toast(f"Đã bỏ '{dname}' khỏi mục yêu thích", "info")
            else:
                new_fav_id = res.get("id", 1) if isinstance(res, dict) else 1
                deck_fav_map[did] = new_fav_id
                deck["is_favorite"] = True
                show_toast(f"Đã thêm '{dname}' vào mục yêu thích! ⭐", "positive")

            refresh_decks_view()

        async def delete_deck_handler(did: int, title: str) -> None:
            del_resp = await api.delete_deck(did)
            if isinstance(del_resp, dict) and del_resp.get("error"):
                show_toast(del_resp.get("message", "Lỗi xóa bộ thẻ"), "negative")
                return
            show_toast(f"Đã xóa bộ thẻ '{title}'", "info")
            nonlocal decks_list
            decks_list = [d for d in decks_list if d.get("id") != did]
            deck_fav_map.pop(did, None)
            refresh_decks_view()

        async def open_detail_modal(did: int) -> None:
            """Mở dialog quản lý chi tiết bộ thẻ và thẻ học tập."""
            if page_client:
                with page_client:
                    await open_deck_detail_dialog(did, on_refresh=load_decks_data)
            else:
                await open_deck_detail_dialog(did, on_refresh=load_decks_data)

        def set_filter_mode(mode: str) -> None:
            nonlocal filter_mode
            filter_mode = mode
            refresh_decks_view()

        def apply_sidebar_filter(cat_id: Optional[int], fold_id: Optional[int]) -> None:
            nonlocal sidebar_category_id, sidebar_folder_id
            sidebar_category_id = cat_id
            sidebar_folder_id = fold_id
            refresh_decks_view()

        def _render_deck_item(deck: Dict[str, Any]) -> None:
            did = deck.get("id", 1)
            dcards = cards_by_deck.get(did, [])
            dcat = categories_map.get(deck.get("category_id"))
            dfolder = folders_map.get(deck.get("folder_id"))
            is_fav = (did in deck_fav_map) or bool(deck.get("is_favorite"))
            f_id = deck_fav_map.get(did)

            render_deck_card(
                deck=deck,
                deck_cards=dcards,
                deck_cat=dcat,
                deck_folder=dfolder,
                is_favorite=is_fav,
                fav_id=f_id,
                on_toggle_favorite=lambda d=deck: toggle_fav_handler(d),
                on_open_detail=lambda d_id=did: open_detail_modal(d_id),
                on_delete_deck=lambda d_id=did, d_title=deck.get("title", ""): delete_deck_handler(d_id, d_title),
            )

        def _render_deck_grid(items: List[Dict[str, Any]]) -> None:
            with ui.element("div").classes("grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5 w-full"):
                for deck in items:
                    _render_deck_item(deck)

        @ui.refreshable
        def render_decks_toolbar_and_content() -> None:
            fav_count = sum(1 for d in decks_list if (d.get("id") in deck_fav_map or d.get("is_favorite")))

            with ui.row().classes("items-center justify-between w-full bg-white border border-slate-200 rounded-2xl p-2 shadow-2xs flex-wrap gap-2"):
                with ui.row().classes("items-center gap-2 flex-wrap"):
                    ui.button("TẤT CẢ", icon="grid_view", on_click=lambda: set_filter_mode("all")).props("flat unelevated no-caps").classes(
                        BTN_ACTIVE if filter_mode == "all" else BTN_INACTIVE
                    )
                    ui.button(f"YÊU THÍCH (⭐ {fav_count})", icon="star", on_click=lambda: set_filter_mode("favorites")).props("flat unelevated no-caps").classes(
                        BTN_ACTIVE if filter_mode == "favorites" else BTN_INACTIVE
                    )
                    ui.button("THEO THƯ MỤC", icon="folder", on_click=lambda: set_filter_mode("folders")).props("flat unelevated no-caps").classes(
                        BTN_ACTIVE if filter_mode == "folders" else BTN_INACTIVE
                    )

                with ui.row().classes("items-center gap-2"):
                    if sidebar_category_id is not None:
                        cat_obj = categories_map.get(sidebar_category_id, {})
                        with ui.row().classes("items-center gap-1 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-bold border border-blue-200"):
                            ui.label(f"Môn: {cat_obj.get('name', '')}")
                            ui.button(icon="close", on_click=lambda: apply_sidebar_filter(None, None)).props("flat dense round").classes("text-blue-500 hover:text-blue-800 text-[10px]")

                    if sidebar_folder_id is not None:
                        fold_obj = folders_map.get(sidebar_folder_id, {})
                        with ui.row().classes("items-center gap-1 px-3 py-1 rounded-full bg-indigo-50 text-indigo-700 text-xs font-bold border border-indigo-200"):
                            ui.label(f"Thư mục: {fold_obj.get('name', '')}")
                            ui.button(icon="close", on_click=lambda: apply_sidebar_filter(None, None)).props("flat dense round").classes("text-indigo-500 hover:text-indigo-800 text-[10px]")

            filtered = decks_list
            if sidebar_category_id is not None:
                filtered = [d for d in filtered if d.get("category_id") == sidebar_category_id]
            if sidebar_folder_id is not None:
                filtered = [d for d in filtered if d.get("folder_id") == sidebar_folder_id]

            if filter_mode == "all":
                if not filtered:
                    empty_deck_state("Không tìm thấy bộ thẻ nào phù hợp!", "Hãy tạo bộ thẻ mới.", "folder_off", "Tạo Deck mới ngay", deck_dialog_ref["open"])
                else:
                    _render_deck_grid(filtered)

            elif filter_mode == "favorites":
                fav_decks = [d for d in filtered if (d.get("id") in deck_fav_map or d.get("is_favorite"))]
                if not fav_decks:
                    with ui.card().classes("w-full bg-amber-50/70 border border-amber-200/80 rounded-3xl p-8 text-center items-center justify-center gap-3 my-4 shadow-xs"):
                        ui.icon("star_outline", size="32px").classes("text-amber-500 mx-auto")
                        ui.label("Chưa có bộ thẻ yêu thích").classes("text-lg font-bold text-amber-900")
                        ui.label("Nhấn biểu tượng ⭐ để ghim bộ thẻ vào đây!").classes("text-sm text-amber-700 max-w-md mx-auto")
                else:
                    _render_deck_grid(fav_decks)

            elif filter_mode == "folders":
                by_folder: Dict[Optional[int], List[Dict[str, Any]]] = {}
                for d in filtered:
                    by_folder.setdefault(d.get("folder_id"), []).append(d)

                with ui.column().classes("w-full gap-4"):
                    has_folders = False
                    for folder in folders_list:
                        f_id = folder.get("id")
                        f_name = folder.get("name", "Thư mục không tên")
                        f_decks = by_folder.get(f_id, [])
                        has_folders = True

                        with ui.expansion(f"{f_name} ({len(f_decks)} bộ thẻ)", icon="folder", value=True).classes(
                            "w-full bg-white border border-slate-200 rounded-2xl shadow-xs overflow-hidden"
                        ):
                            if not f_decks:
                                ui.label("Chưa có bộ thẻ nào trong thư mục này.").classes("text-xs text-slate-400 italic p-4")
                            else:
                                with ui.element("div").classes("p-4"):
                                    _render_deck_grid(f_decks)

                    unclass = by_folder.get(None, [])
                    if unclass or not has_folders:
                        with ui.expansion(f"Chưa phân loại ({len(unclass)} bộ thẻ)", icon="folder_open", value=True).classes(
                            "w-full bg-white border border-slate-200 rounded-2xl shadow-xs overflow-hidden"
                        ):
                            if not unclass:
                                ui.label("Tất cả bộ thẻ đã được phân loại vào thư mục.").classes("text-xs text-slate-400 italic p-4")
                            else:
                                with ui.element("div").classes("p-4"):
                                    _render_deck_grid(unclass)

        async def load_decks_data() -> None:
            if getattr(ui.context.client, "is_deleted", False):
                return
            page_container.clear()
            with page_container:
                d_resp = await api.get_decks(user_id=active_user_id)
                c_resp = await api.get_cards(user_id=active_user_id)
                cat_resp = await api.get_categories(user_id=active_user_id)
                f_resp = await api.get_folders(user_id=active_user_id)
                fav_resp = await api.get_favorites(user_id=active_user_id)

                if getattr(ui.context.client, "is_deleted", False):
                    return

                if any(api.is_connection_error(r) for r in [d_resp, c_resp, cat_resp, f_resp]):
                    network_error_banner(on_retry=load_decks_data, message="Không thể kết nối đến máy chủ Backend.")
                    return

                nonlocal decks_list, all_cards, categories_list, folders_list, favorites_list
                nonlocal deck_fav_map, cards_by_deck, categories_map, folders_map

                decks_list = d_resp if isinstance(d_resp, list) else []
                all_cards = c_resp if isinstance(c_resp, list) else []
                categories_list = cat_resp if isinstance(cat_resp, list) else []
                folders_list = f_resp if isinstance(f_resp, list) else []
                favorites_list = fav_resp if isinstance(fav_resp, list) else []

                cat_opts = build_category_options(categories_list)
                folder_opts = build_folder_options(folders_list)

                _set_select_options(deck_dialog_ref.get("category_select"), cat_opts)
                _set_select_options(deck_dialog_ref.get("folder_select"), folder_opts)
                _set_select_options(folder_dialog_ref.get("cat_select"), cat_opts)
                _set_select_options(folder_dialog_ref.get("parent_select"), folder_opts)

                categories_map = {c["id"]: c for c in categories_list if "id" in c}
                folders_map = {f["id"]: f for f in folders_list if "id" in f}
                deck_fav_map = {fav["deck_id"]: fav.get("id", 0) for fav in favorites_list if fav.get("deck_id")}
                for d in decks_list:
                    if d.get("id") in deck_fav_map:
                        d["is_favorite"] = True

                cards_by_deck = {}
                for c in all_cards:
                    cards_by_deck.setdefault(c.get("deck_id", 0), []).append(c)

                with ui.row().classes("items-center justify-between w-full pb-6 border-b border-slate-200 flex-wrap gap-4"):
                    with ui.column().classes("gap-1"):
                        ui.label("Thư Viện Bộ Thẻ Học Tập").classes(f"text-3xl font-black text-{TOKENS['text_primary']} tracking-tight")
                        ui.label("Quản lý toàn bộ danh mục, thư mục phân cấp và các bộ thẻ ghi nhớ thông minh.").classes(f"text-sm text-{TOKENS['text_secondary']}")

                    with ui.row().classes("items-center gap-2 flex-wrap"):
                        ui.button("+ Danh mục", icon="palette", on_click=cat_dialog_ref["open"]).props("outline").classes(
                            f"text-{TOKENS['primary']} border-{TOKENS['primary']} font-bold px-4 py-2.5 rounded-2xl cursor-pointer"
                        )
                        ui.button("+ Thư mục", icon="create_new_folder", on_click=folder_dialog_ref["open"]).props("outline").classes(
                            "text-indigo-600 border-indigo-200 bg-indigo-50/50 font-bold px-4 py-2.5 rounded-2xl cursor-pointer"
                        )
                        ui.button("+ Tạo Deck Mới", icon="add", on_click=deck_dialog_ref["open"]).classes(
                            f"bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold px-6 py-2.5 rounded-2xl shadow-lg cursor-pointer"
                        )

                fav_count = sum(1 for d in decks_list if d.get("id") in deck_fav_map or d.get("is_favorite"))
                render_deck_stats_cards(
                    category_count=len(categories_list),
                    folder_count=len(folders_list),
                    total_decks=len(decks_list),
                    fav_decks_count=fav_count,
                    due_cards_count=sum(len(cs) for cs in cards_by_deck.values()),
                    on_due_click=lambda: ui.navigate.to("/cards"),
                )

                with ui.row().classes("w-full gap-6 items-start flex-col lg:flex-row"):
                    render_deck_sidebar(
                        categories_list=categories_list,
                        folders_list=folders_list,
                        decks_list=decks_list,
                        filter_state={"category_id": sidebar_category_id, "folder_id": sidebar_folder_id, "tab": filter_mode},
                        on_filter_change=apply_sidebar_filter,
                        on_create_category=cat_dialog_ref["open"],
                        on_create_folder=folder_dialog_ref["open"],
                    )

                    with ui.column().classes("flex-1 w-full gap-5"):
                        render_decks_toolbar_and_content()

                render_footer()

        try:
            asyncio.get_running_loop()
            if not ui.context.client.has_socket_connection:
                await ui.context.client.connected()
        except RuntimeError:
            pass

        await load_decks_data()


open_deck_manager_dialog = open_deck_detail_dialog

__all__ = ["render_decks_page", "open_deck_manager_dialog", "open_deck_detail_dialog"]
