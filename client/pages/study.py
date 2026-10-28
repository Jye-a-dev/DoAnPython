"""
study.py — Spaced Repetition (SM-2) Focus Mode Page.
Orchestrator for modular components in pages.study_components.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Set
from nicegui import ui

from components import (
    app_shell,
    empty_deck_state,
    network_error_banner,
    show_toast,
)
from pages.study_components.category_modal import (
    _CATEGORY_COLOR_MAP,
    _CATEGORY_ICON_MAP,
    _category_icon,
    _run_random_two_level_selection,
    _show_category_selection_modal,
)
from pages.study_components.study_session_view import render_study_session_view
from services import api
from services.auth_guard import get_current_user


async def render_study_page(
    deck_id: Optional[int] = None, tag: Optional[str] = None
) -> None:
    """Trang Ôn tập Lặp lại Ngắt quãng (SM-2) chế độ Focus Mode tối giản tích hợp Favorites & Lọc Tag.

    Khi deck_id is None: hiển thị modal Chọn Môn Học và thực thi thuật toán Random 2 Cấp.
    """
    with app_shell(
        active_tab="study", title="EduFlash AI - Chế Độ Ôn Tập Lặp Lại Ngắt Quãng SM-2"
    ):
        cur_user = get_current_user() or {}
        active_user_id = int(cur_user.get("id") or cur_user.get("user_id") or 1)

        ui.add_head_html("""
        <style>
        .study-focus-container {
            min-height: calc(100vh - 120px);
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            align-items: center;
        }
        .card-transition-wrapper {
            transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
        }
        </style>
        """)

        selected_tag_state = {"value": tag}
        resolved_deck_id: Dict[str, Optional[int]] = {"value": deck_id}
        study_container = ui.column().classes("w-full")

        async def load_study_data() -> None:
            """Tải dữ liệu bài học, thẻ, danh sách yêu thích và áp dụng bộ lọc tag."""
            if getattr(ui.context.client, "is_deleted", False):
                return
            study_container.clear()
            with study_container:
                active_deck: Optional[Dict[str, Any]] = None
                deck_resp: Any = None
                current_deck_id = resolved_deck_id["value"]

                if current_deck_id is not None:
                    deck_resp = await api.get_deck_by_id(current_deck_id)
                    if isinstance(deck_resp, dict) and "id" in deck_resp:
                        active_deck = deck_resp

                cards_resp = await api.get_cards(
                    deck_id=current_deck_id, user_id=active_user_id
                )
                favorites_resp = await api.get_favorites(user_id=active_user_id)

                if getattr(ui.context.client, "is_deleted", False):
                    return

                if api.is_connection_error(cards_resp) or (
                    current_deck_id is not None and api.is_connection_error(deck_resp)
                ):
                    network_error_banner(
                        on_retry=load_study_data,
                        message="Không thể kết nối đến máy chủ Backend (Port 3000). Vui lòng kiểm tra lại tiến trình.",
                    )
                    return

                if isinstance(cards_resp, dict) and cards_resp.get("error"):
                    network_error_banner(
                        on_retry=load_study_data,
                        message=cards_resp.get(
                            "message", "Không thể nạp danh sách thẻ ôn tập."
                        ),
                    )
                    return

                raw_cards: List[Dict[str, Any]] = (
                    [c for c in cards_resp if isinstance(c, dict)]
                    if isinstance(cards_resp, list)
                    else []
                )

                card_fav_map: Dict[int, int] = {}
                if isinstance(favorites_resp, list):
                    for fav in favorites_resp:
                        cid = fav.get("card_id")
                        if cid:
                            card_fav_map[cid] = fav.get("id", 0)

                available_tags: Set[str] = set()
                for c in raw_cards:
                    c_tags = c.get("tags", [])
                    if isinstance(c_tags, list):
                        for t in c_tags:
                            t_name = t if isinstance(t, str) else t.get("name", "")
                            if t_name and t_name.strip():
                                available_tags.add(t_name.strip())

                active_tag_filter = selected_tag_state["value"]
                cards_pool: List[Dict[str, Any]] = raw_cards
                if active_tag_filter and active_tag_filter != "all":
                    cards_pool = []
                    for c in raw_cards:
                        c_tags = c.get("tags", [])
                        matches = False
                        if isinstance(c_tags, list):
                            for t in c_tags:
                                t_name = t if isinstance(t, str) else t.get("name", "")
                                if (
                                    t_name.strip().lower()
                                    == active_tag_filter.strip().lower()
                                ):
                                    matches = True
                                    break
                        if matches:
                            cards_pool.append(c)

                if not cards_pool:
                    deck_name = (
                        active_deck.get("title", "Bộ thẻ")
                        if active_deck
                        else "Hệ thống"
                    )
                    desc_msg = (
                        f"Không tìm thấy thẻ nào có nhãn '#{active_tag_filter}' trong {deck_name}."
                        if active_tag_filter and active_tag_filter != "all"
                        else (
                            f"{deck_name} hiện chưa có thẻ nào đến hạn ôn tập hoặc chưa được tạo nội dung. "
                            "Hãy vào Studio để tự động tạo bộ thẻ mới từ bài giảng."
                        )
                    )
                    empty_deck_state(
                        title="Không có thẻ nào phù hợp để ôn tập!",
                        description=desc_msg,
                        icon="school",
                        action_text="Tạo bài học mới",
                        action_url="/",
                        secondary_text="Xem thư viện Deck",
                        secondary_url="/decks",
                    )
                    return

                session_id: int = 1
                target_deck_id = current_deck_id or cards_pool[0].get("deck_id", 1)
                sess_resp = await api.create_study_session(
                    deck_id=target_deck_id, user_id=active_user_id
                )
                if isinstance(sess_resp, dict):
                    session_id = sess_resp.get("session_id") or sess_resp.get("id", 1)

                async def handle_tag_filter_change(selected_val: str) -> None:
                    selected_tag_state["value"] = selected_val
                    await load_study_data()

                render_study_session_view(
                    study_container=study_container,
                    cards_pool=cards_pool,
                    active_deck=active_deck,
                    available_tags=available_tags,
                    selected_tag=selected_tag_state["value"],
                    card_fav_map=card_fav_map,
                    session_id=session_id,
                    active_user_id=active_user_id,
                    on_tag_change=handle_tag_filter_change,
                )

        try:
            asyncio.get_running_loop()
            if not ui.context.client.has_socket_connection:
                await ui.context.client.connected()
        except RuntimeError:
            pass

        await load_study_data()

    # Nếu không có deck_id: hiển thị modal chọn môn học trước
    async def _boot_study_flow() -> None:
        if deck_id is not None:
            return

        async def on_deck_resolved(
            chosen_deck: Optional[Dict[str, Any]], category_name: str = ""
        ) -> None:
            if chosen_deck is None or not isinstance(chosen_deck, dict):
                study_container.clear()
                with study_container:
                    empty_deck_state(
                        title=f"Môn học '{category_name}' chưa có bộ thẻ nào",
                        description=(
                            "Hãy vào Studio để tạo bộ thẻ mới từ bài giảng hoặc chọn môn học khác."
                        ),
                        icon="school",
                        action_text="Tạo bài học mới",
                        action_url="/",
                        secondary_text="Chọn lại môn học",
                        secondary_url="/study",
                    )
                return

            resolved_deck_id["value"] = chosen_deck["id"]
            show_toast(
                f"Đã chọn ngẫu nhiên: {chosen_deck.get('title', 'Bộ thẻ')} 🎲",
                "positive",
            )
            await load_study_data()

        await _show_category_selection_modal(
            study_container=study_container,
            active_user_id=active_user_id,
            on_deck_resolved=on_deck_resolved,
        )

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_boot_study_flow())
    except RuntimeError:
        pass


__all__ = [
    "render_study_page",
    "_category_icon",
    "_run_random_two_level_selection",
    "_show_category_selection_modal",
]
