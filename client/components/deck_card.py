from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from nicegui import ui

from components.layout import TOKENS


def _format_date(iso_str: Optional[str]) -> str:
    """Format thời gian ISO 8601 sang định dạng ngày tháng tiếng Việt."""
    if not iso_str:
        return "Gần đây"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return "Gần đây"


def render_deck_card(
    deck: Dict[str, Any],
    deck_cards: List[Dict[str, Any]],
    deck_cat: Optional[Dict[str, Any]],
    deck_folder: Optional[Dict[str, Any]],
    is_favorite: bool,
    fav_id: Optional[int],
    on_toggle_favorite: Callable[[], Any],
    on_open_detail: Callable[[], Any],
    on_delete_deck: Callable[[], Any],
) -> None:
    """Render a single Deck card in the grid with status badges, progress and actions."""
    deck_id = deck.get("id", 1)
    deck_title = deck.get("title", f"Bộ thẻ #{deck_id}")
    card_count = len(deck_cards)
    created_date_str = _format_date(deck.get("created_at"))

    with ui.card().classes(
        "bg-white border border-slate-200 rounded-3xl p-5 shadow-sm hover:shadow-xl hover:border-indigo-200 transition-all duration-200 flex flex-col justify-between gap-4 relative group"
    ):
        with ui.column().classes("w-full gap-3"):
            # Hàng trên cùng: Badges & Bookmark Star (⭐ user_favorites)
            with ui.row().classes("items-center justify-between w-full"):
                with ui.row().classes("items-center gap-1.5 flex-wrap"):
                    if deck_cat:
                        cat_color = deck_cat.get("color_code", "#3B82F6")
                        with ui.row().classes(
                            "items-center gap-1 px-2.5 py-0.5 rounded-full bg-slate-50 border border-slate-200 text-xs font-semibold text-slate-700"
                        ):
                            ui.element("span").classes(
                                "w-2 h-2 rounded-full inline-block"
                            ).style(f"background-color: {cat_color}")
                            ui.label(deck_cat.get("name", "Danh mục")).classes(
                                "truncate max-w-[90px]"
                            )

                    if deck_folder:
                        with ui.row().classes(
                            "items-center gap-1 px-2.5 py-0.5 rounded-full bg-indigo-50/70 border border-indigo-200/60 text-xs font-semibold text-indigo-700"
                        ):
                            ui.icon("folder", size="12px").classes("text-indigo-500")
                            ui.label(deck_folder.get("name", "Thư mục")).classes(
                                "truncate max-w-[90px]"
                            )

                    if not deck_cat and not deck_folder:
                        with ui.row().classes(
                            "items-center gap-1 px-2 py-0.5 rounded-full bg-slate-100 text-xs font-medium text-slate-500"
                        ):
                            ui.label("Mặc định")

                ui.button(
                    icon="star" if is_favorite else "star_border",
                    on_click=on_toggle_favorite,
                ).props("flat dense round").classes(
                    "text-amber-500 hover:scale-125 transition-transform"
                    if is_favorite
                    else "text-slate-300 hover:text-amber-500 transition-colors"
                ).tooltip(
                    "Hủy yêu thích" if is_favorite else "Đánh dấu yêu thích"
                )

            # Tiêu đề & mô tả
            with ui.column().classes("gap-1"):
                ui.label(deck_title).classes(
                    "text-lg font-black text-slate-900 tracking-tight leading-snug line-clamp-1"
                )
                desc_text = (
                    deck.get("description")
                    or "Bộ thẻ được quản lý thông minh bởi EduFlash AI."
                )
                ui.label(desc_text).classes(
                    "text-xs text-slate-500 line-clamp-2 leading-relaxed"
                )

            # Thống kê thẻ cần ôn
            with ui.row().classes("items-center justify-between w-full pt-1"):
                with ui.row().classes(
                    "items-center gap-1.5 px-2.5 py-1 rounded-lg bg-amber-50 border border-amber-200/80 text-amber-700 text-xs font-bold"
                ):
                    ui.icon("alarm", size="14px").classes("text-amber-500")
                    ui.label(f"{card_count} thẻ cần ôn")

                ui.label(created_date_str).classes("text-xs text-slate-400 font-medium")

            # Thanh tiến độ độ thuần thục
            with ui.column().classes("w-full gap-1 pt-1"):
                mastery_ratio = min(1.0, 0.45 if card_count > 0 else 0.0)
                ui.linear_progress(value=mastery_ratio).props("rounded").classes(
                    f"w-full h-1.5 text-{TOKENS['primary']} bg-slate-100"
                )
                with ui.row().classes(
                    "items-center justify-between w-full text-[11px] font-semibold text-slate-400"
                ):
                    ui.label("Độ thuần thục")
                    ui.label(f"{int(mastery_ratio * 100)}%")

        # Nút hành động đáy thẻ
        with ui.row().classes(
            "items-center justify-between w-full pt-3 border-t border-slate-100 gap-2"
        ):
            ui.button(
                "Học ngay",
                icon="play_arrow",
                on_click=lambda d_id=deck_id: ui.navigate.to(f"/study?deck_id={d_id}"),
            ).classes(
                f"flex-1 bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold py-2 px-3 rounded-xl shadow-xs transition duration-200 text-xs cursor-pointer"
            )

            ui.button(
                icon="visibility",
                on_click=on_open_detail,
            ).props("flat dense round").classes(
                "text-slate-500 hover:text-slate-800"
            ).tooltip("Xem chi tiết các thẻ & nhãn")

            ui.button(
                icon="delete_outline",
                on_click=on_delete_deck,
            ).props("flat dense round").classes(
                "text-slate-400 hover:text-rose-600"
            ).tooltip("Xóa bộ thẻ")

