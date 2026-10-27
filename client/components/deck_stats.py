from __future__ import annotations

from typing import Any, Callable, Optional
from nicegui import ui

from components.layout import TOKENS


def render_deck_stats_cards(
    category_count: int,
    folder_count: int,
    total_decks: int,
    fav_decks_count: int,
    due_cards_count: int,
    on_due_click: Optional[Callable[[], Any]] = None,
) -> None:
    """Render top 4 overview KPI stat cards for Decks library."""
    with ui.element("div").classes("grid grid-cols-1 md:grid-cols-4 gap-4 w-full my-6"):
        # Stat 1: Tổng số Danh mục
        with ui.card().classes(
            "bg-white border border-slate-200 rounded-2xl p-4 shadow-xs flex flex-row items-center justify-between"
        ):
            with ui.column().classes("gap-0.5"):
                ui.label("Danh mục môn").classes(
                    f"text-xs font-bold text-{TOKENS['text_secondary']} uppercase tracking-wider"
                )
                ui.label(str(category_count)).classes(
                    f"text-2xl font-black text-{TOKENS['text_primary']}"
                )
            with ui.element("div").classes(
                "w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center"
            ):
                ui.icon("category", size="22px")

        # Stat 2: Tổng số Thư mục
        with ui.card().classes(
            "bg-white border border-slate-200 rounded-2xl p-4 shadow-xs flex flex-row items-center justify-between"
        ):
            with ui.column().classes("gap-0.5"):
                ui.label("Thư mục bài học").classes(
                    f"text-xs font-bold text-{TOKENS['text_secondary']} uppercase tracking-wider"
                )
                ui.label(str(folder_count)).classes(
                    "text-2xl font-black text-indigo-600"
                )
            with ui.element("div").classes(
                "w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center"
            ):
                ui.icon("folder", size="22px")

        # Stat 3: Tổng số Deck & Yêu thích
        with ui.card().classes(
            "bg-white border border-slate-200 rounded-2xl p-4 shadow-xs flex flex-row items-center justify-between"
        ):
            with ui.column().classes("gap-0.5"):
                ui.label("Bộ thẻ / Yêu thích").classes(
                    f"text-xs font-bold text-{TOKENS['text_secondary']} uppercase tracking-wider"
                )
                ui.label(f"{total_decks} / {fav_decks_count} ⭐").classes(
                    "text-2xl font-black text-amber-600"
                )
            with ui.element("div").classes(
                "w-10 h-10 rounded-xl bg-amber-50 text-amber-500 flex items-center justify-center"
            ):
                ui.icon("star", size="22px")

        # Stat 4: Thẻ cần ôn hôm nay (Interactive Clickable Card)
        due_card = ui.card().classes(
            "bg-gradient-to-br from-amber-50 to-orange-50/50 border border-amber-200 rounded-2xl p-4 shadow-xs "
            "flex flex-row items-center justify-between cursor-pointer hover:shadow-md hover:border-amber-400 "
            "transition-all duration-200 select-none"
        )
        if on_due_click is not None:
            due_card.on("click", on_due_click)

        with due_card:
            with ui.column().classes("gap-0.5"):
                ui.label("Cần ôn tập").classes(
                    "text-xs font-bold text-amber-700 uppercase tracking-wider"
                )
                ui.label(f"{due_cards_count} thẻ").classes(
                    "text-2xl font-black text-amber-500"
                )
            with ui.element("div").classes(
                "w-10 h-10 rounded-xl bg-amber-500 text-white flex items-center justify-center shadow-md shadow-amber-500/30"
            ):
                ui.icon("alarm", size="22px")
