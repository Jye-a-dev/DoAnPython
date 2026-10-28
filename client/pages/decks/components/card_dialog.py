"""
card_dialog.py — Modal popup for creating and editing Flashcards with Text-to-Speech (TTS).
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, Optional
from nicegui import ui

from components.layout import show_toast
from ..handlers.deck_actions import play_tts_speech, save_card_action


def open_card_dialog(
    deck_id: int,
    card: Optional[Dict[str, Any]] = None,
    on_saved: Optional[Callable[[], Any]] = None,
) -> None:
    """Modal dialog Thêm mới hoặc Chỉnh sửa Flashcard tích hợp cấu hình TTS."""
    is_edit = card is not None and bool(card.get("id"))
    card_id = int(card["id"]) if is_edit and card else None

    target_client = getattr(ui.context, "client", None)
    with target_client or ui.context.client:
        dlg = ui.dialog().props("maximized=false persistent=false")
        dlg.on("hide", dlg.delete)

    with dlg, ui.card().classes(
        "w-full max-w-lg p-6 rounded-3xl bg-white shadow-2xl border border-slate-100 gap-4"
    ):
        with ui.row().classes(
            "items-center justify-between w-full pb-2 border-b border-slate-100"
        ):
            title_text = f"Chỉnh sửa Thẻ #{card_id}" if is_edit else "Thêm Thẻ Mới"
            ui.label(title_text).classes("text-base font-black text-slate-900")
            ui.button(icon="close", on_click=dlg.close).props("flat dense round")

        q_input = (
            ui.textarea(
                label="Mặt trước (Question)",
                value=card.get("question", "") if card else "",
                placeholder="Nhập nội dung câu hỏi...",
            )
            .props("outlined dense rows=3")
            .classes("w-full bg-white")
        )
        a_input = (
            ui.textarea(
                label="Mặt sau (Answer)",
                value=card.get("answer", "") if card else "",
                placeholder="Nhập đáp án chuẩn...",
            )
            .props("outlined dense rows=3")
            .classes("w-full bg-white")
        )
        exp_input = (
            ui.input(
                label="Giải thích (Explanation)",
                value=(card.get("explanation") or "") if card else "",
                placeholder="Ghi chú thêm khái niệm hoặc ngữ cảnh...",
            )
            .props("outlined dense")
            .classes("w-full bg-white")
        )

        # Khối cấu hình Text-to-Speech (TTS)
        with ui.column().classes(
            "w-full gap-2 p-3 bg-slate-50 border border-slate-200 rounded-2xl"
        ):
            ui.label("Cấu hình Phát âm (Text-to-Speech)").classes(
                "text-xs font-bold text-slate-700 tracking-wide uppercase"
            )

            with ui.row().classes("w-full items-center gap-2"):
                tts_input = (
                    ui.input(
                        label="Văn bản phát âm (TTS)",
                        placeholder="Mặc định lấy từ Mặt trước nếu để trống",
                        value=(card.get("tts_text") or "") if card else "",
                    )
                    .props("outlined dense")
                    .classes("flex-1 bg-white")
                )

                def sync_question_to_tts():
                    val = (q_input.value or "").strip()
                    if val:
                        tts_input.value = val
                        show_toast("Đã đồng bộ Mặt trước vào ô TTS", "info")

                ui.button(icon="sync", on_click=sync_question_to_tts).props(
                    "flat round dense size=sm"
                ).classes("text-indigo-600 cursor-pointer").tooltip(
                    "Đồng bộ từ Mặt trước"
                )

                def preview_audio():
                    text = (tts_input.value or "").strip() or (
                        q_input.value or ""
                    ).strip()
                    if not text:
                        show_toast(
                            "Vui lòng nhập Mặt trước hoặc TTS text để nghe thử",
                            "warning",
                        )
                        return
                    lang = lang_select.value or "en-US"
                    play_tts_speech(text, lang)

                ui.button(icon="volume_up", on_click=preview_audio).props(
                    "flat round dense size=sm"
                ).classes(
                    "text-indigo-600 hover:text-indigo-800 cursor-pointer"
                ).tooltip(
                    "Nghe thử phát âm trực tiếp"
                )

            lang_select = (
                ui.select(
                    options={"en-US": "English (en-US)", "vi-VN": "Tiếng Việt (vi-VN)"},
                    value=(card.get("tts_lang") or "en-US") if card else "en-US",
                    label="Ngôn ngữ phát âm",
                )
                .props("outlined dense")
                .classes("w-full bg-white")
            )

        with ui.row().classes("w-full justify-end gap-2 pt-2"):
            ui.button("Hủy", on_click=dlg.close).props("flat dense").classes(
                "text-slate-500 text-xs font-bold cursor-pointer"
            )

            async def handle_submit():
                q = (q_input.value or "").strip()
                a = (a_input.value or "").strip()
                exp = (exp_input.value or "").strip() or None
                if not q or not a:
                    show_toast("Câu hỏi và đáp án không được để trống", "warning")
                    return

                tts_text = (tts_input.value or "").strip() or q
                tts_lang = lang_select.value or "en-US"

                res = await save_card_action(
                    deck_id=deck_id,
                    card_id=card_id,
                    question=q,
                    answer=a,
                    explanation=exp,
                    tts_text=tts_text,
                    tts_lang=tts_lang,
                )
                if isinstance(res, dict) and res.get("error"):
                    show_toast(res.get("message", "Lỗi lưu flashcard"), "negative")
                    return

                if is_edit and card:
                    card["question"] = q
                    card["answer"] = a
                    card["explanation"] = exp
                    card["tts_text"] = tts_text
                    card["tts_lang"] = tts_lang

                msg = (
                    "Đã cập nhật thẻ thành công!"
                    if is_edit
                    else "Đã thêm thẻ mới thành công!"
                )
                show_toast(msg, "positive")
                dlg.close()
                if on_saved:
                    saved_res = on_saved()
                    if asyncio.iscoroutine(saved_res):
                        await saved_res

            btn_label = "LƯU THAY ĐỔI" if is_edit else "THÊM THẺ MỚI"
            btn_icon = "save" if is_edit else "add"
            ui.button(btn_label, icon=btn_icon, on_click=handle_submit).classes(
                "bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-4 py-2 rounded-xl text-xs cursor-pointer"
            )

    dlg.open()


def open_card_editor_dialog(
    target_card: Dict[str, Any],
    on_saved: Optional[Callable[[], Any]] = None,
) -> None:
    """Tương thích ngược: mở dialog chỉnh sửa flashcard."""
    open_card_dialog(
        deck_id=int(target_card.get("deck_id") or 0),
        card=target_card,
        on_saved=on_saved,
    )
