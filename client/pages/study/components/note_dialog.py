"""
note_dialog.py — Modal chỉnh sửa ghi chú cá nhân / mẹo nhớ (Personal Notes / Side Annotation).
Chỉ cập nhật trường personal_notes mà không thay đổi câu hỏi/đáp án gốc.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Optional
from nicegui import ui
from components.layout import show_toast
from services import api


def open_card_note_dialog(
    card_id: int,
    current_notes: Optional[str] = None,
    on_saved: Optional[Callable[[str], Any]] = None,
) -> None:
    """Mở hộp thoại ghi chú cá nhân nhanh cho flashcard."""
    dialog = ui.dialog().props("maximized=false persistent=false")
    dialog.on("hide", dialog.delete)

    with dialog, ui.card().classes(
        "w-full max-w-md p-6 rounded-3xl bg-white shadow-2xl border border-slate-100 gap-4"
    ):
        with ui.row().classes("w-full items-center justify-between pb-2 border-b border-slate-100"):
            with ui.row().classes("items-center gap-2.5"):
                with ui.element("div").classes(
                    "w-9 h-9 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center border border-amber-100 shadow-2xs"
                ):
                    ui.icon("edit_note", size="22px")
                with ui.column().classes("gap-0"):
                    ui.label("Ghi chú cá nhân").classes("text-base font-extrabold text-slate-800")
                    ui.label(f"Thẻ #{card_id} • Mẹo nhớ & Annotation").classes("text-xs text-slate-400 font-medium")

            ui.button(icon="close", on_click=dialog.close).props("flat round dense").classes(
                "text-slate-400 hover:text-slate-700"
            )

        with ui.element("div").classes("p-3 rounded-xl bg-amber-50/60 border border-amber-200/60 text-xs text-amber-800"):
            ui.label("💡 Mẹo: Ghi lại liên tưởng, từ đồng nghĩa hoặc ngữ cảnh riêng của bạn để tăng khả năng nhớ lại theo thuật toán SM-2.")

        notes_input = (
            ui.textarea(
                label="Nội dung ghi chú cá nhân (Personal Notes)",
                value=current_notes or "",
                placeholder="Nhập mẹo nhớ riêng cho thẻ này...",
            )
            .props("outlined autogrow")
            .classes("w-full bg-slate-50 rounded-xl text-xs")
        )

        async def save_note():
            val = (notes_input.value or "").strip()
            save_btn.props("loading")
            try:
                res = await api.update_card_notes(card_id=card_id, personal_notes=val)
                if isinstance(res, dict) and res.get("error"):
                    show_toast(res.get("message") or "Không thể lưu ghi chú", "negative")
                else:
                    show_toast("Đã lưu ghi chú cá nhân thành công!", "positive")
                    dialog.close()
                    if on_saved:
                        cb = on_saved(val)
                        if asyncio.iscoroutine(cb):
                            await cb
            finally:
                save_btn.props(remove="loading")

        with ui.row().classes("w-full items-center justify-end gap-2 pt-2"):
            ui.button("HỦY", on_click=dialog.close).props("flat").classes("text-slate-500 font-bold text-xs")
            save_btn = ui.button("LƯU GHI CHÚ", icon="save", on_click=save_note).classes(
                "bg-amber-500 hover:bg-amber-600 text-white font-extrabold text-xs px-5 py-2 rounded-xl shadow-xs"
            )

    dialog.open()

