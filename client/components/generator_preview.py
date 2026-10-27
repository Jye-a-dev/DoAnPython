from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional
from nicegui import ui

from components.layout import TOKENS, show_toast
from services import api


async def render_generator_preview(
    preview_container: ui.column,
    generated_cards_state: List[Dict[str, Any]],
    active_user_id: int,
    on_add_card: Callable[[], Any],
    on_reset: Callable[[], Any],
    on_rerender: Callable[[], Any],
) -> None:
    """Render preview cards list, deck selector, save-to-deck workflow, and tag chips."""
    preview_container.clear()
    if not generated_cards_state:
        preview_container.set_visibility(False)
        return

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
                ).props("flat dense").classes(
                    "text-xs font-semibold text-rose-500 hover:underline"
                )

        # Save to Main Deck Card
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

                        saved_count = 0
                        for c in generated_cards_state:
                            q = c.get("question", "").strip()
                            a = c.get("answer", "").strip()
                            exp = c.get("explanation", "").strip()
                            diff = c.get("difficulty", "Trung bình")
                            if not q or not a:
                                continue

                            saved_card_id: Optional[int] = None
                            if c.get("id"):
                                saved_card_id = c["id"]
                                await api.update_card(
                                    saved_card_id,
                                    question=q,
                                    answer=a,
                                    explanation=exp,
                                    difficulty=diff,
                                    deck_id=target_deck_id,
                                )
                            else:
                                card_res = await api.create_card(
                                    question=q,
                                    answer=a,
                                    explanation=exp,
                                    difficulty=diff,
                                    deck_id=target_deck_id,
                                )
                                if isinstance(card_res, dict) and "id" in card_res:
                                    saved_card_id = card_res["id"]

                            if saved_card_id and c.get("tags"):
                                for tag_item in c.get("tags", []):
                                    tag_str = (
                                        tag_item
                                        if isinstance(tag_item, str)
                                        else tag_item.get("name", "")
                                    ).strip()
                                    if tag_str:
                                        t_res = await api.create_tag(
                                            name=tag_str, user_id=active_user_id
                                        )
                                        tag_pk = (
                                            t_res.get("id")
                                            if isinstance(t_res, dict)
                                            else None
                                        )
                                        if tag_pk:
                                            await api.add_card_tag(
                                                card_id=saved_card_id,
                                                tag_id=tag_pk,
                                            )

                            saved_count += 1

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

        # Card Items Grid
        with ui.element("div").classes("grid grid-cols-1 md:grid-cols-2 gap-4 w-full"):
            for idx, card in enumerate(generated_cards_state):
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
                        with ui.row().classes("items-center justify-between w-full"):
                            ui.label(f"Thẻ #{idx + 1}").classes(
                                f"text-xs font-extrabold px-2.5 py-1 rounded-md bg-{TOKENS['primary_light']} text-{TOKENS['primary']}"
                            )

                            def make_delete_cb(target_idx: int, card_id: Optional[int]):
                                async def remove_card():
                                    if card_id:
                                        await api.delete_card(card_id)
                                    generated_cards_state.pop(target_idx)
                                    show_toast("Đã loại bỏ thẻ khỏi danh sách", "info")
                                    await on_rerender()

                                return remove_card

                            ui.button(
                                icon="delete_outline",
                                on_click=make_delete_cb(idx, card.get("id")),
                            ).props("flat dense round").classes(
                                "text-slate-400 hover:text-rose-600"
                            )

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

                        def bind_card_fields(
                            target_c=card,
                            qi=q_input,
                            ai=a_input,
                            ei=exp_input,
                        ):
                            target_c["question"] = qi.value
                            target_c["answer"] = ai.value
                            target_c["explanation"] = ei.value

                        q_input.on("blur", lambda: bind_card_fields())
                        a_input.on("blur", lambda: bind_card_fields())
                        exp_input.on("blur", lambda: bind_card_fields())

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
                                                if target_c.get("id"):
                                                    t_res = await api.create_tag(
                                                        name=t_str, user_id=active_user_id
                                                    )
                                                    t_id = t_res.get("id") if isinstance(t_res, dict) else None
                                                    if t_id:
                                                        await api.remove_card_tag(target_c["id"], t_id)
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
                                        if target_c.get("id"):
                                            t_res = await api.create_tag(
                                                name=tag_text, user_id=active_user_id
                                            )
                                            t_id = t_res.get("id") if isinstance(t_res, dict) else None
                                            if t_id:
                                                await api.add_card_tag(target_c["id"], t_id)
                                        show_toast(f"Đã gắn nhãn '{tag_text}'", "positive")
                                        inp.value = ""
                                        await on_rerender()

                                    return add_tag_to_card_action

                                add_tag_cb = make_add_preview_tag_cb()
                                tag_input_box.on("keydown.enter", add_tag_cb)
                                ui.button("+", on_click=add_tag_cb).props("flat dense").classes(
                                    f"text-xs font-bold text-{TOKENS['primary']}"
                                )

