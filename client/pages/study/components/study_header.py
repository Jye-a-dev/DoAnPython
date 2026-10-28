"""
study_header.py — Thanh tiến trình, tiêu đề bộ thẻ và điều khiển điều hướng tại Focus Mode.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from nicegui import ui


def render_focus_header(
    deck_title: str,
    total_cards: int,
    on_exit: Optional[Callable[[], Any]] = None,
    on_toggle_favorite: Optional[Callable[[], Any]] = None,
    is_favorite: bool = False,
) -> Dict[str, Any]:
    """Render thanh header tối giản chế độ Focus Mode SM-2."""
    refs: Dict[str, Any] = {}

    with ui.column().classes("w-full max-w-xl mx-auto mb-4 gap-2"):
        with ui.row().classes("w-full items-center justify-between"):
            with ui.row().classes("items-center gap-2"):
                exit_func = on_exit or (lambda: ui.navigate.to("/study"))
                ui.button(icon="arrow_back", on_click=exit_func).props(
                    "flat round dense color=slate-6 size=sm"
                ).tooltip("Quay lại chọn bộ thẻ")

                with ui.column().classes("gap-0"):
                    ui.label(deck_title).classes(
                        "text-base font-bold text-slate-800 leading-tight truncate max-w-xs sm:max-w-md"
                    )
                    refs["remaining_label"] = ui.label(
                        f"Còn lại: {max(0, total_cards - 1)} thẻ"
                    ).classes("text-xs text-slate-400 font-medium")

            with ui.row().classes("items-center gap-3"):
                refs["counter_label"] = ui.label(f"1 / {total_cards}").classes(
                    "text-xs font-bold text-indigo-600 bg-indigo-50 border border-indigo-100 px-2 py-0.5 rounded-full"
                )
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
