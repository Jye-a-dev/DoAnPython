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
    """Dialog phụ chỉnh sửa nội dung câu hỏi/đáp án của flashcard."""
    edit_dlg = ui.dialog()
    with edit_dlg, ui.card().classes(
        "w-full max-w-lg p-6 rounded-3xl bg-white shadow-2xl border border-slate-100 gap-4"
    ):
        with ui.row().classes(
            "items-center justify-between w-full pb-2 border-b border-slate-100"
        ):
            ui.label(f"Chỉnh sửa Thẻ #{target_card.get('id')}").classes(
                "text-base font-black text-slate-900"
            )
            ui.button(icon="close", on_click=edit_dlg.close).props(
                "flat dense round"
            )

        edit_q_in = (
            ui.textarea(
                label="Mặt trước (Question)",
                value=target_card.get("question", ""),
            )
            .props("outlined dense rows=3")
            .classes("w-full bg-white")
        )
        edit_a_in = (
            ui.textarea(
                label="Mặt sau (Answer)",
                value=target_card.get("answer", ""),
            )
            .props("outlined dense rows=3")
            .classes("w-full bg-white")
        )
        edit_exp_in = (
            ui.input(
                label="Giải thích (Explanation)",
                value=target_card.get("explanation") or "",
            )
            .props("outlined dense")
            .classes("w-full bg-white")
        )

        with ui.row().classes("w-full justify-end gap-2 pt-2"):
            ui.button("Hủy", on_click=edit_dlg.close).props("flat dense").classes(
                "text-slate-500 text-xs font-bold cursor-pointer"
            )

            async def save_card_changes():
                q_e = edit_q_in.value.strip() if edit_q_in.value else ""
                a_e = edit_a_in.value.strip() if edit_a_in.value else ""
                exp_e = edit_exp_in.value.strip() if edit_exp_in.value else ""
                if not q_e or not a_e:
                    show_toast("Câu hỏi và đáp án không được rỗng", "warning")
                    return
                u_res = await api.update_card(
                    target_card.get("id", 0),
                    data={"question": q_e, "answer": a_e, "explanation": exp_e},
                )
                if isinstance(u_res, dict) and u_res.get("error"):
                    show_toast(
                        u_res.get("message", "Lỗi cập nhật thẻ"), "negative"
                    )
                else:
                    target_card["question"] = q_e
                    target_card["answer"] = a_e
                    target_card["explanation"] = exp_e
                    show_toast("Đã cập nhật thẻ thành công!", "positive")
                    edit_dlg.close()
                    if on_saved:
                        res = on_saved()
                        if asyncio.iscoroutine(res):
                            await res

            ui.button("Lưu thay đổi", icon="save", on_click=save_card_changes).classes(
                "bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-4 py-2 rounded-xl text-xs cursor-pointer"
            )
    edit_dlg.open()


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
            ui.button("Hủy", on_click=confirm_dlg.close).props(
                "flat dense"
            ).classes("text-slate-500 font-bold text-xs")

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

