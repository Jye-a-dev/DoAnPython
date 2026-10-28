"""
deck_picker_view.py — Giao diện Chọn Bộ Thẻ (Deck Picker) tại /study.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from nicegui import ui


def render_deck_picker_view(
    decks: List[Dict[str, Any]],
    categories_map: Optional[Dict[int, str]] = None,
    on_select_deck: Optional[Callable[[Dict[str, Any]], Any]] = None,
) -> None:
    """Hiển thị danh sách các Deck hiện có dưới dạng lưới thẻ tương tác."""
    cats = categories_map or {}

    with ui.column().classes("w-full max-w-5xl mx-auto py-6 px-4 gap-6"):
        # Header banner
        with ui.column().classes("w-full items-start gap-1"):
            with ui.row().classes(
                "w-full items-center justify-between flex-wrap gap-2"
            ):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("school", size="30px").classes("text-indigo-600")
                    ui.label("Kho Ôn Tập Flashcard (SM-2)").classes(
                        "text-2xl font-black text-slate-900 tracking-tight"
                    )
                ui.button(
                    "Quản lý bộ thẻ",
                    icon="folder",
                    on_click=lambda: ui.navigate.to("/decks"),
                ).props("flat color=indigo-6 size=sm").classes(
                    "rounded-lg font-semibold"
                )

            ui.label(
                "Chọn bộ thẻ mục tiêu để bắt đầu phiên học tập trung với thuật toán ghi nhớ ngắt quãng tối ưu."
            ).classes("text-sm text-slate-500")

        if not decks:
            with ui.column().classes(
                "w-full items-center text-center p-12 bg-white rounded-2xl border border-slate-200/90 shadow-sm gap-3 mt-4"
            ):
                ui.icon("inventory_2", size="40px").classes("text-slate-300")
                ui.label("Chưa có bộ thẻ nào trong tài khoản").classes(
                    "text-lg font-bold text-slate-700"
                )
                ui.label(
                    "Tạo bộ thẻ mới tại thư viện Deck hoặc dùng AI Studio để tự động tạo flashcards."
                ).classes("text-sm text-slate-400 max-w-md")
                with ui.row().classes("gap-3 mt-2"):
                    ui.button(
                        "Tạo bộ thẻ mới",
                        icon="add",
                        on_click=lambda: ui.navigate.to("/decks"),
                    ).props("unelevated color=indigo-6").classes("rounded-xl px-4")
                    ui.button(
                        "Đến AI Studio",
                        icon="auto_awesome",
                        on_click=lambda: ui.navigate.to("/"),
                    ).props("outline color=indigo-6").classes("rounded-xl px-4")
            return

        # Grid danh sách bộ thẻ
        with ui.grid().classes(
            "w-full grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mt-2"
        ):
            for deck in decks:
                deck_id = deck.get("id")
                deck_title = deck.get("title", "Bộ thẻ không tên")
                deck_desc = deck.get("description") or "Chưa có mô tả chi tiết."
                card_count = int(deck.get("card_count", 0))
                cat_id = deck.get("category_id")
                cat_name = cats.get(cat_id, "Tổng hợp") if cat_id else "Tổng hợp"

                def make_click_handler(d=deck):
                    callback = on_select_deck
                    if callback is not None:
                        return lambda: callback(d)
                    return lambda: ui.navigate.to(f"/study/{d.get('id')}")

                with ui.card().classes(
                    "w-full p-5 bg-white border border-slate-200/90 rounded-2xl "
                    "shadow-sm hover:shadow-md hover:border-indigo-300 "
                    "transition-all duration-200 cursor-pointer flex flex-col justify-between h-52 group"
                ).on("click", make_click_handler(deck)):
                    # Top: Chủ đề & Số thẻ
                    with ui.row().classes("w-full items-center justify-between"):
                        with ui.row().classes(
                            "items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 text-xs font-semibold"
                        ):
                            ui.icon("category", size="13px")
                            ui.label(cat_name)

                        with ui.row().classes(
                            "items-center gap-1 text-xs text-slate-500 font-medium"
                        ):
                            ui.icon("style", size="14px").classes("text-slate-400")
                            ui.label(f"{card_count} thẻ")

                    # Center: Tiêu đề & mô tả
                    with ui.column().classes("w-full gap-1 my-2"):
                        ui.label(deck_title).classes(
                            "text-base font-bold text-slate-800 line-clamp-1 group-hover:text-indigo-600 transition-colors"
                        )
                        ui.label(deck_desc).classes(
                            "text-xs text-slate-500 line-clamp-2 leading-relaxed"
                        )

                    # Bottom: Nút bắt đầu học
                    with ui.row().classes(
                        "w-full items-center justify-between pt-2 border-t border-slate-100"
                    ):
                        ui.label("Bấm để học ngay").classes(
                            "text-[11px] text-slate-400 font-medium"
                        )
                        ui.button(
                            "Ôn tập",
                            icon="play_arrow",
                            on_click=make_click_handler(deck),
                        ).props("flat dense color=indigo-6 size=sm").classes(
                            "font-bold group-hover:translate-x-0.5 transition-transform"
                        )
