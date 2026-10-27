from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from nicegui import ui

from components.deck_card import render_deck_card
from components.feedback_states import empty_deck_state
from components.layout import TOKENS, show_toast
from services import api


def render_decks_grid_section(
    decks_list: List[Dict[str, Any]],
    cards_by_deck: Dict[int, List[Dict[str, Any]]],
    categories_map: Dict[Any, Any],
    folders_map: Dict[Any, Any],
    deck_fav_map: Dict[Any, int],
    filter_state: Dict[str, Any],
    active_user_id: int,
    on_filter_tab: Callable[[str], Any],
    on_clear_sidebar_filter: Callable[[], Any],
    on_open_detail: Callable[[int], Any],
    on_reload: Callable[[], Any],
) -> None:
    """Render thanh bộ lọc tab ngang và lưới danh sách các bộ thẻ (Decks Grid)."""
    with ui.column().classes("flex-1 w-full gap-5"):
        # 1. Thanh Filter Tabs ngang
        with ui.row().classes(
            "items-center justify-between w-full bg-white border border-slate-200 rounded-2xl p-2 shadow-2xs flex-wrap gap-2"
        ):
            with ui.row().classes("items-center gap-1"):
                ui.button(
                    "Tất cả",
                    icon="grid_view",
                    on_click=lambda: on_filter_tab("all"),
                ).props("flat dense").classes(
                    f"rounded-xl px-3 py-1.5 text-xs font-bold transition-all "
                    + (
                        f"bg-{TOKENS['primary']} text-white shadow-xs"
                        if filter_state["tab"] == "all"
                        else "text-slate-600 hover:bg-slate-100"
                    )
                )

                ui.button(
                    f"Yêu thích (⭐ {len(deck_fav_map)})",
                    icon="star",
                    on_click=lambda: on_filter_tab("favorites"),
                ).props("flat dense").classes(
                    f"rounded-xl px-3 py-1.5 text-xs font-bold transition-all "
                    + (
                        "bg-amber-500 text-white shadow-xs"
                        if filter_state["tab"] == "favorites"
                        else "text-amber-700 hover:bg-amber-50"
                    )
                )

                ui.button(
                    "Theo Thư mục",
                    icon="folder",
                    on_click=lambda: on_filter_tab("folder"),
                ).props("flat dense").classes(
                    f"rounded-xl px-3 py-1.5 text-xs font-bold transition-all "
                    + (
                        "bg-indigo-600 text-white shadow-xs"
                        if filter_state["tab"] == "folder"
                        else "text-indigo-700 hover:bg-indigo-50"
                    )
                )

            with ui.row().classes("items-center gap-2"):
                active_cat_id = filter_state.get("category_id")
                if active_cat_id is not None:
                    cat_obj = categories_map.get(active_cat_id) or {}
                    with ui.row().classes(
                        "items-center gap-1 px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-bold border border-blue-200"
                    ):
                        ui.label(f"Môn: {cat_obj.get('name', '')}")
                        ui.button(
                            icon="close",
                            on_click=on_clear_sidebar_filter,
                        ).props("flat dense round").classes(
                            "text-blue-500 hover:text-blue-800 text-[10px]"
                        )

                active_fold_id = filter_state.get("folder_id")
                if active_fold_id is not None:
                    fold_obj = folders_map.get(active_fold_id) or {}
                    with ui.row().classes(
                        "items-center gap-1 px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 text-xs font-bold border border-indigo-200"
                    ):
                        ui.label(f"Thư mục: {fold_obj.get('name', '')}")
                        ui.button(
                            icon="close",
                            on_click=on_clear_sidebar_filter,
                        ).props("flat dense round").classes(
                            "text-indigo-500 hover:text-indigo-800 text-[10px]"
                        )

        # 2. Lọc dữ liệu theo tab & bộ chọn sidebar
        filtered_decks = decks_list
        if filter_state["tab"] == "favorites":
            filtered_decks = [d for d in filtered_decks if d.get("id") in deck_fav_map]
        elif filter_state["tab"] == "folder":
            filtered_decks = [
                d for d in filtered_decks if d.get("folder_id") is not None
            ]

        if filter_state["category_id"] is not None:
            filtered_decks = [
                d
                for d in filtered_decks
                if d.get("category_id") == filter_state["category_id"]
            ]

        if filter_state["folder_id"] is not None:
            filtered_decks = [
                d
                for d in filtered_decks
                if d.get("folder_id") == filter_state["folder_id"]
            ]

        # 3. Lưới hiển thị danh sách bộ thẻ
        if not filtered_decks:
            empty_deck_state(
                title="Không tìm thấy bộ thẻ nào phù hợp!",
                description=(
                    "Thư mục hoặc danh mục này hiện chưa có bộ thẻ nào. "
                    "Hãy tạo bộ thẻ mới hoặc chuyển sang tab 'Tất cả' để xem toàn bộ kho thẻ."
                ),
                icon="folder_off",
                action_text="Tạo Deck mới ngay",
                action_url="javascript:void(0)",
            )
        else:
            with ui.element("div").classes(
                "grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5 w-full"
            ):
                for deck in filtered_decks:
                    deck_id = deck.get("id", 1)
                    deck_cards = cards_by_deck.get(deck_id, [])
                    deck_cat_id = deck.get("category_id")
                    deck_cat = (
                        categories_map.get(deck_cat_id)
                        if deck_cat_id is not None
                        else None
                    )
                    deck_folder_id = deck.get("folder_id")
                    deck_folder = (
                        folders_map.get(deck_folder_id)
                        if deck_folder_id is not None
                        else None
                    )
                    is_favorite = deck_id in deck_fav_map
                    fav_id = deck_fav_map.get(deck_id)

                    def make_fav_toggle_cb(
                        did: int, is_fav: bool, f_id: Optional[int], dname: str
                    ):
                        async def toggle_favorite():
                            if is_fav and f_id:
                                res = await api.delete_favorite(f_id)
                                if isinstance(res, dict) and res.get("error"):
                                    show_toast(
                                        res.get("message", "Lỗi hủy yêu thích"),
                                        "negative",
                                    )
                                else:
                                    show_toast(
                                        f"Đã bỏ '{dname}' khỏi mục yêu thích",
                                        "info",
                                    )
                                    await on_reload()
                            else:
                                res = await api.add_favorite(
                                    user_id=active_user_id, deck_id=did
                                )
                                if isinstance(res, dict) and res.get("error"):
                                    show_toast(
                                        res.get("message", "Lỗi thêm yêu thích"),
                                        "negative",
                                    )
                                else:
                                    show_toast(
                                        f"Đã thêm '{dname}' vào mục yêu thích! ⭐",
                                        "positive",
                                    )
                                    await on_reload()

                        return toggle_favorite

                    def make_delete_deck_cb(d_id: int, d_title: str):
                        async def del_deck_action():
                            del_resp = await api.delete_deck(d_id)
                            if isinstance(del_resp, dict) and del_resp.get("error"):
                                show_toast(
                                    del_resp.get("message", "Lỗi xóa bộ thẻ"),
                                    "negative",
                                )
                            else:
                                show_toast(f"Đã xóa bộ thẻ '{d_title}'", "info")
                                await on_reload()

                        return del_deck_action

                    render_deck_card(
                        deck=deck,
                        deck_cards=deck_cards,
                        deck_cat=deck_cat,
                        deck_folder=deck_folder,
                        is_favorite=is_favorite,
                        fav_id=fav_id,
                        on_toggle_favorite=make_fav_toggle_cb(
                            deck_id,
                            is_favorite,
                            fav_id,
                            deck.get("title", ""),
                        ),
                        on_open_detail=lambda did=deck_id: on_open_detail(did),
                        on_delete_deck=make_delete_deck_cb(
                            deck_id, deck.get("title", "")
                        ),
                    )
