"""
cards.py — Flashcards Management Page.
Orchestrator for modular components in pages.cards_components.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List
from nicegui import ui

from components import (
    TOKENS,
    app_shell,
    network_error_banner,
    render_footer,
)
from pages.cards_components.card_form import render_add_card_panel
from pages.cards_components.card_grid import render_cards_filter_and_grid
from services import api
from services.auth_guard import get_current_user


async def render_cards_page() -> None:
    """Trang Quản lý Toàn bộ Flashcards riêng của User kèm đầy đủ chức năng CRUD."""
    with app_shell(active_tab="cards", title="EduFlash AI - Kho Thẻ Ghi Nhớ"):
        cur_user = get_current_user() or {}
        active_user_id = int(cur_user.get("id") or cur_user.get("user_id") or 1)

        filter_state: Dict[str, Any] = {
            "deck_id": "all",
            "search_query": "",
            "is_adding": False,
        }

        page_container = ui.column().classes("w-full gap-0")

        async def load_cards_data() -> None:
            if getattr(ui.context.client, "is_deleted", False):
                return
            page_container.clear()
            with page_container:
                cards_resp = await api.get_cards(user_id=active_user_id)
                decks_resp = await api.get_decks(user_id=active_user_id)

                if getattr(ui.context.client, "is_deleted", False):
                    return

                if api.is_connection_error(cards_resp) or api.is_connection_error(
                    decks_resp
                ):
                    network_error_banner(
                        on_retry=load_cards_data,
                        message="Không thể kết nối đến máy chủ Backend (Port 3000). Vui lòng thử lại.",
                    )
                    return

                all_cards: List[Dict[str, Any]] = (
                    cards_resp if isinstance(cards_resp, list) else []
                )
                all_decks: List[Dict[str, Any]] = (
                    decks_resp if isinstance(decks_resp, list) else []
                )

                decks_map: Dict[int, str] = {
                    d["id"]: d.get("title", f"Bộ #{d['id']}")
                    for d in all_decks
                    if "id" in d
                }

                # 1. Header & Actions
                with ui.row().classes(
                    "items-center justify-between w-full pb-6 border-b border-slate-200 flex-wrap gap-4"
                ):
                    with ui.column().classes("gap-1"):
                        with ui.row().classes("items-center gap-2.5"):
                            with ui.element("div").classes(
                                "w-10 h-10 rounded-2xl bg-amber-500 text-white flex items-center justify-center shadow-md shadow-amber-500/25"
                            ):
                                ui.icon("layers", size="24px")
                            ui.label("Kho Thẻ Ghi Nhớ").classes(
                                f"text-3xl font-black text-{TOKENS['text_primary']} tracking-tight"
                            )
                            ui.label(f"{len(all_cards)} thẻ").classes(
                                "text-xs font-bold px-3 py-1 rounded-full bg-amber-100 text-amber-800 border border-amber-200"
                            )
                        ui.label(
                            "Xem toàn bộ các thẻ flashcard bạn đã tạo, lọc theo bộ thẻ và thực hiện CRUD trực tiếp."
                        ).classes(f"text-sm text-{TOKENS['text_secondary']}")

                    with ui.row().classes("items-center gap-2 flex-wrap"):

                        def toggle_add_form():
                            filter_state["is_adding"] = not filter_state["is_adding"]
                            add_card_panel.set_visibility(filter_state["is_adding"])

                        ui.button(
                            "+ Thêm Thẻ Mới",
                            icon="add",
                            on_click=toggle_add_form,
                        ).classes(
                            f"bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold px-5 py-2.5 rounded-2xl "
                            "shadow-lg hover:shadow-indigo-500/25 transition duration-200 cursor-pointer text-sm"
                        )

                        ui.button(
                            "Ôn tập ngay (Focus Mode)",
                            icon="school",
                            on_click=lambda: ui.navigate.to("/study"),
                        ).props("outline").classes(
                            "text-amber-600 border-amber-300 bg-amber-50/60 font-bold px-4 py-2.5 rounded-2xl cursor-pointer text-sm"
                        )

                # 2. Form Thêm Thẻ Mới (Collapsible)
                add_card_panel = render_add_card_panel(
                    filter_state=filter_state,
                    all_decks=all_decks,
                    decks_map=decks_map,
                    on_card_created=load_cards_data,
                )

                # 3. Filter Bar & Grid
                render_cards_filter_and_grid(
                    all_cards=all_cards,
                    all_decks=all_decks,
                    decks_map=decks_map,
                    filter_state=filter_state,
                )

                render_footer()

        try:
            asyncio.get_running_loop()
            if not ui.context.client.has_socket_connection:
                await ui.context.client.connected()
        except RuntimeError:
            pass

        await load_cards_data()


__all__ = ["render_cards_page"]
