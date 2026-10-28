"""
card_form.py — Collapsible form panel for adding new flashcard.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from nicegui import ui

from components import TOKENS, show_toast
from services import api


def render_add_card_panel(
    filter_state: Dict[str, Any],
    all_decks: List[Dict[str, Any]],
    decks_map: Dict[int, str],
    on_card_created: Callable[[], Any],
) -> ui.card:
    """Tạo form thêm flashcard mới có thể đóng/mở."""
    add_card_panel = ui.card().classes(
        "w-full my-6 bg-slate-50 border border-slate-200 rounded-3xl p-5 md:p-6 gap-4 shadow-sm"
    )
    add_card_panel.set_visibility(False)

    with add_card_panel:
        with ui.row().classes("items-center justify-between w-full"):
            ui.label("TẠO FLASHCARD MỚI").classes(
                "text-xs font-black text-slate-700 tracking-wider"
            )
            ui.button(
                icon="close",
                on_click=lambda: (
                    filter_state.update({"is_adding": False}),
                    add_card_panel.set_visibility(False),
                ),
            ).props("flat dense round").classes("text-slate-400 hover:text-slate-700")

        with ui.row().classes("w-full gap-4 flex-col md:flex-row"):
            q_input = (
                ui.textarea(
                    label="Mặt trước: Câu hỏi / Khái niệm",
                    placeholder="Nhập nội dung cần ghi nhớ...",
                )
                .props("outlined dense rows=2")
                .classes("flex-1 bg-white")
            )

            a_input = (
                ui.textarea(
                    label="Mặt sau: Đáp án chuẩn",
                    placeholder="Nhập đáp án trả lời...",
                )
                .props("outlined dense rows=2")
                .classes("flex-1 bg-white")
            )

        with ui.row().classes("w-full gap-4 flex-col md:flex-row items-center"):
            deck_options: Dict[Any, str] = {None: "-- Chưa gán bộ thẻ (Tự do) --"}
            deck_options.update(decks_map)
            target_deck_select = (
                ui.select(
                    options=deck_options,
                    value=all_decks[0]["id"] if all_decks else None,
                    label="Gắn vào Bộ thẻ (Tùy chọn)",
                )
                .props("outlined dense")
                .classes("w-full md:w-72 bg-white")
            )

            exp_input = (
                ui.input(
                    label="Giải thích / Mẹo ghi nhớ (Tùy chọn)",
                    placeholder="Ghi chú thêm...",
                )
                .props("outlined dense")
                .classes("flex-1 bg-white")
            )

        with ui.row().classes(
            "w-full justify-end items-center gap-2 pt-2 border-t border-slate-200"
        ):
            ui.button(
                "Hủy",
                on_click=lambda: (
                    filter_state.update({"is_adding": False}),
                    add_card_panel.set_visibility(False),
                ),
            ).props("flat dense").classes("text-slate-500 text-xs font-bold")

            async def handle_create_card() -> None:
                q_val = q_input.value.strip() if q_input.value else ""
                a_val = a_input.value.strip() if a_input.value else ""
                exp_val = exp_input.value.strip() if exp_input.value else None
                d_val = target_deck_select.value

                if not q_val or not a_val:
                    show_toast("Vui lòng điền đủ câu hỏi và đáp án", "warning")
                    return

                res = await api.create_card(
                    deck_id=d_val,
                    question=q_val,
                    answer=a_val,
                    explanation=exp_val,
                )
                if isinstance(res, dict) and "id" in res:
                    show_toast("Đã thêm flashcard mới thành công!", "positive")
                    q_input.value = ""
                    a_input.value = ""
                    exp_input.value = ""
                    filter_state["is_adding"] = False
                    add_card_panel.set_visibility(False)
                    await on_card_created()
                else:
                    err = res.get("message") if isinstance(res, dict) else "Lỗi tạo thẻ"
                    show_toast(err or "Lỗi tạo thẻ", "negative")

            ui.button(
                "Lưu Thẻ",
                icon="save",
                on_click=handle_create_card,
            ).classes(
                f"bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold px-6 py-2 rounded-xl text-xs cursor-pointer shadow-md"
            )

    return add_card_panel
