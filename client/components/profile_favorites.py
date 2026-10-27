from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from nicegui import ui

from components.layout import TOKENS, show_toast
from services import api


def _format_date(iso_str: Optional[str]) -> str:
    """Format thời gian ISO 8601 sang ngày tháng."""
    if not iso_str:
        return "Gần đây"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return str(iso_str)[:10]


def render_profile_favorites_tab(
    favorites_list: List[Dict[str, Any]],
    decks_map: Dict[Any, Any],
    cards_map: Dict[Any, Any],
    on_reload: Callable[[], Any],
) -> None:
    """Render Tab 2: User Favorites (Favorite Decks and Favorite Flashcards)."""
    fav_decks = [f for f in favorites_list if f.get("deck_id")]
    fav_cards = [f for f in favorites_list if f.get("card_id")]

    # Phần 1: Bộ thẻ yêu thích (Decks)
    with ui.column().classes("w-full gap-3"):
        with ui.row().classes("items-center justify-between w-full"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("folder_special", size="20px").classes("text-amber-500")
                ui.label(f"Bộ thẻ yêu thích ({len(fav_decks)})").classes(
                    "text-lg font-extrabold text-slate-800"
                )

        if not fav_decks:
            with ui.card().classes(
                "w-full p-8 text-center items-center justify-center bg-white border border-slate-200 rounded-3xl gap-2 text-slate-400"
            ):
                ui.icon("star_outline", size="36px")
                ui.label("Bạn chưa đánh dấu bộ thẻ nào vào mục yêu thích").classes("text-sm")
                ui.label(
                    "Bấm vào biểu tượng ⭐ trên các thẻ ở màn hình Thư viện để lưu nhanh"
                ).classes("text-xs text-slate-400")
        else:
            with ui.element("div").classes(
                "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 w-full"
            ):
                for f in fav_decks:
                    fav_id = f.get("id")
                    if fav_id is None:
                        continue
                    did = f.get("deck_id")
                    deck_obj = decks_map.get(did, {})
                    title = deck_obj.get("title", f"Bộ thẻ #{did}")
                    desc = deck_obj.get("description", "Không có mô tả")

                    def make_remove_fav_deck_cb(fid: int, name: str):
                        async def del_fav():
                            await api.delete_favorite(fid)
                            show_toast(f"Đã bỏ '{name}' khỏi mục yêu thích", "info")
                            await on_reload()

                        return del_fav

                    with ui.card().classes(
                        "bg-white border border-slate-200 rounded-2xl p-4 shadow-2xs flex flex-col justify-between gap-3"
                    ):
                        with ui.column().classes("gap-1"):
                            with ui.row().classes("items-center justify-between w-full"):
                                ui.label(title).classes(
                                    "font-black text-slate-900 text-base line-clamp-1"
                                )
                                ui.button(
                                    icon="star",
                                    on_click=make_remove_fav_deck_cb(fav_id, title),
                                ).props("flat dense round").classes(
                                    "text-amber-500 hover:text-rose-500 text-xs"
                                ).tooltip("Hủy yêu thích")
                            ui.label(desc).classes(
                                "text-xs text-slate-500 line-clamp-2"
                            )

                        with ui.row().classes(
                            "items-center justify-between w-full pt-2 border-t border-slate-100"
                        ):
                            ui.button(
                                "Ôn tập ngay",
                                icon="play_arrow",
                                on_click=lambda target_did=did: ui.navigate.to(
                                    f"/study?deck_id={target_did}"
                                ),
                            ).classes(
                                f"bg-{TOKENS['primary']} text-white text-xs font-bold px-3 py-1.5 rounded-xl cursor-pointer"
                            )
                            ui.label(_format_date(f.get("created_at"))).classes(
                                "text-[11px] text-slate-400"
                            )

    # Phần 2: Flashcards yêu thích (Cards)
    with ui.column().classes("w-full gap-3 pt-4 border-t border-slate-200"):
        with ui.row().classes("items-center justify-between w-full"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("style", size="20px").classes("text-indigo-600")
                ui.label(f"Thẻ Flashcard yêu thích ({len(fav_cards)})").classes(
                    "text-lg font-extrabold text-slate-800"
                )

        if not fav_cards:
            with ui.card().classes(
                "w-full p-8 text-center items-center justify-center bg-white border border-slate-200 rounded-3xl gap-2 text-slate-400"
            ):
                ui.icon("bookmark_border", size="36px")
                ui.label("Bạn chưa đánh dấu thẻ flashcard nào vào mục yêu thích").classes("text-sm")
                ui.label(
                    "Bấm vào biểu tượng ⭐ trên góc thẻ trong lúc ôn tập Focus Mode để lưu lại thẻ khó"
                ).classes("text-xs text-slate-400")
        else:
            with ui.element("div").classes("grid grid-cols-1 md:grid-cols-2 gap-4 w-full"):
                for f in fav_cards:
                    fav_id = f.get("id")
                    cid = f.get("card_id")
                    card_obj = cards_map.get(cid, {})
                    q = card_obj.get("question", f"Thẻ #{cid}")
                    a = card_obj.get("answer", "")
                    exp = card_obj.get("explanation", "")
                    card_tags = card_obj.get("tags", [])

                    def make_remove_fav_card_cb(fid: int):
                        async def del_fav():
                            await api.delete_favorite(fid)
                            show_toast("Đã bỏ thẻ khỏi mục yêu thích", "info")
                            await on_reload()

                        return del_fav

                    with ui.card().classes(
                        "bg-white border border-slate-200 rounded-2xl p-4 shadow-2xs flex flex-col justify-between gap-3"
                    ):
                        with ui.column().classes("gap-1.5"):
                            with ui.row().classes("items-center justify-between w-full"):
                                ui.label(f"Thẻ #{cid}").classes(
                                    "text-xs font-bold text-slate-400"
                                )
                                if fav_id is not None:
                                    ui.button(
                                        icon="star",
                                        on_click=make_remove_fav_card_cb(int(fav_id)),
                                    ).props("flat dense round").classes(
                                        "text-amber-500 hover:text-rose-500 text-xs"
                                    ).tooltip("Hủy yêu thích")

                            ui.label(f"Hỏi: {q}").classes(
                                "text-sm font-bold text-slate-900 leading-snug"
                            )
                            ui.label(f"Đáp: {a}").classes(
                                "text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-1 rounded-md"
                            )
                            if exp:
                                ui.label(f"Giải thích: {exp}").classes(
                                    "text-xs text-slate-500 italic"
                                )

                        if card_tags:
                            with ui.row().classes("items-center gap-1 flex-wrap pt-1"):
                                for t in card_tags:
                                    t_str = t if isinstance(t, str) else t.get("name", "")
                                    if t_str:
                                        ui.label(f"#{t_str}").classes(
                                            "text-[10px] bg-slate-100 text-slate-600 rounded px-1.5 py-0.5"
                                        )

