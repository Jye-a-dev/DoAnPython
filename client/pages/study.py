from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from nicegui import ui

from components import (
    TOKENS,
    app_shell,
    empty_deck_state,
    network_error_banner,
    render_flashcard,
    render_srs_action_bar,
    show_toast,
)
from services import api
from services.auth_guard import get_current_user


async def render_study_page(deck_id: Optional[int] = None) -> None:
    """Trang Ôn tập Lặp lại Ngắt quãng (SM-2) chế độ Focus Mode tối giản."""
    with app_shell(
        active_tab="study", title="EduFlash AI - Chế Độ Ôn Tập Lặp Lại Ngắt Quãng SM-2"
    ):
        # Thiết lập Focus Mode: ẩn thanh cuộn phụ ngoài màn hình
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

        study_container = ui.column().classes("w-full")

        async def load_study_data() -> None:
            """Tải dữ liệu bài học và thẻ, hiển thị Error Banner hoặc Empty State chuẩn."""
            study_container.clear()
            with study_container:
                # -----------------------------------------------------------
                # 1. TẢI DỮ LIỆU DECK VÀ CARDS TỪ BACKEND API
                # -----------------------------------------------------------
                active_deck: Optional[Dict[str, Any]] = None
                deck_resp: Any = None
                if deck_id is not None:
                    deck_resp = await api.get_deck_by_id(deck_id)
                    if isinstance(deck_resp, dict) and "id" in deck_resp:
                        active_deck = deck_resp

                cards_resp = await api.get_cards(deck_id=deck_id)

                # Kiểm tra lỗi mất kết nối máy chủ backend
                if api.is_connection_error(cards_resp) or (
                    deck_id is not None and api.is_connection_error(deck_resp)
                ):
                    network_error_banner(
                        on_retry=load_study_data,
                        message="Không thể kết nối đến máy chủ Backend (Port 3000). Vui lòng kiểm tra lại tiến trình.",
                    )
                    return

                # Kiểm tra phản hồi lỗi nghiệp vụ
                if isinstance(cards_resp, dict) and cards_resp.get("error"):
                    network_error_banner(
                        on_retry=load_study_data,
                        message=cards_resp.get(
                            "message", "Không thể nạp danh sách thẻ ôn tập."
                        ),
                    )
                    return

                cards_pool: List[Dict[str, Any]] = []
                if isinstance(cards_resp, list):
                    cards_pool = [c for c in cards_resp if isinstance(c, dict)]

                # -----------------------------------------------------------
                # 2. XỬ LÝ TRẠNG THÁI RỖNG (EMPTY STATE)
                # -----------------------------------------------------------
                if not cards_pool:
                    deck_name = (
                        active_deck.get("title", "Bộ thẻ")
                        if active_deck
                        else "Hệ thống"
                    )
                    empty_deck_state(
                        title="Bạn chưa có bài học hoặc thẻ ghi nhớ nào!",
                        description=(
                            f"{deck_name} hiện chưa có thẻ nào đến hạn ôn tập hoặc chưa được tạo nội dung. "
                            "Hãy vào Studio để tự động tạo bộ thẻ mới từ bài giảng."
                        ),
                        icon="school",
                        action_text="Tạo bài học mới",
                        action_url="/",
                        secondary_text="Xem thư viện Deck",
                        secondary_url="/decks",
                    )
                    return

                # -----------------------------------------------------------
                # 3. TẠO PHIÊN HỌC (STUDY SESSION) & SETUP FOCUS MODE
                # -----------------------------------------------------------
                session_id: int = 1
                target_deck_id = deck_id or cards_pool[0].get("deck_id", 1)
                cur_user = get_current_user()
                active_user_id = (
                    (cur_user.get("id") or cur_user.get("user_id") or 1)
                    if cur_user
                    else 1
                )
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
                    "study-focus-container w-full max-w-2xl mx-auto gap-6"
                ):
                    # Header Tiến trình & Streak
                    with ui.column().classes("w-full gap-2 pt-2"):
                        with ui.row().classes("items-center justify-between w-full"):
                            with ui.row().classes("items-center gap-2"):
                                ui.icon("school", size="22px").classes(
                                    f"text-{TOKENS['primary']}"
                                )
                                deck_title = (
                                    active_deck.get("title")
                                    if active_deck
                                    else f"Phiên Ôn Tập ({total_cards} thẻ)"
                                )
                                ui.label(deck_title).classes(
                                    "font-extrabold text-base text-slate-900 tracking-tight truncate max-w-[280px]"
                                )

                            with ui.row().classes("items-center gap-2"):
                                with ui.row().classes(
                                    "items-center gap-1 px-3 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-700 font-black text-xs shadow-2xs"
                                ):
                                    ui.label("🔥")
                                    ui.label("Streak: 3 ngày")

                                ui.button(
                                    icon="close",
                                    on_click=lambda: ui.navigate.to("/decks"),
                                ).props("flat dense round").classes(
                                    "text-slate-400 hover:text-slate-700"
                                )

                        progress_bar = (
                            ui.linear_progress(
                                value=1.0 / total_cards,
                                show_value=False,
                            )
                            .props("rounded")
                            .classes(
                                f"w-full h-2 text-{TOKENS['primary']} bg-slate-100"
                            )
                        )

                        with ui.row().classes(
                            "items-center justify-between w-full text-xs font-semibold text-slate-500"
                        ):
                            counter_label = ui.label(f"Thẻ 1 / {total_cards}")
                            remaining_label = ui.label(
                                f"Còn lại: {total_cards - 1} thẻ"
                            )

                    # FLASHCARD CONTAINER
                    card_slot = ui.column().classes(
                        "card-transition-wrapper w-full items-center justify-center min-h-[340px] opacity-100 translate-x-0"
                    )

                    # CONGRATS CONTAINER
                    congrats_container = ui.column().classes(
                        "w-full items-center text-center py-12 gap-5 bg-white border border-slate-200 rounded-3xl p-8 shadow-xl"
                    )
                    congrats_container.set_visibility(False)

                    with congrats_container:
                        with ui.element("div").classes(
                            "w-20 h-20 rounded-3xl bg-emerald-50 text-emerald-600 flex items-center justify-center shadow-sm border border-emerald-200"
                        ):
                            ui.icon("emoji_events", size="44px")

                        ui.label("Tuyệt Vời! Đã Hoàn Thành Phiên Ôn Tập").classes(
                            "text-2xl font-black text-slate-900 tracking-tight"
                        )

                        ui.label(
                            f"Bạn đã hoàn thành việc ôn luyện toàn bộ {total_cards} thẻ theo chu kỳ thuật toán SM-2. "
                            "Khoảng cách ôn tập tiếp theo đã được hệ thống tính toán và tự động cập nhật."
                        ).classes("text-sm text-slate-600 max-w-md leading-relaxed")

                        with ui.row().classes(
                            "items-center justify-center gap-6 py-4 w-full border-y border-slate-100 my-2"
                        ):
                            with ui.column().classes("items-center gap-0.5"):
                                ui.label(str(total_cards)).classes(
                                    "text-2xl font-black text-indigo-600"
                                )
                                ui.label("Thẻ đã ôn").classes(
                                    "text-xs font-semibold text-slate-500"
                                )

                            with ui.column().classes("items-center gap-0.5"):
                                ui.label("100%").classes(
                                    "text-2xl font-black text-emerald-600"
                                )
                                ui.label("Hoàn thành").classes(
                                    "text-xs font-semibold text-slate-500"
                                )

                            with ui.column().classes("items-center gap-0.5"):
                                ui.label("🔥 +1").classes(
                                    "text-2xl font-black text-amber-500"
                                )
                                ui.label("Chuỗi Streak").classes(
                                    "text-xs font-semibold text-slate-500"
                                )

                        with ui.row().classes("gap-4 mt-2"):
                            ui.button(
                                "Xem Thư Viện Deck",
                                icon="folder_special",
                                on_click=lambda: ui.navigate.to("/decks"),
                            ).classes(
                                f"bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold px-6 py-2.5 rounded-xl shadow-md"
                            )

                            async def restart_session():
                                state["current_index"] = 0
                                state["reviewed_count"] = 0
                                congrats_container.set_visibility(False)
                                action_bar_ref["set_active"](True)
                                action_bar_ref["container"].set_visibility(True)
                                card_slot.set_visibility(True)
                                await update_current_card_ui()

                            ui.button(
                                "Ôn Tập Lại Bộ Này",
                                icon="replay",
                                on_click=restart_session,
                            ).props('text-color="black"').classes(
                                "bg-white hover:bg-slate-100 !text-black text-black font-bold px-6 py-2.5 rounded-xl border border-slate-200"
                            )

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

                        counter_label.text = f"Thẻ {idx + 1} / {total_cards}"
                        remaining_label.text = f"Còn lại: {total_cards - idx - 1} thẻ"
                        progress_bar.set_value((idx + 1) / total_cards)

                        current_card_data = cards_pool[idx]
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
                        card_id = current_card.get("id", 1)

                        asyncio.create_task(
                            api.submit_srs_review(
                                session_id=session_id, card_id=card_id, rating=rating
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

        # Tải dữ liệu ban đầu
        await load_study_data()
