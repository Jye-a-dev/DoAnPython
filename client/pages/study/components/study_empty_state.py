"""
study_empty_state.py — Giao diện hiển thị khi Deck không có flashcard nào.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Optional
from nicegui import ui


def render_study_empty_state(
    deck_title: Optional[str] = None,
    on_back_to_picker: Optional[Callable[[], None]] = None,
) -> None:
    """Hiển thị khối Empty State trực quan khi Deck chưa có thẻ học."""
    title_text = (
        f"Bộ thẻ '{deck_title}' chưa có thẻ học"
        if deck_title
        else "Deck này chưa có thẻ học"
    )

    with ui.column().classes(
        "w-full max-w-lg mx-auto my-12 items-center text-center p-8 "
        "bg-white rounded-2xl border border-slate-200/90 shadow-sm gap-4"
    ):
        with ui.element("div").classes(
            "w-16 h-16 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center text-2xl"
        ):
            ui.icon("style", size="32px")

        ui.label(title_text).classes("text-xl font-bold text-slate-800")
        ui.label(
            "Bộ thẻ này hiện chưa có nội dung nào để ôn tập. "
            "Bạn có thể bổ sung thẻ mới hoặc quay lại chọn một bộ thẻ khác."
        ).classes("text-sm text-slate-500 leading-relaxed max-w-md")

        with ui.row().classes("items-center gap-3 mt-4"):

            def handle_back():
                if on_back_to_picker:
                    on_back_to_picker()
                else:
                    ui.navigate.to("/study")

            ui.button(
                "Quay lại chọn Deck", icon="arrow_back", on_click=handle_back
            ).props("unelevated color=indigo-6").classes(
                "px-4 py-2 text-sm font-semibold rounded-xl"
            )

            ui.button(
                "Thêm thẻ mới",
                icon="add_circle_outline",
                on_click=lambda: ui.navigate.to("/cards"),
            ).props("outline color=indigo-6").classes(
                "px-4 py-2 text-sm font-semibold rounded-xl"
            )
