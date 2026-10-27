from __future__ import annotations

from typing import Any, Callable
from nicegui import ui

from components.layout import TOKENS


def render_study_congrats(
    total_cards: int,
    on_restart: Callable[[], Any],
) -> ui.column:
    """Render completion card when user completes an SM-2 study session."""
    congrats_container = ui.column().classes(
        "w-full items-center text-center py-12 gap-5 bg-white border border-slate-200 rounded-3xl p-8 shadow-xl"
    )
    with congrats_container:
        with ui.element("div").classes(
            "w-20 h-20 rounded-3xl bg-emerald-50 text-emerald-600 flex items-center justify-center shadow-sm border border-emerald-200"
        ):
            ui.icon("emoji_events", size="44px")

        ui.label("Tuyệt Vời! Đã Hoàn Thành Phiên Ôn Tập").classes(
            "text-2xl font-black text-slate-900 tracking-tight"
        )

        ui.label(
            f"Bạn đã hoàn thành việc ôn luyện toàn bộ {total_cards} thẻ theo chu kỳ thuật toán SM-2. "
            "Khoảng cách ôn tập tiếp theo đã được hệ thống tính toán và tự động cập nhật."
        ).classes("text-sm text-slate-600 max-w-md leading-relaxed")

        with ui.row().classes(
            "items-center justify-center gap-6 py-4 w-full border-y border-slate-100 my-2"
        ):
            with ui.column().classes("items-center gap-0.5"):
                ui.label(str(total_cards)).classes("text-2xl font-black text-indigo-600")
                ui.label("Thẻ đã ôn").classes("text-xs font-semibold text-slate-500")

            with ui.column().classes("items-center gap-0.5"):
                ui.label("100%").classes("text-2xl font-black text-emerald-600")
                ui.label("Hoàn thành").classes("text-xs font-semibold text-slate-500")

            with ui.column().classes("items-center gap-0.5"):
                ui.label("🔥 +1").classes("text-2xl font-black text-amber-500")
                ui.label("Chuỗi Streak").classes("text-xs font-semibold text-slate-500")

        with ui.row().classes("gap-4 mt-2"):
            ui.button(
                "Xem Thư Viện Deck",
                icon="folder_special",
                on_click=lambda: ui.navigate.to("/decks"),
            ).classes(
                f"bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold px-6 py-2.5 rounded-xl shadow-md cursor-pointer"
            )

            ui.button(
                "Ôn Tập Lại Bộ Này",
                icon="replay",
                on_click=on_restart,
            ).props('text-color="black"').classes(
                "bg-white hover:bg-slate-100 !text-black text-black font-bold px-6 py-2.5 rounded-xl border border-slate-200 cursor-pointer"
            )

    return congrats_container

