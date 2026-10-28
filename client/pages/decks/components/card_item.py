"""
card_item.py — Render individual card item row with TTS indicator and actions.
"""
from __future__ import annotations

from typing import Any, Callable, Dict
from nicegui import ui
from ..handlers.deck_actions import play_tts_speech


def render_card_item(
    idx: int,
    card: Dict[str, Any],
    on_edit: Callable[[Dict[str, Any]], Any],
    on_delete: Callable[[int], Any],
) -> None:
    """Render từng dòng thẻ trong danh sách Deck kèm icon TTS loa phát âm trực tiếp."""
    card_id = int(card.get("id") or 0)
    tts_text = (card.get("tts_text") or "").strip()
    tts_lang = (card.get("tts_lang") or "en-US").strip()

    with ui.card().classes(
        "w-full bg-white border border-slate-200 rounded-2xl p-4 shadow-2xs hover:border-indigo-200 transition-all gap-2"
    ):
        with ui.row().classes("items-start justify-between w-full gap-2"):
            with ui.column().classes("gap-1 flex-1"):
                with ui.row().classes("items-center gap-2 flex-wrap"):
                    ui.label(f"#{idx + 1}. {card.get('question', '')}").classes(
                        "text-sm font-black text-slate-800 leading-snug"
                    )
                    if tts_text:
                        spk_btn = ui.button(
                            icon="volume_up",
                            on_click=lambda c=card: play_tts_speech(
                                text=c.get("tts_text") or c.get("question") or "",
                                lang=c.get("tts_lang") or "en-US",
                            ),
                        ).props("flat round dense size=sm").classes(
                            "text-indigo-500 hover:text-indigo-700 cursor-pointer"
                        ).tooltip("Nghe phát âm thẻ")
                        spk_btn.on("click.stop", lambda: None)

                ui.label(f"Đáp án: {card.get('answer', '')}").classes(
                    "text-xs font-semibold text-emerald-800 bg-emerald-50 border border-emerald-200/60 px-2.5 py-1 rounded-lg inline-block"
                )
                if card.get("explanation"):
                    ui.label(f"💡 {card['explanation']}").classes(
                        "text-xs text-slate-500 italic mt-0.5"
                    )

            with ui.row().classes("items-center gap-1 shrink-0"):
                ui.button(
                    icon="edit",
                    on_click=lambda c=card: on_edit(c),
                ).props("flat dense round").classes(
                    "text-slate-400 hover:text-indigo-600 text-xs cursor-pointer"
                ).tooltip("Chỉnh sửa Thẻ")

                ui.button(
                    icon="delete",
                    on_click=lambda cid=card_id: on_delete(cid),
                ).props("flat dense round").classes(
                    "text-slate-400 hover:text-rose-600 text-xs cursor-pointer"
                ).tooltip("Xóa thẻ")

