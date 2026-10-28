"""
index.py — Entrypoint điều phối và gắn kết các sub-component của module Study.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from nicegui import ui

from components import app_shell, network_error_banner, show_toast
from components.study_congrats import render_study_congrats
from pages.study.components.deck_picker_view import render_deck_picker_view
from pages.study.components.study_empty_state import render_study_empty_state
from pages.study.components.study_header import render_focus_header
from pages.study.components.study_stage import create_study_stage
from pages.study.handlers.srs_handler import (
    complete_study_session,
    load_deck_cards,
    record_card_review,
    resolve_deck,
    start_study_session,
)
from services import api
from services.auth_guard import get_current_user


async def render_deck_picker() -> None:
    """Màn hình Chọn Bộ Thẻ tại route /study."""
    with app_shell(active_tab="study", title="EduFlash AI - Kho Ôn Tập SM-2"):
        cur_user = get_current_user() or {}
        active_user_id = int(cur_user.get("id") or cur_user.get("user_id") or 1)

        container = ui.column().classes("w-full")
        with container:
            spinner = ui.spinner("dots", size="lg", color="indigo").classes(
                "mx-auto my-16"
            )

        decks_resp = await api.get_decks(user_id=active_user_id)
        cats_resp = await api.get_categories(user_id=active_user_id)

        container.clear()
        with container:
            if api.is_connection_error(decks_resp):
                network_error_banner(
                    on_retry=render_deck_picker,
                    message="Không thể kết nối đến máy chủ Backend (Port 3000).",
                )
                return

            decks_list: List[Dict[str, Any]] = (
                decks_resp if isinstance(decks_resp, list) else []
            )
            cats_map: Dict[int, str] = {}
            if isinstance(cats_resp, list):
                for c in cats_resp:
                    if isinstance(c, dict) and "id" in c:
                        cats_map[c["id"]] = str(c.get("name", ""))

            render_deck_picker_view(
                decks=decks_list,
                categories_map=cats_map,
                on_select_deck=lambda d: ui.navigate.to(f"/study/{d.get('id')}"),
            )


async def render_study_page(
    deck_identifier: Optional[str | int] = None,
    deck_id: Optional[int] = None,
    tag: Optional[str] = None,
) -> None:
    """Entrypoint màn hình học: nếu chưa chọn Deck -> Picker; nếu có Deck -> Focus Mode."""
    target_ident = deck_identifier if deck_identifier is not None else deck_id
    if target_ident is None:
        await render_deck_picker()
        return

    with app_shell(active_tab="study", title="EduFlash AI - Phiên Ôn Tập SM-2"):
        cur_user = get_current_user() or {}
        active_user_id = int(cur_user.get("id") or cur_user.get("user_id") or 1)

        main_slot = ui.column().classes("w-full min-h-[500px]")
        with main_slot:
            ui.spinner("dots", size="lg", color="indigo").classes("mx-auto my-20")

        # 1. Giải mã Deck
        deck_obj, deck_err = await resolve_deck(target_ident, active_user_id)
        if deck_err or not deck_obj:
            main_slot.clear()
            with main_slot:
                render_study_empty_state(deck_title=str(target_ident))
            return

        resolved_id = int(deck_obj["id"])
        deck_title = deck_obj.get("title", "Bộ thẻ ôn tập")

        # 2. Tải danh sách thẻ
        cards_raw, cards_err = await load_deck_cards(resolved_id, active_user_id)
        if cards_err or cards_raw is None:
            main_slot.clear()
            with main_slot:
                network_error_banner(
                    on_retry=lambda: render_study_page(
                        deck_identifier=target_ident, tag=tag
                    ),
                    message=cards_err or "Lỗi tải danh sách thẻ ôn tập",
                )
            return

        # 3. Áp dụng bộ lọc Tag (nếu có)
        cards_state: List[Dict[str, Any]] = []
        for c in cards_raw:
            if not tag or tag == "all":
                cards_state.append(c)
            else:
                c_tags = [
                    t if isinstance(t, str) else t.get("name", "")
                    for t in c.get("tags", [])
                ]
                if any(t.lower() == tag.lower() for t in c_tags):
                    cards_state.append(c)

        # 4. Xử lý khi Deck rỗng
        if not cards_state:
            main_slot.clear()
            with main_slot:
                render_study_empty_state(deck_title=deck_title)
            return

        # 5. Khởi tạo phiên ôn tập và render Focus Mode
        total_count = len(cards_state)
        session_id = await start_study_session(resolved_id, active_user_id)
        state = {"current_index": 0}

        main_slot.clear()
        with main_slot:
            with ui.column().classes(
                "study-focus-container w-full max-w-2xl mx-auto gap-4 py-4"
            ):
                header_refs = render_focus_header(
                    deck_title=deck_title,
                    total_cards=total_count,
                    on_exit=lambda: ui.navigate.to("/study"),
                )

                async def handle_rating(rating: int) -> None:
                    idx = state["current_index"]
                    if idx >= total_count:
                        return
                    cur_card = cards_state[idx]
                    card_id = int(cur_card.get("id", 1))

                    asyncio.create_task(record_card_review(session_id, card_id, rating))

                    state["current_index"] += 1
                    next_idx = state["current_index"]

                    if next_idx < total_count:
                        header_refs["counter_label"].text = (
                            f"{next_idx + 1} / {total_count}"
                        )
                        header_refs["remaining_label"].text = (
                            f"Còn lại: {total_count - next_idx - 1} thẻ"
                        )
                        header_refs["progress_bar"].set_value(
                            (next_idx + 1) / total_count
                        )
                        stage.render_card(cards_state[next_idx])
                    else:
                        await complete_study_session(session_id, total_count)
                        stage.hide()
                        header_refs["counter_label"].text = (
                            f"Hoàn thành ({total_count}/{total_count})"
                        )
                        header_refs["remaining_label"].text = (
                            "Đã hoàn thành toàn bộ thẻ!"
                        )
                        header_refs["progress_bar"].set_value(1.0)
                        congrats.set_visibility(True)
                        show_toast("Chúc mừng! Đã hoàn thành phiên ôn tập!", "positive")

                congrats = render_study_congrats(
                    total_cards=total_count,
                    on_restart=lambda: render_study_page(
                        deck_identifier=target_ident, tag=tag
                    ),
                )
                congrats.set_visibility(False)

                stage = create_study_stage(on_rating=handle_rating)
                stage.render_card(cards_state[0])
