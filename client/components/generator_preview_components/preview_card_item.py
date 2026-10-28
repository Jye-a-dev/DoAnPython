"""
preview_card_item.py — Individual flashcard card component for generator preview.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List
from nicegui import ui

from components.layout import TOKENS, show_toast


def render_preview_card_item(
    idx: int,
    card: Dict[str, Any],
    generated_cards_state: List[Dict[str, Any]],
    on_refresh_counter: Callable[[], Any],
    on_rerender: Callable[[], Any],
) -> None:
    """Render thẻ flashcard xem trước với trình soạn thảo inline, TTS, và tag chips."""
    # Chuẩn hoá tags
    raw_card_tags = card.get("tags", [])
    card_tags_normalized: List[str] = []
    for ct in raw_card_tags:
        if isinstance(ct, str) and ct.strip():
            card_tags_normalized.append(ct.strip())
        elif isinstance(ct, dict) and ct.get("name"):
            card_tags_normalized.append(str(ct["name"]).strip())
    card["tags"] = card_tags_normalized

    with ui.card().classes(
        "w-full bg-white border border-slate-200 rounded-2xl p-5 shadow-xs gap-3 hover:shadow-md transition-shadow relative flex flex-col justify-between"
    ):
        with ui.column().classes("w-full gap-3"):
            # Header thẻ: số thứ tự + checkbox chọn + nút xóa
            with ui.row().classes("items-center justify-between w-full"):
                with ui.row().classes("items-center gap-2"):
                    def make_select_cb(target_c=card):
                        def on_card_select_change(e):
                            target_c["selected"] = e.value
                            on_refresh_counter()
                        return on_card_select_change

                    card_checkbox = ui.checkbox(
                        value=card.get("selected", True),
                    ).classes("text-indigo-600")
                    card_checkbox.on_value_change(make_select_cb(card))

                    ui.label(f"Thẻ #{idx + 1}").classes(
                        f"text-xs font-extrabold px-2.5 py-1 rounded-md bg-{TOKENS['primary_light']} text-{TOKENS['primary']}"
                    )

                def make_delete_cb(target_idx: int):
                    async def remove_card():
                        if target_idx < len(generated_cards_state):
                            generated_cards_state.pop(target_idx)
                        show_toast("Đã loại bỏ thẻ khỏi danh sách", "info")
                        await on_rerender()
                    return remove_card

                ui.button(
                    icon="delete_outline",
                    on_click=make_delete_cb(idx),
                ).props("flat dense round").classes("text-slate-400 hover:text-rose-600")

            # Inputs chỉnh sửa nhanh
            q_input = (
                ui.textarea(
                    label="Câu hỏi",
                    value=card.get("question", ""),
                )
                .props("rows=2 outlined dense")
                .classes("w-full bg-slate-50/50 text-sm")
            )
            a_input = (
                ui.textarea(
                    label="Đáp án",
                    value=card.get("answer", ""),
                )
                .props("rows=2 outlined dense")
                .classes("w-full bg-slate-50/50 text-sm")
            )
            exp_input = (
                ui.input(
                    label="Giải thích chi tiết",
                    value=card.get("explanation", ""),
                )
                .props("outlined dense")
                .classes("w-full bg-slate-50/50 text-xs")
            )

            # Trường TTS
            with ui.row().classes("w-full items-end gap-2"):
                tts_input = (
                    ui.input(
                        label="Text to Speech:",
                        value=card.get("tts_text") or card.get("question", ""),
                    )
                    .props("outlined dense")
                    .classes("flex-1 bg-slate-50/50 text-xs")
                )
                tts_lang_select = (
                    ui.select(
                        options={"en-US": "🇺🇸 en-US", "vi-VN": "🇻🇳 vi-VN"},
                        value=card.get("tts_lang") or "en-US",
                        label="Ngôn ngữ",
                    )
                    .props("outlined dense")
                    .classes("w-32 bg-white")
                )

            def bind_card_fields(
                target_c=card,
                qi=q_input,
                ai=a_input,
                ei=exp_input,
                ti=tts_input,
                tl=tts_lang_select,
            ):
                target_c["question"] = qi.value
                target_c["answer"] = ai.value
                target_c["explanation"] = ei.value
                target_c["tts_text"] = ti.value
                target_c["tts_lang"] = tl.value

            q_input.on("blur", lambda: bind_card_fields())
            a_input.on("blur", lambda: bind_card_fields())
            exp_input.on("blur", lambda: bind_card_fields())
            tts_input.on("blur", lambda: bind_card_fields())
            tts_lang_select.on_value_change(lambda _: bind_card_fields())

            # Tags section
            with ui.column().classes("w-full gap-1.5 pt-2 border-t border-slate-100"):
                ui.label("Nhãn phân loại (Tags):").classes(
                    "text-[11px] font-bold text-slate-400 uppercase tracking-wider"
                )

                chips_row = ui.row().classes("items-center gap-1.5 flex-wrap w-full")
                with chips_row:
                    if not card["tags"]:
                        ui.label("Chưa có nhãn").classes("text-xs text-slate-400 italic")
                    else:
                        for tag_val in card["tags"]:
                            def make_remove_tag_cb(t_str: str, target_c=card):
                                async def remove_tag_action():
                                    if t_str in target_c["tags"]:
                                        target_c["tags"].remove(t_str)
                                    show_toast(f"Đã gỡ nhãn '{t_str}'", "info")
                                    await on_rerender()
                                return remove_tag_action

                            with ui.row().classes(
                                "items-center gap-1 px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200 text-xs font-medium cursor-pointer hover:bg-rose-50 hover:text-rose-600 hover:border-rose-200 transition-colors"
                            ).tooltip("Nhấp để xóa nhãn").on("click", make_remove_tag_cb(tag_val)):
                                ui.icon("label", size="11px").classes("text-slate-400")
                                ui.label(tag_val)
                                ui.icon("close", size="11px")

                with ui.row().classes("w-full items-center gap-2 mt-1"):
                    tag_input_box = (
                        ui.input(placeholder="+ Thêm nhãn (Enter)...")
                        .props("outlined dense")
                        .classes("flex-1 text-xs bg-slate-50")
                    )

                    def make_add_preview_tag_cb(target_c=card, inp=tag_input_box):
                        async def add_tag_to_card_action():
                            tag_text = inp.value.strip() if inp.value else ""
                            if not tag_text:
                                return
                            if tag_text not in target_c["tags"]:
                                target_c["tags"].append(tag_text)
                            show_toast(f"Đã gắn nhãn '{tag_text}'", "positive")
                            inp.value = ""
                            await on_rerender()
                        return add_tag_to_card_action

                    add_tag_cb = make_add_preview_tag_cb()
                    tag_input_box.on("keydown.enter", add_tag_cb)
                    ui.button("+", on_click=add_tag_cb).props("flat dense").classes(
                        f"text-xs font-bold text-{TOKENS['primary']}"
                    )

