"""
deck_card_editor.py — Dialogs for editing card content and confirming deck deletion.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, Optional
from nicegui import ui

from components.layout import show_toast
from services import api


async def open_card_editor_dialog(
    target_card: Dict[str, Any],
    on_saved: Optional[Callable[[], Any]] = None,
) -> None:
    """Dialog phụ chỉnh sửa nội dung câu hỏi/đáp án/TTS của flashcard."""
    from pages.decks.components.card_dialog import open_card_dialog

    open_card_dialog(
        deck_id=int(target_card.get("deck_id") or 0),
        card=target_card,
        on_saved=on_saved,
    )


async def confirm_delete_deck_dialog(
    deck_id: int,
    deck_title: str,
    on_deleted: Optional[Callable[[], Any]] = None,
) -> None:
    """Popup xác nhận cảnh báo trước khi xóa vĩnh viễn toàn bộ Deck."""
    confirm_dlg = ui.dialog()
    with confirm_dlg, ui.card().classes(
        "p-6 rounded-3xl bg-white max-w-sm gap-4 border border-rose-100 shadow-xl"
    ):
        with ui.row().classes("items-center gap-3"):
            with ui.element("div").classes(
                "w-10 h-10 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center shrink-0"
            ):
                ui.icon("delete_forever", size="24px")
            ui.label("Xóa bộ thẻ này?").classes("text-lg font-black text-slate-900")
        ui.label(
            f"Bạn có chắc muốn xóa vĩnh viễn '{deck_title}'? Mọi thẻ ghi nhớ bên trong sẽ bị xóa hoàn toàn."
        ).classes("text-xs text-slate-500 leading-relaxed")
        with ui.row().classes("w-full justify-end gap-2 pt-2"):
            ui.button("Hủy", on_click=confirm_dlg.close).props("flat dense").classes(
                "text-slate-500 font-bold text-xs"
            )

            async def do_delete():
                confirm_dlg.close()
                del_res = await api.delete_deck(deck_id)
                if isinstance(del_res, dict) and del_res.get("error"):
                    show_toast(del_res.get("message", "Lỗi xóa bộ thẻ"), "negative")
                else:
                    show_toast(f"Đã xóa bộ thẻ '{deck_title}'", "info")
                    if on_deleted:
                        res = on_deleted()
                        if asyncio.iscoroutine(res):
                            await res

            ui.button("Xác nhận xóa", icon="delete", on_click=do_delete).classes(
                "bg-rose-600 text-white font-bold rounded-xl text-xs px-3 py-1.5 cursor-pointer"
            )
    confirm_dlg.open()
