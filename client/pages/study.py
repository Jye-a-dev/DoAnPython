from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Set
from nicegui import ui

from components import (
    app_shell,
    empty_deck_state,
    network_error_banner,
    render_flashcard,
    render_srs_action_bar,
    show_toast,
)
from components.study_congrats import render_study_congrats
from components.study_header import render_study_header
from services import api
from services.auth_guard import get_current_user


async def render_study_page(
    deck_id: Optional[int] = None, tag: Optional[str] = None
) -> None:
    """Trang Ôn tập Lặp lại Ngắt quãng (SM-2) chế độ Focus Mode tối giản tích hợp Favorites & Lọc Tag."""
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
        study_container = ui.column().classes("w-full")

        async def load_study_data() -> None:
            """Tải dữ liệu bài học, thẻ, danh sách yêu thích và áp dụng bộ lọc tag."""
            if getattr(ui.context.client, "is_deleted", False):
                return
            study_container.clear()
            with study_container:
                active_deck: Optional[Dict[str, Any]] = None
                deck_resp: Any = None
                if deck_id is not None:
                    deck_resp = await api.get_deck_by_id(deck_id)
                    if isinstance(deck_resp, dict) and "id" in deck_resp:
                        active_deck = deck_resp

                cards_resp = await api.get_cards(
                    deck_id=deck_id, user_id=active_user_id
                )
                favorites_resp = await api.get_favorites(user_id=active_user_id)

                if getattr(ui.context.client, "is_deleted", False):
                    return

                if api.is_connection_error(cards_resp) or (
                    deck_id is not None and api.is_connection_error(deck_resp)
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
                target_deck_id = deck_id or cards_pool[0].get("deck_id", 1)
                sess_resp = await api.create_study_session(
                    deck_id=target_deck_id, user_id=active_user_id
                )
                if isinstance(sess_resp, dict):
                    session_id = sess_resp.get("session_id") or sess_resp.get("id", 1)

                total_cards = len(cards_pool)
                state = {
                    "current_index": 0,
                    "reviewed_count": 0,
                    "card_controller": None,
                    "is_animating": False,
                }

                with ui.column().classes(
                    "study-focus-container w-full max-w-2xl mx-auto gap-5"
                ):
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
                                show_toast(
                                    res.get("message", "Lỗi hủy yêu thích"), "negative"
                                )
                            else:
                                card_fav_map.pop(cid, None)
                                header_refs["bookmark_star_btn"].props(
                                    "icon=star_border"
                                )
                                header_refs["bookmark_star_btn"].classes(
                                    add="text-slate-400 hover:text-amber-500",
                                    remove="text-amber-500",
                                )
                                header_refs["bookmark_star_btn"].tooltip(
                                    "Thêm vào yêu thích"
                                )
                                show_toast("Đã bỏ thẻ khỏi danh sách yêu thích", "info")
                        else:
                            res = await api.add_favorite(
                                user_id=active_user_id, card_id=cid
                            )
                            if isinstance(res, dict) and res.get("error"):
                                show_toast(
                                    res.get("message", "Lỗi thêm yêu thích"), "negative"
                                )
                            else:
                                new_fid = (
                                    res.get("id", 1) if isinstance(res, dict) else 1
                                )
                                card_fav_map[cid] = new_fid
                                header_refs["bookmark_star_btn"].props("icon=star")
                                header_refs["bookmark_star_btn"].classes(
                                    add="text-amber-500",
                                    remove="text-slate-400 hover:text-amber-500",
                                )
                                header_refs["bookmark_star_btn"].tooltip(
                                    "Bỏ yêu thích thẻ này"
                                )
                                show_toast(
                                    "Đã lưu thẻ vào mục yêu thích! ⭐", "positive"
                                )

                    async def handle_tag_filter_change(selected_val: str) -> None:
                        selected_tag_state["value"] = selected_val
                        await load_study_data()

                    header_refs = render_study_header(
                        deck_title=deck_title or "",
                        total_cards=total_cards,
                        available_tags=available_tags,
                        selected_tag=selected_tag_state["value"],
                        on_tag_change=handle_tag_filter_change,
                        on_toggle_favorite=handle_toggle_card_favorite,
                    )

                    card_slot = ui.column().classes(
                        "card-transition-wrapper w-full items-center justify-center min-h-[340px] opacity-100 translate-x-0"
                    )

                    async def restart_session():
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
                            show_toast(
                                "Chúc mừng! Đã hoàn thành phiên ôn tập!", "positive"
                            )
                            return

                        header_refs["counter_label"].text = (
                            f"Thẻ {idx + 1} / {total_cards}"
                        )
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
                            header_refs["bookmark_star_btn"].tooltip(
                                "Bỏ yêu thích thẻ này"
                            )
                        else:
                            header_refs["bookmark_star_btn"].props("icon=star_border")
                            header_refs["bookmark_star_btn"].classes(
                                add="text-slate-400 hover:text-amber-500",
                                remove="text-amber-500",
                            )
                            header_refs["bookmark_star_btn"].tooltip(
                                "Lưu thẻ vào mục yêu thích"
                            )

                        with card_slot:
                            state["card_controller"] = render_flashcard(
                                card_data=current_card_data,
                                is_flipped_default=False,
                            )

                    async def handle_rating_submission(rating: int) -> None:
                        if (
                            state["is_animating"]
                            or state["current_index"] >= total_cards
                        ):
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

                    await update_current_card_ui()

        try:
            asyncio.get_running_loop()
            if not ui.context.client.has_socket_connection:
                await ui.context.client.connected()
        except RuntimeError:
            pass

        await load_study_data()
