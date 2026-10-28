"""
deck_create_dialog.py — Modal dialog for creating new Flashcard Decks.
"""
from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, Optional
from nicegui import ui
from components.layout import show_toast
from services import api


def render_create_deck_modal(
    active_user_id: int,
    on_created: Optional[Callable[[], Any]] = None,
) -> Dict[str, Any]:
    """Modal popup Tạo Deck Mới với lựa chọn Danh mục và Thư mục."""
    dlg = ui.dialog().props("maximized=false")
    with dlg, ui.card().classes(
        "w-full max-w-md p-6 rounded-3xl bg-white shadow-2xl border border-slate-100 gap-4"
    ):
        with ui.row().classes("items-center justify-between w-full pb-2 border-b border-slate-100"):
            ui.label("Tạo Bộ Thẻ Mới").classes("text-base font-black text-slate-900")
            ui.button(icon="close", on_click=dlg.close).props("flat dense round")

        title_in = ui.input(
            label="Tên bộ thẻ *", placeholder="VD: 3000 Từ vựng Oxford..."
        ).props("outlined dense").classes("w-full bg-white")
        desc_in = ui.textarea(
            label="Mô tả", placeholder="Ghi chú về nội dung..."
        ).props("outlined dense rows=2").classes("w-full bg-white")

        cat_sel = ui.select(
            options={None: "-- Chọn Danh mục (Tùy chọn) --"},
            value=None,
            label="Danh mục",
        ).props("outlined dense").classes("w-full bg-white")
        folder_sel = ui.select(
            options={None: "-- Chọn Thư mục (Tùy chọn) --"},
            value=None,
            label="Thư mục",
        ).props("outlined dense").classes("w-full bg-white")

        with ui.row().classes("w-full justify-end gap-2 pt-2"):
            ui.button("Hủy", on_click=dlg.close).props("flat dense").classes(
                "text-slate-500 font-bold text-xs"
            )

            async def do_create():
                t = (title_in.value or "").strip()
                if not t:
                    show_toast("Vui lòng nhập tên bộ thẻ", "warning")
                    return
                res = await api.create_deck(
                    user_id=active_user_id,
                    title=t,
                    description=(desc_in.value or "").strip() or None,
                    category_id=cat_sel.value,
                    folder_id=folder_sel.value,
                )
                if isinstance(res, dict) and res.get("error"):
                    show_toast(res.get("message", "Lỗi tạo bộ thẻ"), "negative")
                else:
                    show_toast(f"Đã tạo bộ thẻ '{t}' thành công!", "positive")
                    dlg.close()
                    title_in.value = ""
                    desc_in.value = ""
                    if on_created:
                        c_res = on_created()
                        if asyncio.iscoroutine(c_res):
                            await c_res

            ui.button("Tạo Deck", icon="add", on_click=do_create).classes(
                "bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-4 py-2 rounded-xl text-xs"
            )

    return {
        "dialog": dlg,
        "open": dlg.open,
        "close": dlg.close,
        "category_select": cat_sel,
        "folder_select": folder_sel,
    }

