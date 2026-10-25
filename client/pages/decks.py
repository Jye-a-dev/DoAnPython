from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional
from nicegui import ui

from components import (
    TOKENS,
    app_shell,
    empty_deck_state,
    network_error_banner,
    render_footer,
    show_toast,
)
from services import api
from services.auth_guard import get_current_user


def _format_date(iso_str: Optional[str]) -> str:
    """Format thời gian ISO 8601 sang định dạng ngày tháng tiếng Việt."""
    if not iso_str:
        return "Gần đây"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return "Gần đây"


async def render_decks_page() -> None:
    """Trang Thư viện & Quản lý Deck (Flashcard Collections)."""
    with app_shell(active_tab="decks", title="EduFlash AI - Thư Viện Bộ Thẻ"):
        # -------------------------------------------------------------------
        # 1. DIALOGS QUẢN LÝ (MODALS)
        # -------------------------------------------------------------------
        # DIALOG: TẠO DECK MỚI
        with ui.dialog() as create_deck_dialog, ui.card().classes(
            "w-full max-w-md p-6 rounded-3xl bg-white shadow-2xl border border-slate-100 gap-4"
        ):
            with ui.row().classes(
                "items-center justify-between w-full pb-2 border-b border-slate-100"
            ):
                with ui.row().classes("items-center gap-2"):
                    with ui.element("div").classes(
                        f"w-8 h-8 rounded-lg bg-{TOKENS['primary_light']} flex items-center justify-center text-{TOKENS['primary']}"
                    ):
                        ui.icon("create_new_folder", size="20px")
                    ui.label("Tạo Bộ Thẻ Mới").classes(
                        "text-lg font-bold text-slate-900"
                    )
                ui.button(icon="close", on_click=create_deck_dialog.close).props(
                    "flat dense round"
                ).classes("text-slate-400 hover:text-slate-700")

            deck_title_input = (
                ui.input(
                    label="Tên bộ thẻ",
                    placeholder="Ví dụ: Lịch sử Đảng, Từ vựng IELTS...",
                )
                .props("outlined dense")
                .classes("w-full")
            )
            deck_desc_input = (
                ui.textarea(
                    label="Mô tả bộ thẻ (tùy chọn)",
                    placeholder="Ghi chú khái quát về nội dung...",
                )
                .props("outlined dense rows=3")
                .classes("w-full")
            )

            async def handle_create_deck() -> None:
                title_val = (
                    deck_title_input.value.strip() if deck_title_input.value else ""
                )
                if not title_val:
                    show_toast("Vui lòng nhập tiêu đề bộ thẻ", "warning")
                    return

                desc_val = (
                    deck_desc_input.value.strip() if deck_desc_input.value else ""
                )
                cur_user = get_current_user()
                active_user_id = (
                    (cur_user.get("id") or cur_user.get("user_id") or 1)
                    if cur_user
                    else 1
                )
                res = await api.create_deck(
                    title=title_val, description=desc_val, user_id=active_user_id
                )

                if isinstance(res, dict) and "id" in res:
                    show_toast(f"Tạo thành công bộ thẻ '{title_val}'!", "positive")
                    create_deck_dialog.close()
                    deck_title_input.value = ""
                    deck_desc_input.value = ""
                    await load_decks_data()
                elif isinstance(res, dict) and res.get("error"):
                    show_toast(res.get("message", "Lỗi tạo Deck"), "negative")

            ui.button(
                "TẠO BỘ THẺ NGAY", icon="check", on_click=handle_create_deck
            ).classes(
                f"w-full py-3 bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold rounded-xl shadow-md transition duration-200"
            )

        # DIALOG: XEM VÀ QUẢN LÝ CHI TIẾT THẺ BÊN TRONG DECK
        detail_state: Dict[str, Any] = {"deck": None, "cards": []}

        with ui.dialog() as detail_dialog, ui.card().classes(
            "w-full max-w-3xl p-6 rounded-3xl bg-white shadow-2xl border border-slate-100 gap-4 max-h-[85vh] flex flex-col"
        ):
            with ui.row().classes(
                "items-center justify-between w-full pb-3 border-b border-slate-100"
            ):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("style", size="22px").classes(f"text-{TOKENS['primary']}")
                    detail_title_label = ui.label("Chi tiết bộ thẻ").classes(
                        "text-lg font-bold text-slate-900"
                    )
                ui.button(icon="close", on_click=detail_dialog.close).props(
                    "flat dense round"
                ).classes("text-slate-400 hover:text-slate-700")

            detail_cards_scroll = ui.column().classes(
                "w-full overflow-y-auto gap-3 pr-1 max-h-[50vh]"
            )

            with ui.card().classes(
                "w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 gap-2"
            ):
                ui.label("Thêm nhanh flashcard vào bộ thẻ:").classes(
                    f"text-xs font-bold text-{TOKENS['text_secondary']} uppercase tracking-wider"
                )
                with ui.row().classes("w-full gap-2 items-center"):
                    new_q_input = (
                        ui.input(placeholder="Câu hỏi...")
                        .props("outlined dense")
                        .classes("flex-1 bg-white")
                    )
                    new_a_input = (
                        ui.input(placeholder="Đáp án...")
                        .props("outlined dense")
                        .classes("flex-1 bg-white")
                    )

                    async def handle_quick_add_card():
                        q = new_q_input.value.strip() if new_q_input.value else ""
                        a = new_a_input.value.strip() if new_a_input.value else ""
                        if not q or not a:
                            show_toast("Vui lòng điền đủ câu hỏi và đáp án", "warning")
                            return
                        target_d = detail_state["deck"]
                        if not target_d:
                            return
                        res = await api.create_card(
                            question=q, answer=a, deck_id=target_d["id"]
                        )
                        if isinstance(res, dict) and "id" in res:
                            show_toast("Đã thêm flashcard mới!", "positive")
                            new_q_input.value = ""
                            new_a_input.value = ""
                            await open_deck_detail_modal(target_d)
                            await load_decks_data()
                        else:
                            show_toast("Lỗi khi thêm thẻ", "negative")

                    ui.button("+ Thêm", on_click=handle_quick_add_card).classes(
                        f"bg-{TOKENS['primary']} text-white font-bold px-4 py-2 rounded-xl"
                    )

        async def open_deck_detail_modal(deck_data: Dict[str, Any]) -> None:
            """Mở modal danh sách chi tiết các thẻ của một Deck."""
            detail_state["deck"] = deck_data
            detail_title_label.text = f"Bộ Thẻ: {deck_data.get('title', 'Deck')}"
            detail_dialog.open()

            detail_cards_scroll.clear()
            deck_cards_resp = await api.get_cards(deck_id=deck_data["id"])
            deck_cards = deck_cards_resp if isinstance(deck_cards_resp, list) else []
            detail_state["cards"] = deck_cards

            with detail_cards_scroll:
                if not deck_cards:
                    with ui.column().classes(
                        "w-full py-8 items-center text-center gap-2 text-slate-400"
                    ):
                        ui.icon("inbox", size="36px")
                        ui.label("Chưa có thẻ nào trong bộ này").classes("text-sm")
                    return

                for idx, c in enumerate(deck_cards):
                    with ui.card().classes(
                        "w-full bg-white border border-slate-200 rounded-xl p-3.5 shadow-2xs gap-2"
                    ):
                        with ui.row().classes("items-center justify-between w-full"):
                            ui.label(f"#{idx + 1}").classes(
                                "text-xs font-bold text-slate-400"
                            )

                            def make_del_card_cb(target_card_id: int):
                                async def del_card():
                                    await api.delete_card(target_card_id)
                                    show_toast("Đã xóa thẻ", "info")
                                    await open_deck_detail_modal(deck_data)
                                    await load_decks_data()

                                return del_card

                            ui.button(
                                icon="delete",
                                on_click=make_del_card_cb(c.get("id", 0)),
                            ).props("flat dense round").classes(
                                "text-slate-400 hover:text-rose-600 text-xs"
                            )

                        ui.label(f"Hỏi: {c.get('question', '')}").classes(
                            "text-sm font-bold text-slate-800"
                        )
                        ui.label(f"Đáp: {c.get('answer', '')}").classes(
                            "text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-1 rounded-md"
                        )
                        if c.get("explanation"):
                            ui.label(f"Giải thích: {c['explanation']}").classes(
                                "text-xs text-slate-500 italic"
                            )

        # -------------------------------------------------------------------
        # 2. KHUNG NỘI DUNG CHÍNH (DYNAMIC REFRESHABLE CONTAINER)
        # -------------------------------------------------------------------
        page_container = ui.column().classes("w-full gap-0")

        async def load_decks_data() -> None:
            """Tải dữ liệu decks/cards và hiển thị Network Error Banner hoặc Empty State."""
            page_container.clear()
            with page_container:
                decks_resp = await api.get_decks()
                all_cards_resp = await api.get_cards()

                # Kiểm tra lỗi mất kết nối máy chủ backend
                if api.is_connection_error(decks_resp) or api.is_connection_error(
                    all_cards_resp
                ):
                    network_error_banner(
                        on_retry=load_decks_data,
                        message="Không thể kết nối đến máy chủ Backend (Port 3000). Vui lòng kiểm tra lại tiến trình.",
                    )
                    return

                # Kiểm tra phản hồi lỗi nghiệp vụ khác nếu có
                if isinstance(decks_resp, dict) and decks_resp.get("error"):
                    network_error_banner(
                        on_retry=load_decks_data,
                        message=decks_resp.get(
                            "message",
                            "Không thể tải danh sách bộ thẻ từ máy chủ Backend.",
                        ),
                    )
                    return

                decks_list: List[Dict[str, Any]] = (
                    decks_resp if isinstance(decks_resp, list) else []
                )
                all_cards: List[Dict[str, Any]] = (
                    all_cards_resp if isinstance(all_cards_resp, list) else []
                )

                # Thống kê tổng quan
                total_decks = len(decks_list)
                total_cards = len(all_cards)

                cards_by_deck: Dict[int, List[Dict[str, Any]]] = {}
                for c in all_cards:
                    d_id = c.get("deck_id", 0)
                    cards_by_deck.setdefault(d_id, []).append(c)

                due_cards_count = sum(len(cards) for cards in cards_by_deck.values())

                # Header thống kê tổng quan & Nút tạo Deck
                with ui.row().classes(
                    "items-center justify-between w-full pb-6 border-b border-slate-200 flex-wrap gap-4"
                ):
                    with ui.column().classes("gap-1"):
                        ui.label("Thư Viện Bộ Thẻ Học Tập").classes(
                            f"text-3xl font-black text-{TOKENS['text_primary']} tracking-tight"
                        )
                        ui.label(
                            "Quản lý toàn bộ các chủ đề flashcard được phân loại tự động bởi EduFlash AI."
                        ).classes(f"text-sm text-{TOKENS['text_secondary']}")

                    ui.button(
                        "+ Tạo Deck Mới",
                        icon="add",
                        on_click=create_deck_dialog.open,
                    ).classes(
                        f"bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold px-6 py-3 rounded-2xl "
                        "shadow-lg hover:shadow-indigo-500/25 transition duration-200 cursor-pointer"
                    )

                # Cụm Stat Cards
                with ui.element("div").classes(
                    "grid grid-cols-1 md:grid-cols-3 gap-5 w-full my-6"
                ):
                    # Stat 1: Tổng số Deck
                    with ui.card().classes(
                        "bg-white border border-slate-200 rounded-2xl p-5 shadow-xs flex flex-row items-center justify-between"
                    ):
                        with ui.column().classes("gap-0.5"):
                            ui.label("Tổng số Bộ thẻ").classes(
                                f"text-xs font-bold text-{TOKENS['text_secondary']} uppercase tracking-wider"
                            )
                            ui.label(str(total_decks)).classes(
                                f"text-3xl font-black text-{TOKENS['text_primary']}"
                            )
                        with ui.element("div").classes(
                            f"w-12 h-12 rounded-xl bg-{TOKENS['primary_light']} text-{TOKENS['primary']} flex items-center justify-center"
                        ):
                            ui.icon("folder_special", size="26px")

                    # Stat 2: Tổng số Flashcards
                    with ui.card().classes(
                        "bg-white border border-slate-200 rounded-2xl p-5 shadow-xs flex flex-row items-center justify-between"
                    ):
                        with ui.column().classes("gap-0.5"):
                            ui.label("Tổng số Flashcards").classes(
                                f"text-xs font-bold text-{TOKENS['text_secondary']} uppercase tracking-wider"
                            )
                            ui.label(str(total_cards)).classes(
                                "text-3xl font-black text-indigo-600"
                            )
                        with ui.element("div").classes(
                            "w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center"
                        ):
                            ui.icon("style", size="26px")

                    # Stat 3: Thẻ cần ôn hôm nay
                    with ui.card().classes(
                        "bg-gradient-to-br from-amber-50 to-orange-50/50 border border-amber-200 rounded-2xl p-5 shadow-xs flex flex-row items-center justify-between"
                    ):
                        with ui.column().classes("gap-0.5"):
                            ui.label("Cần Ôn Tập Hôm Nay").classes(
                                "text-xs font-bold text-amber-700 uppercase tracking-wider"
                            )
                            ui.label(f"{due_cards_count} thẻ").classes(
                                "text-3xl font-black text-amber-500"
                            )
                        with ui.element("div").classes(
                            "w-12 h-12 rounded-xl bg-amber-500 text-white flex items-center justify-center shadow-md shadow-amber-500/30"
                        ):
                            ui.icon("alarm", size="26px")

                # -----------------------------------------------------------
                # DANH SÁCH BỘ THẺ DẠNG LƯỚI HOẶC EMPTY STATE
                # -----------------------------------------------------------
                if not decks_list:
                    empty_deck_state(
                        title="Bạn chưa có bài học hoặc thẻ ghi nhớ nào!",
                        description=(
                            "Hãy nạp tài liệu bài học hoặc dán nội dung vào Studio "
                            "để AI tự động trích xuất bộ Flashcard đầu tiên."
                        ),
                        icon="auto_stories",
                        action_text="Tạo bài học mới",
                        action_url="/",
                    )
                else:
                    with ui.element("div").classes(
                        "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 w-full mt-2"
                    ):
                        for deck in decks_list:
                            deck_id = deck.get("id", 1)
                            deck_cards = cards_by_deck.get(deck_id, [])
                            card_count = len(deck_cards)
                            created_date_str = _format_date(deck.get("created_at"))
                            folder_label = (
                                deck.get("category", {}).get("name")
                                if isinstance(deck.get("category"), dict)
                                else "Mặc định"
                            )

                            with ui.card().classes(
                                "bg-white border border-slate-200 rounded-3xl p-6 shadow-sm hover:shadow-xl hover:border-indigo-200 transition-all duration-200 flex flex-col justify-between gap-5 relative group"
                            ):
                                with ui.column().classes("w-full gap-3"):
                                    with ui.row().classes(
                                        "items-center justify-between w-full"
                                    ):
                                        with ui.row().classes(
                                            "items-center gap-1.5 px-3 py-1 rounded-full bg-slate-100 border border-slate-200 text-xs font-semibold text-slate-600"
                                        ):
                                            ui.icon("folder", size="14px").classes(
                                                "text-slate-400"
                                            )
                                            ui.label(folder_label)

                                        ui.label(created_date_str).classes(
                                            "text-xs text-slate-400 font-medium"
                                        )

                                    with ui.column().classes("gap-1"):
                                        ui.label(
                                            deck.get("title", f"Bộ thẻ #{deck_id}")
                                        ).classes(
                                            "text-xl font-black text-slate-900 tracking-tight leading-snug line-clamp-1"
                                        )
                                        desc_text = (
                                            deck.get("description")
                                            or "Bộ thẻ được sinh tự động từ tài liệu học tập."
                                        )
                                        ui.label(desc_text).classes(
                                            "text-xs text-slate-500 line-clamp-2 leading-relaxed"
                                        )

                                    with ui.row().classes(
                                        "items-center justify-between w-full pt-1"
                                    ):
                                        with ui.row().classes(
                                            "items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-50 border border-amber-200/80 text-amber-700 text-xs font-bold"
                                        ):
                                            ui.icon("alarm", size="14px").classes(
                                                "text-amber-500"
                                            )
                                            ui.label(f"{card_count} thẻ cần ôn hôm nay")

                                        ui.label(f"Tổng: {card_count} thẻ").classes(
                                            "text-xs font-bold text-slate-400"
                                        )

                                    with ui.column().classes("w-full gap-1 pt-1"):
                                        mastery_ratio = min(
                                            1.0, 0.45 if card_count > 0 else 0.0
                                        )
                                        ui.linear_progress(value=mastery_ratio).props(
                                            "rounded"
                                        ).classes(
                                            f"w-full h-1.5 text-{TOKENS['primary']} bg-slate-100"
                                        )
                                        with ui.row().classes(
                                            "items-center justify-between w-full text-[11px] font-semibold text-slate-400"
                                        ):
                                            ui.label("Độ thuần thục")
                                            ui.label(f"{int(mastery_ratio * 100)}%")

                                with ui.row().classes(
                                    "items-center justify-between w-full pt-3 border-t border-slate-100 gap-2"
                                ):
                                    ui.button(
                                        "Học ngay",
                                        icon="play_arrow",
                                        on_click=lambda d_id=deck_id: ui.navigate.to(
                                            f"/study?deck_id={d_id}"
                                        ),
                                    ).classes(
                                        f"flex-1 bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold py-2 px-3 rounded-xl shadow-xs transition duration-200 text-xs cursor-pointer"
                                    )

                                    ui.button(
                                        icon="visibility",
                                        on_click=lambda d=deck: open_deck_detail_modal(
                                            d
                                        ),
                                    ).props("flat dense round").classes(
                                        "text-slate-500 hover:text-slate-800"
                                    ).tooltip(
                                        "Xem chi tiết các thẻ"
                                    )

                                    def make_delete_deck_cb(d_id: int, d_title: str):
                                        async def del_deck_action():
                                            del_resp = await api.delete_deck(d_id)
                                            if isinstance(
                                                del_resp, dict
                                            ) and del_resp.get("error"):
                                                show_toast(
                                                    del_resp.get(
                                                        "message", "Lỗi xóa bộ thẻ"
                                                    ),
                                                    "negative",
                                                )
                                            else:
                                                show_toast(
                                                    f"Đã xóa bộ thẻ '{d_title}'", "info"
                                                )
                                                await load_decks_data()

                                        return del_deck_action

                                    ui.button(
                                        icon="delete_outline",
                                        on_click=make_delete_deck_cb(
                                            deck_id, deck.get("title", "")
                                        ),
                                    ).props("flat dense round").classes(
                                        "text-slate-400 hover:text-rose-600"
                                    ).tooltip(
                                        "Xóa bộ thẻ"
                                    )

                render_footer()

        # Tải dữ liệu ban đầu
        await load_decks_data()
