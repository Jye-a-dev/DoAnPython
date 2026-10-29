"""
study_header.py — Thanh tiến trình, tiêu đề bộ thẻ và điều khiển điều hướng tại Focus Mode.
Tích hợp Đồng hồ Pomodoro 25/5 và Chế độ đảo ngược (Reverse Q&A).
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from nicegui import ui
from pages.study.components.pomodoro_timer import render_pomodoro_widget


def render_focus_header(
    deck_title: str,
    total_cards: int,
    on_exit: Optional[Callable[[], Any]] = None,
    on_toggle_favorite: Optional[Callable[[], Any]] = None,
    is_favorite: bool = False,
    on_toggle_reverse: Optional[Callable[[bool], Any]] = None,
    on_freeze_change: Optional[Callable[[bool], Any]] = None,
) -> Dict[str, Any]:
    """Render thanh header chế độ Focus Mode SM-2 kèm Pomodoro và Reverse toggle."""
    refs: Dict[str, Any] = {}

    with ui.column().classes("w-full max-w-xl mx-auto mb-3 gap-2"):
        # Hàng 1: Nút thoát, Tiêu đề Deck, Pomodoro Widget
        with ui.row().classes("w-full items-center justify-between flex-wrap gap-2"):
            with ui.row().classes("items-center gap-2"):
                exit_func = on_exit or (lambda: ui.navigate.to("/study"))
                ui.button(icon="arrow_back", on_click=exit_func).props(
                    "flat round dense color=slate-6 size=sm"
                ).tooltip("Quay lại chọn bộ thẻ")

                with ui.column().classes("gap-0"):
                    ui.label(deck_title).classes(
                        "text-base font-bold text-slate-800 leading-tight truncate max-w-[180px] sm:max-w-xs"
                    )
                    refs["remaining_label"] = ui.label(
                        f"Còn lại: {max(0, total_cards - 1)} thẻ"
                    ).classes("text-xs text-slate-400 font-medium")

            # Widget Pomodoro nhúng trực tiếp trên Header
            refs["pomodoro"] = render_pomodoro_widget(on_freeze_change=on_freeze_change)

        # Hàng 2: Progress bar, Counter, Toggle Chế độ đảo ngược
        with ui.row().classes(
            "w-full items-center justify-between pt-1 gap-2 flex-wrap"
        ):
            with ui.row().classes("items-center gap-3"):
                refs["counter_label"] = ui.label(f"1 / {total_cards}").classes(
                    "text-xs font-bold text-indigo-600 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded-full"
                )

                # Toggle Chế độ đảo ngược (Reverse Q&A)
                def handle_reverse_switch(e):
                    if on_toggle_reverse:
                        on_toggle_reverse(bool(e.value))

                rev_switch = (
                    ui.switch(
                        "Đảo ngược (Reverse Q&A)",
                        value=False,
                        on_change=handle_reverse_switch,
                    )
                    .props("dense size=xs color=amber")
                    .classes("text-xs font-bold text-slate-600")
                )
                rev_switch.tooltip(
                    "Hoán đổi: Hiển thị Đáp án làm câu hỏi để đoán lại Câu hỏi gốc"
                )
                refs["reverse_switch"] = rev_switch

            if on_toggle_favorite:
                icon_name = "star" if is_favorite else "star_border"
                color_prop = "text-amber-500" if is_favorite else "text-slate-400"
                fav_btn = (
                    ui.button(icon=icon_name, on_click=on_toggle_favorite)
                    .props(f"flat round dense size=sm")
                    .classes(color_prop)
                )
                refs["fav_btn"] = fav_btn

        init_prog = 1.0 / total_cards if total_cards > 0 else 0.0
        refs["progress_bar"] = (
            ui.linear_progress(value=init_prog)
            .props("size=6px rounded color=indigo-6 track-color=slate-2")
            .classes("w-full transition-all duration-300")
        )

    return refs
