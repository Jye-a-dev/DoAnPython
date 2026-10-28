"""
study_session_view.py — Study Session Focus Mode view and SM-2 action logic.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional, Set
from nicegui import ui

from components import (
    render_flashcard,
    render_srs_action_bar,
    show_toast,
)
from components.study_congrats import render_study_congrats
from components.study_header import render_study_header
from services import api


def render_study_session_view(
    study_container: ui.column,
    cards_pool: List[Dict[str, Any]],
    active_deck: Optional[Dict[str, Any]],
    available_tags: Set[str],
    selected_tag: Optional[str],
    card_fav_map: Dict[int, int],
    session_id: int,
    active_user_id: int,
    on_tag_change: Callable[[str], Any],
    on_session_finished: Optional[Callable[[], Any]] = None,
) -> None:
    """Render giao diện phiên học Focus Mode gồm Header, Card 3D Flip và SRS Bar."""
    total_cards = len(cards_pool)
    state = {
        "current_index": 0,
        "reviewed_count": 0,
        "card_controller": None,
        "is_animating": False,
    }

    with ui.column().classes("study-focus-container w-full max-w-2xl mx-auto gap-5"):
        deck_title = (
            active_deck.get("title")
            if active_deck
            else f"Phiên Ôn Tập ({total_cards} thẻ)"
        )

        async def handle_toggle_card_favorite() -> None:
            if state["current_index"] >= total_cards:
                return
            curr_card = cards_pool[state["current_index"]]
            cid = curr_card.get("id")
            if not cid:
                return

            if cid in card_fav_map:
                fid = card_fav_map[cid]
                res = await api.delete_favorite(fid)
                if isinstance(res, dict) and res.get("error"):
                    show_toast(res.get("message", "Lỗi hủy yêu thích"), "negative")
                else:
                    card_fav_map.pop(cid, None)
                    header_refs["bookmark_star_btn"].props("icon=star_border")
                    header_refs["bookmark_star_btn"].classes(
                        add="text-slate-400 hover:text-amber-500",
                        remove="text-amber-500",
                    )
                    header_refs["bookmark_star_btn"].tooltip("Thêm vào yêu thích")
                    show_toast("Đã bỏ thẻ khỏi danh sách yêu thích", "info")
            else:
                res = await api.add_favorite(user_id=active_user_id, card_id=cid)
                if isinstance(res, dict) and res.get("error"):
                    show_toast(res.get("message", "Lỗi thêm yêu thích"), "negative")
                else:
                    new_fid = res.get("id", 1) if isinstance(res, dict) else 1
                    card_fav_map[cid] = new_fid
                    header_refs["bookmark_star_btn"].props("icon=star")
                    header_refs["bookmark_star_btn"].classes(
                        add="text-amber-500",
                        remove="text-slate-400 hover:text-amber-500",
                    )
                    header_refs["bookmark_star_btn"].tooltip("Bỏ yêu thích thẻ này")
                    show_toast("Đã lưu thẻ vào mục yêu thích! ⭐", "positive")

        header_refs = render_study_header(
            deck_title=deck_title or "",
            total_cards=total_cards,
            available_tags=available_tags,
            selected_tag=selected_tag,
            on_tag_change=on_tag_change,
            on_toggle_favorite=handle_toggle_card_favorite,
        )

        card_slot = ui.column().classes(
            "card-transition-wrapper w-full items-center justify-center min-h-[340px] opacity-100 translate-x-0"
        )

        async def restart_session() -> None:
            state["current_index"] = 0
            state["reviewed_count"] = 0
            congrats_container.set_visibility(False)
            action_bar_ref["set_active"](True)
            action_bar_ref["container"].set_visibility(True)
            card_slot.set_visibility(True)
            await update_current_card_ui()

        congrats_container = render_study_congrats(
            total_cards=total_cards,
            on_restart=restart_session,
        )
        congrats_container.set_visibility(False)

        async def update_current_card_ui() -> None:
            card_slot.clear()
            idx = state["current_index"]
            if idx >= total_cards:
                await api.end_study_session(
                    session_id=session_id, total_reviewed=total_cards
                )
                card_slot.set_visibility(False)
                action_bar_ref["set_active"](False)
                action_bar_ref["container"].set_visibility(False)
                congrats_container.set_visibility(True)
                show_toast("Chúc mừng! Đã hoàn thành phiên ôn tập!", "positive")
                if on_session_finished:
                    on_session_finished()
                return

            header_refs["counter_label"].text = f"Thẻ {idx + 1} / {total_cards}"
            header_refs["remaining_label"].text = (
                f"Còn lại: {total_cards - idx - 1} thẻ"
            )
            header_refs["progress_bar"].set_value((idx + 1) / total_cards)

            current_card_data = cards_pool[idx]
            curr_cid = current_card_data.get("id")

            if curr_cid and curr_cid in card_fav_map:
                header_refs["bookmark_star_btn"].props("icon=star")
                header_refs["bookmark_star_btn"].classes(
                    add="text-amber-500",
                    remove="text-slate-400 hover:text-amber-500",
                )
                header_refs["bookmark_star_btn"].tooltip("Bỏ yêu thích thẻ này")
            else:
                header_refs["bookmark_star_btn"].props("icon=star_border")
                header_refs["bookmark_star_btn"].classes(
                    add="text-slate-400 hover:text-amber-500",
                    remove="text-amber-500",
                )
                header_refs["bookmark_star_btn"].tooltip("Lưu thẻ vào mục yêu thích")

            with card_slot:
                state["card_controller"] = render_flashcard(
                    card_data=current_card_data,
                    is_flipped_default=False,
                )

        async def handle_rating_submission(rating: int) -> None:
            if state["is_animating"] or state["current_index"] >= total_cards:
                return

            state["is_animating"] = True
            action_bar_ref["set_active"](False)

            current_card = cards_pool[state["current_index"]]
            card_id_val = current_card.get("id", 1)

            asyncio.create_task(
                api.submit_srs_review(
                    session_id=session_id,
                    card_id=card_id_val,
                    rating=rating,
                )
            )

            card_slot.classes(
                add="opacity-0 -translate-x-8",
                remove="opacity-100 translate-x-0",
            )
            await asyncio.sleep(0.18)

            state["current_index"] += 1
            state["reviewed_count"] += 1
            await update_current_card_ui()

            card_slot.classes(
                add="opacity-100 translate-x-0",
                remove="opacity-0 -translate-x-8",
            )
            await asyncio.sleep(0.1)

            state["is_animating"] = False
            if state["current_index"] < total_cards:
                action_bar_ref["set_active"](True)

        def handle_space_flip():
            if state["card_controller"]:
                state["card_controller"].toggle_flip()

        action_bar_ref = render_srs_action_bar(
            on_rating_callback=handle_rating_submission,
            is_active=True,
            on_space_pressed=handle_space_flip,
        )

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(update_current_card_ui())
        except RuntimeError:
            pass
