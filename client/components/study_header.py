from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Set
from nicegui import ui

from components.layout import TOKENS


def render_study_header(
    deck_title: str,
    total_cards: int,
    available_tags: Set[str],
    selected_tag: Optional[str],
    on_tag_change: Callable[[str], Any],
    on_toggle_favorite: Callable[[], Any],
) -> Dict[str, Any]:
    """Render top progress, filter, tags, bookmark star, and close button for Focus Study."""
    with ui.column().classes("w-full gap-2 pt-2"):
        with ui.row().classes("items-center justify-between w-full flex-wrap gap-2"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("school", size="22px").classes(f"text-{TOKENS['primary']}")
                ui.label(deck_title).classes(
                    "font-extrabold text-base text-slate-900 tracking-tight truncate max-w-[220px]"
                )

            with ui.row().classes("items-center gap-2"):
                with ui.row().classes(
                    "items-center gap-1 px-3 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-700 font-black text-xs shadow-2xs"
                ):
                    ui.label("🔥")
                    ui.label("Streak: 3 ngày")

                bookmark_star_btn = ui.button(
                    icon="star_border",
                ).props("flat dense round").classes(
                    "text-slate-400 hover:text-amber-500 transition-colors"
                )
                bookmark_star_btn.on("click", on_toggle_favorite)

                ui.button(
                    icon="close",
                    on_click=lambda: ui.navigate.to("/decks"),
                ).props("flat dense round").classes(
                    "text-slate-400 hover:text-slate-700"
                ).tooltip("Kết thúc phiên học")

        if available_tags:
            with ui.row().classes(
                "items-center justify-between w-full bg-slate-50 border border-slate-200/80 rounded-xl px-3 py-1.5 text-xs"
            ):
                with ui.row().classes("items-center gap-1.5"):
                    ui.icon("label", size="14px").classes("text-slate-400")
                    ui.label("Lọc theo nhãn:").classes("font-bold text-slate-600")

                tag_options = {"all": "Tất cả các nhãn"}
                for t_item in sorted(list(available_tags)):
                    tag_options[t_item] = f"#{t_item}"

                ui.select(
                    options=tag_options,
                    value=selected_tag or "all",
                    on_change=lambda e: on_tag_change(e.value if hasattr(e, "value") else str(e)),
                ).props("dense outlined options-dense").classes("w-44 bg-white text-xs")

        progress_bar = (
            ui.linear_progress(
                value=1.0 / max(1, total_cards),
                show_value=False,
            )
            .props("rounded")
            .classes(f"w-full h-2 text-{TOKENS['primary']} bg-slate-100")
        )

        with ui.row().classes(
            "items-center justify-between w-full text-xs font-semibold text-slate-500"
        ):
            counter_label = ui.label(f"Thẻ 1 / {total_cards}")
            remaining_label = ui.label(f"Còn lại: {max(0, total_cards - 1)} thẻ")

    return {
        "bookmark_star_btn": bookmark_star_btn,
        "progress_bar": progress_bar,
        "counter_label": counter_label,
        "remaining_label": remaining_label,
    }

