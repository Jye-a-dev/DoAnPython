from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from nicegui import ui

from components import (
    TOKENS,
    app_shell,
    empty_deck_state,
    network_error_banner,
    render_footer,
    show_toast,
)
from components.deck_card_editor import open_card_editor_dialog
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
                add_card_panel = ui.card().classes(
                    "w-full my-6 bg-slate-50 border border-slate-200 rounded-3xl p-5 md:p-6 gap-4 shadow-sm"
                )
                add_card_panel.set_visibility(False)

                with add_card_panel:
                    with ui.row().classes("items-center justify-between w-full"):
                        ui.label("TẠO FLASHCARD MỚI").classes(
                            "text-xs font-black text-slate-700 tracking-wider"
                        )
                        ui.button(
                            icon="close",
                            on_click=lambda: (
                                filter_state.update({"is_adding": False}),
                                add_card_panel.set_visibility(False),
                            ),
                        ).props("flat dense round").classes(
                            "text-slate-400 hover:text-slate-700"
                        )

                    with ui.row().classes("w-full gap-4 flex-col md:flex-row"):
                        q_input = (
                            ui.textarea(
                                label="Mặt trước: Câu hỏi / Khái niệm",
                                placeholder="Nhập nội dung cần ghi nhớ...",
                            )
                            .props("outlined dense rows=2")
                            .classes("flex-1 bg-white")
                        )

                        a_input = (
                            ui.textarea(
                                label="Mặt sau: Đáp án chuẩn",
                                placeholder="Nhập đáp án trả lời...",
                            )
                            .props("outlined dense rows=2")
                            .classes("flex-1 bg-white")
                        )

                    with ui.row().classes(
                        "w-full gap-4 flex-col md:flex-row items-center"
                    ):
                        deck_options: Dict[Any, str] = {
                            None: "-- Chưa gán bộ thẻ (Tự do) --"
                        }
                        deck_options.update(decks_map)
                        target_deck_select = (
                            ui.select(
                                options=deck_options,
                                value=all_decks[0]["id"] if all_decks else None,
                                label="Gắn vào Bộ thẻ (Tùy chọn)",
                            )
                            .props("outlined dense")
                            .classes("w-full md:w-72 bg-white")
                        )

                        exp_input = (
                            ui.input(
                                label="Giải thích / Mẹo ghi nhớ (Tùy chọn)",
                                placeholder="Ghi chú thêm...",
                            )
                            .props("outlined dense")
                            .classes("flex-1 bg-white")
                        )

                    with ui.row().classes(
                        "w-full justify-end items-center gap-2 pt-2 border-t border-slate-200"
                    ):
                        ui.button(
                            "Hủy",
                            on_click=lambda: (
                                filter_state.update({"is_adding": False}),
                                add_card_panel.set_visibility(False),
                            ),
                        ).props("flat dense").classes(
                            "text-slate-500 text-xs font-bold"
                        )

                        async def handle_create_card() -> None:
                            q_val = q_input.value.strip() if q_input.value else ""
                            a_val = a_input.value.strip() if a_input.value else ""
                            exp_val = (
                                exp_input.value.strip() if exp_input.value else None
                            )
                            d_val = target_deck_select.value

                            if not q_val or not a_val:
                                show_toast(
                                    "Vui lòng điền đủ câu hỏi và đáp án", "warning"
                                )
                                return

                            res = await api.create_card(
                                deck_id=d_val,
                                question=q_val,
                                answer=a_val,
                                explanation=exp_val,
                            )
                            if isinstance(res, dict) and "id" in res:
                                show_toast(
                                    "Đã thêm flashcard mới thành công!", "positive"
                                )
                                q_input.value = ""
                                a_input.value = ""
                                exp_input.value = ""
                                filter_state["is_adding"] = False
                                add_card_panel.set_visibility(False)
                                await load_cards_data()
                            else:
                                err = (
                                    res.get("message")
                                    if isinstance(res, dict)
                                    else "Lỗi tạo thẻ"
                                )
                                show_toast(err or "Lỗi tạo thẻ", "negative")

                        ui.button(
                            "Lưu Thẻ",
                            icon="save",
                            on_click=handle_create_card,
                        ).classes(
                            f"bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold px-6 py-2 rounded-xl text-xs cursor-pointer shadow-md"
                        )

                # 3. Filter Bar (Tìm kiếm & Dropdown Deck)
                with ui.row().classes(
                    "items-center justify-between w-full my-6 bg-white border border-slate-200 rounded-2xl p-3 shadow-2xs flex-wrap gap-3"
                ):
                    with ui.row().classes("items-center gap-3 flex-1 min-w-[280px]"):
                        search_in = (
                            ui.input(
                                placeholder="Tìm kiếm thẻ theo câu hỏi, đáp án...",
                                on_change=lambda e: (
                                    filter_state.update(
                                        {
                                            "search_query": (e.value or "")
                                            .strip()
                                            .lower()
                                        }
                                    ),
                                    render_cards_list(),
                                ),
                            )
                            .props("outlined dense clearable")
                            .classes("flex-1 text-xs bg-slate-50 rounded-xl")
                        )

                        filter_deck_opts: Dict[Any, str] = {
                            "all": "Tất cả bộ thẻ",
                            "unassigned": "Chưa gán bộ thẻ",
                        }
                        filter_deck_opts.update(
                            {
                                d["id"]: f"Bộ: {d.get('title')}"
                                for d in all_decks
                                if "id" in d
                            }
                        )

                        ui.select(
                            options=filter_deck_opts,
                            value="all",
                            on_change=lambda e: (
                                filter_state.update({"deck_id": e.value}),
                                render_cards_list(),
                            ),
                        ).props("outlined dense").classes(
                            "w-52 text-xs bg-slate-50 rounded-xl"
                        )

                cards_grid = ui.element("div").classes(
                    "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 w-full"
                )

                def render_cards_list() -> None:
                    cards_grid.clear()
                    q = filter_state["search_query"]
                    d_filter = filter_state["deck_id"]

                    filtered = all_cards
                    if d_filter == "unassigned":
                        filtered = [c for c in filtered if c.get("deck_id") is None]
                    elif d_filter != "all" and d_filter is not None:
                        filtered = [c for c in filtered if c.get("deck_id") == d_filter]

                    if q:
                        filtered = [
                            c
                            for c in filtered
                            if q in (c.get("question") or "").lower()
                            or q in (c.get("answer") or "").lower()
                            or q in (c.get("explanation") or "").lower()
                        ]

                    with cards_grid:
                        if not filtered:
                            with ui.column().classes(
                                "col-span-full py-16 items-center text-center gap-2 text-slate-400"
                            ):
                                ui.icon("inbox", size="42px")
                                ui.label(
                                    "Không tìm thấy thẻ ghi nhớ nào phù hợp."
                                ).classes("text-sm font-semibold")
                            return

                        for idx, card in enumerate(filtered):
                            card_id = card.get("id", 0)
                            card_deck_id = card.get("deck_id")
                            deck_name = (
                                decks_map.get(card_deck_id)
                                if card_deck_id
                                else "Chưa gán bộ thẻ"
                            )

                            with ui.card().classes(
                                "w-full bg-white border border-slate-200 rounded-2xl p-4 shadow-sm hover:shadow-md hover:border-indigo-300 transition-all flex flex-col justify-between gap-3"
                            ):
                                with ui.column().classes("w-full gap-2"):
                                    with ui.row().classes(
                                        "items-center justify-between w-full"
                                    ):
                                        ui.label(f"#{idx + 1} (ID: {card_id})").classes(
                                            "text-xs font-bold text-slate-400"
                                        )
                                        with ui.row().classes(
                                            "items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold "
                                            + (
                                                "bg-indigo-50 text-indigo-700 border border-indigo-200"
                                                if card_deck_id
                                                else "bg-amber-50 text-amber-700 border border-amber-200"
                                            )
                                        ):
                                            ui.icon("style", size="12px")
                                            ui.label(deck_name).classes(
                                                "truncate max-w-[120px]"
                                            )

                                    ui.label(card.get("question", "")).classes(
                                        "text-sm font-black text-slate-900 leading-snug line-clamp-3"
                                    )

                                    with ui.row().classes(
                                        "items-center gap-1.5 w-full"
                                    ):
                                        ui.label(
                                            f"Đáp án: {card.get('answer', '')}"
                                        ).classes(
                                            "text-xs font-semibold text-emerald-800 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-lg w-full line-clamp-2"
                                        )

                                    if card.get("explanation"):
                                        ui.label(f"💡 {card['explanation']}").classes(
                                            "text-xs text-slate-500 italic line-clamp-2"
                                        )

                                with ui.row().classes(
                                    "items-center justify-between w-full pt-2 border-t border-slate-100"
                                ):

                                    def make_delete_cb(cid=card_id):
                                        async def do_del():
                                            res = await api.delete_card(cid)
                                            if isinstance(res, dict) and res.get(
                                                "error"
                                            ):
                                                show_toast(
                                                    res.get("message", "Lỗi xóa thẻ"),
                                                    "negative",
                                                )
                                            else:
                                                show_toast(
                                                    "Đã xóa thẻ thành công", "info"
                                                )
                                                all_cards[:] = [
                                                    c
                                                    for c in all_cards
                                                    if c.get("id") != cid
                                                ]
                                                render_cards_list()

                                        return do_del

                                    ui.button(
                                        "Sửa",
                                        icon="edit",
                                        on_click=lambda c=card: open_card_editor_dialog(
                                            c, on_saved=render_cards_list
                                        ),
                                    ).props("flat dense").classes(
                                        "text-xs font-bold text-indigo-600 hover:bg-indigo-50 rounded-lg px-2 py-1"
                                    )

                                    ui.button(
                                        "Xóa",
                                        icon="delete",
                                        on_click=make_delete_cb(card_id),
                                    ).props("flat dense").classes(
                                        "text-xs font-bold text-rose-500 hover:bg-rose-50 rounded-lg px-2 py-1"
                                    )

                render_cards_list()
                render_footer()

        try:
            asyncio.get_running_loop()
            if not ui.context.client.has_socket_connection:
                await ui.context.client.connected()
        except RuntimeError:
            pass

        await load_cards_data()


__all__ = ["render_cards_page"]
