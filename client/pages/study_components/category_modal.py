"""
category_modal.py — Category Selection Modal and 2-Level Random Selection Algorithm.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional
from nicegui import ui

from components import show_toast
from services import api
from services.api_decks import get_decks as _get_decks_svc
from services.api_decks import get_folders as _get_folders_svc

# Icon mapping cho từng loại môn học phổ biến
_CATEGORY_ICON_MAP: Dict[str, str] = {
    "toán": "calculate",
    "math": "calculate",
    "anh": "language",
    "english": "language",
    "tiếng anh": "language",
    "lịch sử": "history_edu",
    "history": "history_edu",
    "tin học": "computer",
    "it": "computer",
    "computer": "computer",
    "vật lý": "science",
    "physics": "science",
    "hóa học": "biotech",
    "chemistry": "biotech",
    "sinh học": "eco",
    "biology": "eco",
    "địa lý": "public",
    "geography": "public",
    "văn": "menu_book",
    "literature": "menu_book",
    "default": "school",
}

_CATEGORY_COLOR_MAP: List[str] = [
    "bg-indigo-50 border-indigo-200 text-indigo-700",
    "bg-emerald-50 border-emerald-200 text-emerald-700",
    "bg-amber-50 border-amber-200 text-amber-700",
    "bg-rose-50 border-rose-200 text-rose-700",
    "bg-sky-50 border-sky-200 text-sky-700",
    "bg-violet-50 border-violet-200 text-violet-700",
    "bg-orange-50 border-orange-200 text-orange-700",
    "bg-teal-50 border-teal-200 text-teal-700",
]


def _category_icon(name: str) -> str:
    """Trả về icon phù hợp dựa trên tên môn học."""
    name_lower = (name or "").strip().lower()
    for key, icon in _CATEGORY_ICON_MAP.items():
        if key in name_lower:
            return icon
    return _CATEGORY_ICON_MAP["default"]


async def _run_random_two_level_selection(
    category_id: int,
    study_container: ui.column,
    active_user_id: int,
    on_deck_chosen: Any,
) -> None:
    """
    Thuật toán Random 2 Cấp:
    Cấp 1: random 1 Folder thuộc category_id.
    Cấp 2: random 1 Deck bên trong folder đó.
    Fallback: nếu không có folder hoặc folder không có deck, random trực tiếp từ category_id.
    """
    if category_id is None:
        await on_deck_chosen(None)
        return

    folders_resp = await _get_folders_svc(category_id)
    folders: List[Dict[str, Any]] = (
        [f for f in folders_resp if isinstance(f, dict)]
        if isinstance(folders_resp, list)
        else []
    )

    chosen_deck: Optional[Dict[str, Any]] = None

    if folders:
        random.shuffle(folders)
        for chosen_folder in folders:
            decks_resp = await _get_decks_svc(chosen_folder["id"])
            folder_decks: List[Dict[str, Any]] = (
                [d for d in decks_resp if isinstance(d, dict)]
                if isinstance(decks_resp, list)
                else []
            )
            if folder_decks:
                chosen_deck = random.choice(folder_decks)
                break

    if chosen_deck is None:
        direct_decks_resp = await _get_decks_svc()
        direct_decks: List[Dict[str, Any]] = (
            [
                d
                for d in direct_decks_resp
                if isinstance(d, dict) and d.get("category_id") == category_id
            ]
            if isinstance(direct_decks_resp, list)
            else []
        )
        if direct_decks:
            chosen_deck = random.choice(direct_decks)

    await on_deck_chosen(chosen_deck)


async def _show_category_selection_modal(
    study_container: ui.column,
    active_user_id: int,
    on_deck_resolved: Any,
) -> None:
    """Hiển thị Dialog chọn Môn học (Category) với UI grid màu sắc."""
    categories_resp = await api.get_categories()
    categories: List[Dict[str, Any]] = (
        [c for c in categories_resp if isinstance(c, dict)]
        if isinstance(categories_resp, list)
        else []
    )

    with ui.dialog() as category_dialog, ui.card().classes(
        "w-full max-w-2xl rounded-2xl p-0 overflow-hidden shadow-2xl"
    ):
        with ui.row().classes(
            "w-full items-center gap-3 px-6 py-4 bg-gradient-to-r from-indigo-600 to-indigo-700"
        ):
            ui.icon("school", size="28px").classes("text-white")
            with ui.column().classes("gap-0"):
                ui.label("Chọn Môn Học").classes("text-lg font-bold text-white")
                ui.label("Hệ thống sẽ tự động chọn ngẫu nhiên bộ thẻ phù hợp").classes(
                    "text-xs text-indigo-200"
                )
            ui.space()
            ui.button(icon="close", on_click=category_dialog.close).props(
                "flat round dense"
            ).classes("text-white hover:bg-indigo-500")

        with ui.column().classes("w-full p-6 gap-4"):
            if not categories:
                with ui.column().classes("w-full items-center gap-3 py-8"):
                    ui.icon("category", size="48px").classes("text-slate-300")
                    ui.label("Chưa có môn học nào").classes(
                        "text-slate-500 font-semibold"
                    )
                    ui.label("Hãy tạo môn học và thêm bộ thẻ trước").classes(
                        "text-xs text-slate-400"
                    )
            else:
                ui.label("Nhấp vào một môn học để bắt đầu ôn tập:").classes(
                    "text-sm font-semibold text-slate-600"
                )

                with ui.element("div").classes(
                    "grid grid-cols-2 sm:grid-cols-3 gap-3 w-full"
                ):
                    for i, cat in enumerate(categories):
                        cat_name = cat.get("name", f"Môn #{cat.get('id', i + 1)}")
                        cat_id = cat.get("id")
                        color_cls = _CATEGORY_COLOR_MAP[i % len(_CATEGORY_COLOR_MAP)]
                        icon_name = _category_icon(cat_name)

                        def make_category_click(cid=cat_id, cname=cat_name):
                            async def on_category_click():
                                if cid is None:
                                    show_toast("Môn học không có ID hợp lệ", "warning")
                                    return
                                category_dialog.close()
                                study_container.clear()
                                with study_container:
                                    with ui.column().classes(
                                        "w-full items-center justify-center py-20 gap-4"
                                    ):
                                        ui.spinner(size="48px").classes(
                                            "text-indigo-600"
                                        )
                                        ui.label(
                                            f"Đang tìm bộ thẻ ngẫu nhiên cho môn {cname}..."
                                        ).classes("text-slate-500 text-sm")

                                async def on_deck_chosen(
                                    deck: Optional[Dict[str, Any]],
                                ):
                                    await on_deck_resolved(deck, cname)

                                await _run_random_two_level_selection(
                                    category_id=int(cid),
                                    study_container=study_container,
                                    active_user_id=active_user_id,
                                    on_deck_chosen=on_deck_chosen,
                                )

                            return on_category_click

                        with ui.element("div").classes(
                            f"flex flex-col items-center gap-2 p-4 rounded-xl border-2 cursor-pointer "
                            f"hover:shadow-md transition-all duration-200 {color_cls}"
                        ).on("click", make_category_click()):
                            ui.icon(icon_name, size="32px")
                            ui.label(cat_name).classes(
                                "text-sm font-bold text-center leading-tight"
                            )

    category_dialog.open()
