"""
deck_manager_dialog.py — Modal Quản lý Chi tiết Bộ Thẻ & CRUD Thẻ (Deck Detail & Card Manager Dialog).
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional
from nicegui import ui

from components.layout import show_toast
from services import api


async def open_deck_manager_dialog(
    deck_id: int, on_refresh: Optional[Callable[[], Any]] = None
) -> None:
    """Modal Quản lý Chi tiết Bộ Thẻ & CRUD Thẻ (Deck Detail & Card Manager Dialog)."""
    from components.deck_card_editor import confirm_delete_deck_dialog
    from pages.decks.components.card_dialog import open_card_dialog
    from pages.decks.components.card_item import render_card_item

    deck_info = await api.get_deck_by_id(deck_id)
    if isinstance(deck_info, dict) and deck_info.get("error"):
        show_toast(
            deck_info.get("message", f"Không tìm thấy bộ thẻ #{deck_id}"), "warning"
        )
        if on_refresh:
            res = on_refresh()
            if asyncio.iscoroutine(res):
                await res
        return

    deck_obj: Dict[str, Any] = (
        deck_info
        if isinstance(deck_info, dict)
        else {"id": deck_id, "title": f"Bộ thẻ #{deck_id}"}
    )
    cards_resp = await api.get_cards(deck_id=deck_id)
    raw_cards: List[Dict[str, Any]] = cards_resp if isinstance(cards_resp, list) else []
    cards_state: List[Dict[str, Any]] = list(raw_cards)

    state = {
        "title": deck_obj.get("title", f"Bộ thẻ #{deck_id}"),
        "search_query": "",
        "is_renaming": False,
    }

    target_client = getattr(ui.context, "client", None)
    with target_client or ui.context.client:
        dialog = ui.dialog().props("maximized=false persistent=false")
        dialog.on("hide", dialog.delete)

    with dialog, ui.card().classes(
        "w-full max-w-4xl p-6 md:p-8 rounded-3xl bg-white shadow-2xl border border-slate-100 "
        "gap-5 max-h-[90vh] flex flex-col overflow-hidden"
    ):
        header_row = ui.row().classes(
            "items-center justify-between w-full pb-4 border-b border-slate-100 flex-wrap gap-3"
        )
        action_bar = ui.row().classes(
            "items-center justify-between w-full gap-3 flex-wrap"
        )
        cards_scroll = ui.column().classes(
            "w-full max-h-96 overflow-y-auto space-y-3 pr-1"
        )

        async def trigger_refresh() -> None:
            if on_refresh:
                res = on_refresh()
                if asyncio.iscoroutine(res):
                    await res

        async def reload_cards() -> None:
            c_res = await api.get_cards(deck_id=deck_id)
            if isinstance(c_res, list):
                cards_state[:] = c_res
                render_header()
                render_cards()
                await trigger_refresh()

        def render_header() -> None:
            header_row.clear()
            with header_row:
                with ui.row().classes("items-center gap-3 flex-1 min-w-[280px]"):
                    with ui.element("div").classes(
                        "w-10 h-10 rounded-2xl bg-amber-50 text-amber-500 flex items-center justify-center shrink-0 border border-amber-100 shadow-2xs"
                    ):
                        ui.icon("style", size="22px")

                    if not state["is_renaming"]:
                        ui.label(state["title"]).classes(
                            "text-xl font-black text-slate-900 tracking-tight truncate max-w-sm md:max-w-md"
                        )
                        ui.button(
                            "✏️ Đổi tên",
                            on_click=lambda: (
                                state.update({"is_renaming": True}),
                                render_header(),
                            ),
                        ).props("flat dense").classes(
                            "text-xs font-bold text-indigo-600 hover:bg-indigo-50 rounded-lg px-2 py-1 cursor-pointer"
                        )
                    else:
                        title_input = (
                            ui.input(value=state["title"])
                            .props("outlined dense")
                            .classes("w-60 bg-white")
                        )

                        async def save_rename():
                            new_title = (
                                title_input.value.strip() if title_input.value else ""
                            )
                            if not new_title:
                                show_toast("Tên bộ thẻ không được để trống", "warning")
                                return
                            res = await api.update_deck(deck_id, title=new_title)
                            if isinstance(res, dict) and res.get("error"):
                                show_toast(
                                    res.get("message", "Lỗi đổi tên bộ thẻ"),
                                    "negative",
                                )
                            else:
                                state["title"] = new_title
                                deck_obj["title"] = new_title
                                state["is_renaming"] = False
                                show_toast(
                                    f"Đã đổi tên thành '{new_title}'", "positive"
                                )
                                render_header()
                                await trigger_refresh()

                        ui.button(icon="check", on_click=save_rename).props(
                            "flat dense round"
                        ).classes("text-emerald-600 hover:bg-emerald-50 cursor-pointer")
                        ui.button(
                            icon="close",
                            on_click=lambda: (
                                state.update({"is_renaming": False}),
                                render_header(),
                            ),
                        ).props("flat dense round").classes(
                            "text-slate-400 hover:bg-slate-100 cursor-pointer"
                        )

                    ui.label(f"{len(cards_state)} thẻ").classes(
                        "text-xs font-bold px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-200"
                    )
                    ui.label(f"{len(cards_state)} cần ôn").classes(
                        "text-xs font-bold px-2.5 py-1 rounded-full bg-amber-50 text-amber-600 border border-amber-200"
                    )

                with ui.row().classes("items-center gap-2"):

                    async def handle_delete_deck():
                        async def on_deck_deleted():
                            dialog.close()
                            await trigger_refresh()

                        await confirm_delete_deck_dialog(
                            deck_id, state["title"], on_deleted=on_deck_deleted
                        )

                    ui.button("🗑️ Xóa Bộ Thẻ", on_click=handle_delete_deck).props(
                        "flat dense"
                    ).classes(
                        "text-xs font-bold text-rose-500 hover:text-rose-700 hover:bg-rose-50 rounded-lg px-2 py-1 cursor-pointer"
                    )
                    ui.button(icon="close", on_click=dialog.close).props(
                        "flat dense round"
                    ).classes("text-slate-400 hover:text-slate-700 cursor-pointer")

        with action_bar:
            with ui.row().classes("items-center gap-2 flex-1 min-w-[280px]"):

                def open_add_modal():
                    open_card_dialog(deck_id=deck_id, card=None, on_saved=reload_cards)

                ui.button(
                    "+ Thêm Thẻ Mới", icon="add", on_click=open_add_modal
                ).classes(
                    "bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-4 py-2 rounded-xl text-xs cursor-pointer shadow-xs transition"
                )

                def on_search(e):
                    state["search_query"] = (e.value or "").strip().lower()
                    render_cards()

                ui.input(
                    placeholder="Tìm kiếm nhanh câu hỏi...",
                    on_change=on_search,
                ).props("outlined dense clearable").classes(
                    "flex-1 max-w-xs text-xs bg-slate-50 rounded-xl"
                )

            ui.button(
                "Ôn tập ngay (Focus Mode)",
                icon="bolt",
                on_click=lambda did=deck_id: ui.navigate.to(f"/study?deck_id={did}"),
            ).classes(
                "bg-amber-500 hover:bg-amber-600 text-white font-bold px-4 py-2 rounded-xl text-xs cursor-pointer shadow-md shadow-amber-500/20 transition"
            )

        def render_cards() -> None:
            cards_scroll.clear()
            q_filter = state["search_query"]
            displayed_cards = [
                c
                for c in cards_state
                if not q_filter or q_filter in (c.get("question") or "").lower()
            ]

            with cards_scroll:
                if not displayed_cards:
                    with ui.column().classes(
                        "w-full py-10 items-center text-center gap-2 text-slate-400"
                    ):
                        ui.icon("inbox", size="36px")
                        ui.label(
                            "Không tìm thấy thẻ nào phù hợp."
                            if q_filter
                            else "Bộ thẻ này hiện chưa có flashcard nào. Hãy bấm '+ Thêm Thẻ Mới' để bắt đầu."
                        ).classes("text-xs")
                    return

                for idx, card in enumerate(displayed_cards):

                    async def handle_delete_card(cid: int):
                        del_c_res = await api.delete_card(cid)
                        if isinstance(del_c_res, dict) and del_c_res.get("error"):
                            show_toast(
                                del_c_res.get("message", "Lỗi xóa thẻ"),
                                "negative",
                            )
                        else:
                            show_toast("Đã xóa thẻ thành công", "info")
                            cards_state[:] = [
                                c for c in cards_state if c.get("id") != cid
                            ]
                            render_header()
                            render_cards()
                            await trigger_refresh()

                    def handle_edit_card(c: Dict[str, Any]):
                        open_card_dialog(deck_id=deck_id, card=c, on_saved=reload_cards)

                    render_card_item(
                        idx=idx,
                        card=card,
                        on_edit=handle_edit_card,
                        on_delete=handle_delete_card,
                    )

        render_header()
        render_cards()
        dialog.open()
