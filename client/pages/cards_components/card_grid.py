"""
card_grid.py — Search filter bar and responsive flashcards grid.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from nicegui import ui

from components import show_toast
from components.deck_card_editor import open_card_editor_dialog
from services import api


def render_cards_filter_and_grid(
    all_cards: List[Dict[str, Any]],
    all_decks: List[Dict[str, Any]],
    decks_map: Dict[int, str],
    filter_state: Dict[str, Any],
) -> None:
    """Render thanh lọc/tìm kiếm cùng lưới hiển thị thẻ ghi nhớ kèm nút Edit & Delete."""
    with ui.row().classes(
        "items-center justify-between w-full my-6 bg-white border border-slate-200 rounded-2xl p-3 shadow-2xs flex-wrap gap-3"
    ):
        with ui.row().classes("items-center gap-3 flex-1 min-w-[280px]"):
            (
                ui.input(
                    placeholder="Tìm kiếm thẻ theo câu hỏi, đáp án...",
                    on_change=lambda e: (
                        filter_state.update(
                            {"search_query": (e.value or "").strip().lower()}
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
                {d["id"]: f"Bộ: {d.get('title')}" for d in all_decks if "id" in d}
            )

            ui.select(
                options=filter_deck_opts,
                value="all",
                on_change=lambda e: (
                    filter_state.update({"deck_id": e.value}),
                    render_cards_list(),
                ),
            ).props("outlined dense").classes("w-52 text-xs bg-slate-50 rounded-xl")

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
                    ui.label("Không tìm thấy thẻ ghi nhớ nào phù hợp.").classes(
                        "text-sm font-semibold"
                    )
                return

            for idx, card in enumerate(filtered):
                card_id = card.get("id", 0)
                card_deck_id = card.get("deck_id")
                deck_name = (
                    decks_map.get(card_deck_id) if card_deck_id else "Chưa gán bộ thẻ"
                )

                with ui.card().classes(
                    "w-full bg-white border border-slate-200 rounded-2xl p-4 shadow-sm hover:shadow-md hover:border-indigo-300 transition-all flex flex-col justify-between gap-3"
                ):
                    with ui.column().classes("w-full gap-2"):
                        with ui.row().classes("items-center justify-between w-full"):
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
                                ui.label(deck_name).classes("truncate max-w-[120px]")

                        ui.label(card.get("question", "")).classes(
                            "text-sm font-black text-slate-900 leading-snug line-clamp-3"
                        )

                        with ui.row().classes("items-center gap-1.5 w-full"):
                            ui.label(f"Đáp án: {card.get('answer', '')}").classes(
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
                                if isinstance(res, dict) and res.get("error"):
                                    show_toast(
                                        res.get("message", "Lỗi xóa thẻ"),
                                        "negative",
                                    )
                                else:
                                    show_toast("Đã xóa thẻ thành công", "info")
                                    all_cards[:] = [
                                        c for c in all_cards if c.get("id") != cid
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
