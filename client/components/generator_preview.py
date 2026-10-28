"""
generator_preview.py — AI Generator Flashcards Preview Checklist component.
Orchestrator for modular sub-components in components.generator_preview_components.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List
from nicegui import ui

from components.generator_preview_components.preview_actions import (
    render_preview_deck_selector,
)
from components.generator_preview_components.preview_card_item import (
    render_preview_card_item,
)
from components.layout import TOKENS


async def render_generator_preview(
    preview_container: ui.column,
    generated_cards_state: List[Dict[str, Any]],
    active_user_id: int,
    on_add_card: Callable[[], Any],
    on_reset: Callable[[], Any],
    on_rerender: Callable[[], Any],
) -> None:
    """Render preview cards list với Preview Checklist, batch-save workflow và TTS fields."""
    preview_container.clear()
    if not generated_cards_state:
        preview_container.set_visibility(False)
        return

    # Gán mặc định selected=True cho các thẻ chưa có trường selected
    for card in generated_cards_state:
        if "selected" not in card:
            card["selected"] = True

    preview_container.set_visibility(True)

    with preview_container:
        # Header Preview & Quick Actions
        with ui.row().classes(
            "w-full items-center justify-between pb-3 border-b border-slate-100 flex-wrap gap-4"
        ):
            with ui.row().classes("items-center gap-2"):
                ui.icon("check_circle", size="24px").classes("text-emerald-600")
                ui.label(
                    f"Xem trước {len(generated_cards_state)} Flashcards sinh từ AI"
                ).classes("text-lg font-bold text-slate-900")

            with ui.row().classes("items-center gap-2"):
                ui.button(
                    "+ Thêm thẻ thủ công",
                    icon="add",
                    on_click=on_add_card,
                ).props("flat dense").classes(
                    f"text-xs font-bold text-{TOKENS['primary']} hover:underline"
                )
                ui.button(
                    "Làm mới / Hủy",
                    icon="refresh",
                    on_click=on_reset,
                ).props(
                    "flat dense"
                ).classes("text-xs font-semibold text-rose-500 hover:underline")

        # Thanh thao tác: Select All + Đếm số đã chọn
        selection_state = {
            "select_all": all(c.get("selected", True) for c in generated_cards_state)
        }
        selected_count = sum(
            1 for c in generated_cards_state if c.get("selected", True)
        )
        total_count = len(generated_cards_state)

        with ui.row().classes(
            "w-full items-center gap-4 py-2 px-3 bg-slate-50 rounded-xl border border-slate-200"
        ):
            select_all_checkbox = ui.checkbox(
                "Chọn tất cả",
                value=selection_state["select_all"],
            ).classes("font-semibold text-slate-700")

            counter_label = ui.label(
                f"Đã chọn: {selected_count} / Tổng số: {total_count} thẻ"
            ).classes("text-sm text-slate-500 ml-auto")

        def _refresh_counter():
            cnt = sum(1 for c in generated_cards_state if c.get("selected", True))
            counter_label.text = (
                f"Đã chọn: {cnt} / Tổng số: {len(generated_cards_state)} thẻ"
            )

        async def on_select_all_change(e):
            new_val = e.value
            selection_state["select_all"] = new_val
            for card in generated_cards_state:
                card["selected"] = new_val
            _refresh_counter()
            await on_rerender()

        select_all_checkbox.on_value_change(on_select_all_change)

        # Save to Main Deck Card
        await render_preview_deck_selector(
            generated_cards_state=generated_cards_state,
            active_user_id=active_user_id,
        )

        # Card Items Grid
        with ui.element("div").classes("grid grid-cols-1 md:grid-cols-2 gap-4 w-full"):
            for idx, card in enumerate(generated_cards_state):
                render_preview_card_item(
                    idx=idx,
                    card=card,
                    generated_cards_state=generated_cards_state,
                    on_refresh_counter=_refresh_counter,
                    on_rerender=on_rerender,
                )


__all__ = ["render_generator_preview"]
