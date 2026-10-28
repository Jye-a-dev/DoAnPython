"""
preview_actions.py — Batch save to deck selector and action bar for generator preview.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from nicegui import ui

from components.layout import TOKENS, show_toast
from services import api


async def render_preview_deck_selector(
    generated_cards_state: List[Dict[str, Any]],
    active_user_id: int,
) -> None:
    """Render Deck selection card and Batch-Save button."""
    decks_resp = await api.get_decks(user_id=active_user_id)
    existing_decks: List[Dict[str, Any]] = (
        decks_resp if isinstance(decks_resp, list) else []
    )
    deck_options = {
        d["id"]: d.get("title", f"Deck #{d['id']}")
        for d in existing_decks
        if isinstance(d, dict) and "id" in d
    }
    default_deck_id = list(deck_options.keys())[0] if deck_options else None

    with ui.card().classes(
        "w-full bg-slate-50 border border-slate-200/80 rounded-2xl p-4 gap-3"
    ):
        with ui.row().classes("items-center justify-between w-full flex-wrap gap-3"):
            with ui.row().classes("items-center gap-3 flex-1 min-w-[280px]"):
                ui.icon("folder", size="20px").classes(f"text-{TOKENS['primary']}")
                deck_select = (
                    ui.select(
                        options=deck_options,
                        value=default_deck_id,
                        label="Chọn Deck chính",
                    )
                    .props("outlined dense")
                    .classes("w-64 bg-white rounded-lg")
                )

                new_deck_input = (
                    ui.input(placeholder="Hoặc gõ tên Deck mới...")
                    .props("outlined dense")
                    .classes("w-64 bg-white rounded-lg")
                )

            save_all_btn = ui.button(
                "Lưu vào Deck chính",
                icon="save",
            ).classes(
                "bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-6 py-2.5 rounded-xl shadow-md transition duration-200 cursor-pointer"
            )

            async def save_to_deck() -> None:
                save_all_btn.props("loading disable")
                try:
                    target_deck_id = deck_select.value
                    new_name = (
                        new_deck_input.value.strip()
                        if new_deck_input.value
                        else ""
                    )

                    if new_name:
                        created_deck = await api.create_deck(
                            title=new_name, user_id=active_user_id
                        )
                        if (
                            isinstance(created_deck, dict)
                            and "id" in created_deck
                        ):
                            target_deck_id = created_deck["id"]
                            show_toast(
                                f"Đã tạo Deck mới: {new_name}",
                                "positive",
                            )
                        elif isinstance(created_deck, dict) and created_deck.get("error"):
                            show_toast(
                                created_deck.get("message", "Lỗi tạo Deck"),
                                "negative",
                            )
                            return

                    if not target_deck_id:
                        fallback_deck = await api.create_deck(
                            title="Bài học mới", user_id=active_user_id
                        )
                        target_deck_id = fallback_deck.get("id", 1)

                    cards_to_save = [
                        c for c in generated_cards_state if c.get("selected", True)
                    ]

                    if not cards_to_save:
                        show_toast(
                            "Vui lòng chọn ít nhất 1 thẻ để lưu!", "warning"
                        )
                        return

                    batch_payload = []
                    for c in cards_to_save:
                        q = c.get("question", "").strip()
                        a = c.get("answer", "").strip()
                        if not q or not a:
                            continue
                        batch_payload.append(
                            {
                                "question": q,
                                "answer": a,
                                "explanation": c.get("explanation", ""),
                                "difficulty": c.get("difficulty", "medium"),
                                "tts_text": c.get("tts_text") or q,
                                "tts_lang": c.get("tts_lang") or "en-US",
                                "tags": c.get("tags", []),
                            }
                        )

                    result = await api.create_cards_batch(
                        deck_id=target_deck_id,
                        cards=batch_payload,
                    )

                    if isinstance(result, dict) and result.get("error"):
                        show_toast(
                            result.get("message", "Lỗi khi lưu thẻ hàng loạt"),
                            "negative",
                        )
                        return

                    saved_count = (
                        result.get("created_count", len(batch_payload))
                        if isinstance(result, dict)
                        else len(batch_payload)
                    )

                    generated_cards_state.clear()
                    show_toast(
                        f"Đã lưu thành công {saved_count} thẻ vào Deck #{target_deck_id}!",
                        "positive",
                    )
                    ui.navigate.to(f"/study?deck_id={target_deck_id}")
                except Exception as exc:
                    show_toast(f"Lỗi khi lưu thẻ vào Deck: {exc}", "negative")
                finally:
                    save_all_btn.props(remove="loading disable")

            save_all_btn.on_click(save_to_deck)

