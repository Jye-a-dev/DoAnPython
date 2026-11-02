"""
deck_detail_dialog.py — Modal Quản lý Chi tiết Bộ Thẻ, Breadcrumbs, Category/Folder Picker & CRUD Thẻ.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, List, Optional
from nicegui import ui

from components.layout import show_toast
from services import api


def build_folder_options(folders: List[Dict[str, Any]]) -> Dict[Optional[int], str]:
    """Tạo dict options với đường dẫn phân cấp: 📁 Parent / Child."""
    folder_map: Dict[int, Dict[str, Any]] = {
        int(f["id"]): f for f in folders if "id" in f and f["id"] is not None
    }

    def get_full_path(fid: int, visited: Optional[set[int]] = None) -> str:
        if visited is None:
            visited = set()
        if fid in visited or fid not in folder_map:
            return ""
        visited.add(fid)
        f = folder_map[fid]
        parent_id = f.get("parent_id")
        if parent_id and int(parent_id) in folder_map:
            parent_path = get_full_path(int(parent_id), visited)
            fname = f.get("name", "")
            return f"{parent_path} / {fname}" if parent_path else fname
        return str(f.get("name", ""))

    options: Dict[Optional[int], str] = {None: "📁 Thư mục gốc (Root)"}
    sorted_folders = sorted(folders, key=lambda f: str(f.get("name", "")).lower())
    for f in sorted_folders:
        fid = f.get("id")
        if fid is not None:
            options[int(fid)] = f"📁 {get_full_path(int(fid))}"
    return options


def build_category_options(categories: List[Dict[str, Any]]) -> Dict[Optional[int], str]:
    """Tạo dict options danh mục môn học với badge trực quan."""
    options: Dict[Optional[int], str] = {None: "⚪ Không phân loại"}
    for cat in categories:
        cid = cat.get("id")
        if cid is not None:
            cname = cat.get("name", "")
            options[int(cid)] = f"🏷️ {cname}"
    return options


async def open_deck_detail_dialog(
    deck_id: int, on_refresh: Optional[Callable[[], Any]] = None
) -> None:
    """Modal Chi tiết Bộ thẻ: Hiển thị breadcrumbs Folder, Badge Category và CRUD Cards."""
    from components.deck_card_editor import confirm_delete_deck_dialog
    from pages.decks.components.card_dialog import open_card_dialog
    from pages.decks.components.card_item import render_card_item

    # 1. Nạp đồng thời dữ liệu deck, categories, folders và cards
    deck_info = await api.get_deck_by_id(deck_id)
    if isinstance(deck_info, dict) and deck_info.get("error"):
        show_toast(deck_info.get("message", f"Không tìm thấy bộ thẻ #{deck_id}"), "warning")
        if on_refresh:
            res = on_refresh()
            if asyncio.iscoroutine(res):
                await res
        return

    deck_obj: Dict[str, Any] = (
        deck_info if isinstance(deck_info, dict) else {"id": deck_id, "title": f"Bộ thẻ #{deck_id}"}
    )

    categories_resp = await api.get_categories()
    folders_resp = await api.get_folders()
    categories_list: List[Dict[str, Any]] = categories_resp if isinstance(categories_resp, list) else []
    folders_list: List[Dict[str, Any]] = folders_resp if isinstance(folders_resp, list) else []

    cat_map: Dict[int, Dict[str, Any]] = {int(c["id"]): c for c in categories_list if "id" in c}
    folder_map: Dict[int, Dict[str, Any]] = {int(f["id"]): f for f in folders_list if "id" in f}

    category_options = build_category_options(categories_list)
    folder_options = build_folder_options(folders_list)

    cards_resp = await api.get_cards(deck_id=deck_id)
    cards_state: List[Dict[str, Any]] = list(cards_resp if isinstance(cards_resp, list) else [])

    state: Dict[str, Any] = {
        "title": deck_obj.get("title", f"Bộ thẻ #{deck_id}"),
        "category_id": deck_obj.get("category_id"),
        "folder_id": deck_obj.get("folder_id"),
        "description": deck_obj.get("description", ""),
        "search_query": "",
    }

    try:
        target_client = ui.context.client
    except (RuntimeError, AttributeError):
        target_client = None

    if target_client:
        with target_client:
            dialog = ui.dialog().props("maximized=false persistent=false")
            dialog.on("hide", dialog.delete)
    else:
        dialog = ui.dialog().props("maximized=false persistent=false")
        dialog.on("hide", dialog.delete)

    with dialog, ui.card().classes(
        "w-full max-w-4xl p-6 md:p-8 rounded-3xl bg-white shadow-2xl border border-slate-100 "
        "gap-5 max-h-[90vh] flex flex-col overflow-hidden"
    ):
        header_row = ui.row().classes("items-start justify-between w-full pb-4 border-b border-slate-100 flex-wrap gap-3")
        action_bar = ui.row().classes("items-center justify-between w-full gap-3 flex-wrap")
        cards_scroll = ui.column().classes("w-full max-h-96 overflow-y-auto space-y-3 pr-1")

        async def trigger_refresh() -> None:
            if on_refresh:
                res = on_refresh()
                if asyncio.iscoroutine(res):
                    await res

        async def reload_cards() -> None:
            c_res = await api.get_cards(deck_id=deck_id)
            if isinstance(c_res, list):
                cards_state[:] = c_res
                render_header()
                render_cards()
                await trigger_refresh()

        def open_edit_deck_dialog() -> None:
            """Mở Dialog chỉnh sửa thông tin Bộ thẻ (Tên, Danh mục, Thư mục)."""
            edit_dlg = ui.dialog().props("maximized=false")
            with edit_dlg, ui.card().classes(
                "w-full max-w-md p-6 rounded-3xl bg-white shadow-2xl border border-slate-100 gap-4"
            ):
                with ui.row().classes("items-center justify-between w-full pb-2 border-b border-slate-100"):
                    ui.label("Chỉnh sửa thông tin Bộ thẻ").classes("text-base font-black text-slate-900")
                    ui.button(icon="close", on_click=edit_dlg.close).props("flat dense round")

                title_input = (
                    ui.input(label="Tên bộ thẻ", value=state["title"])
                    .props("outlined dense")
                    .classes("w-full bg-white")
                )

                cur_cat_val = int(state["category_id"]) if state.get("category_id") is not None else None
                cat_select = (
                    ui.select(
                        label="Danh mục môn học",
                        options=category_options,
                        value=cur_cat_val if cur_cat_val in category_options else None,
                    )
                    .props("outlined dense")
                    .classes("w-full bg-white")
                )

                cur_folder_val = int(state["folder_id"]) if state.get("folder_id") is not None else None
                folder_select = (
                    ui.select(
                        label="Thư mục lưu trữ",
                        options=folder_options,
                        value=cur_folder_val if cur_folder_val in folder_options else None,
                    )
                    .props("outlined dense")
                    .classes("w-full bg-white")
                )

                with ui.row().classes("w-full justify-end gap-2 pt-2"):
                    ui.button("Hủy", on_click=edit_dlg.close).props("flat dense").classes(
                        "text-slate-500 font-bold text-xs"
                    )

                    async def handle_save_changes() -> None:
                        new_title = (title_input.value or "").strip()
                        if not new_title:
                            show_toast("Tên bộ thẻ không được để trống", "warning")
                            return

                        res = await api.update_deck(
                            deck_id=deck_id,
                            title=new_title,
                            category_id=cat_select.value,
                            folder_id=folder_select.value,
                        )
                        if isinstance(res, dict) and res.get("error"):
                            show_toast(res.get("message", "Lỗi cập nhật bộ thẻ"), "negative")
                            return

                        state["title"] = new_title
                        state["category_id"] = cat_select.value
                        state["folder_id"] = folder_select.value
                        deck_obj.update({
                            "title": new_title,
                            "category_id": cat_select.value,
                            "folder_id": folder_select.value,
                        })

                        show_toast("Đã cập nhật thông tin bộ thẻ thành công!", "positive")
                        edit_dlg.close()
                        render_header()
                        await trigger_refresh()

                    ui.button("Lưu thay đổi", icon="save", on_click=handle_save_changes).classes(
                        "bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-4 py-2 rounded-xl text-xs"
                    )
            edit_dlg.open()

        def render_header() -> None:
            """Render khung header với Badge Môn học, Đường dẫn Thư mục và nút Đổi tên/Chỉnh sửa."""
            header_row.clear()
            with header_row:
                with ui.row().classes("items-start gap-3 flex-1 min-w-[280px]"):
                    with ui.element("div").classes(
                        "w-10 h-10 rounded-2xl bg-amber-50 text-amber-500 flex items-center justify-center shrink-0 border border-amber-100 shadow-2xs mt-1"
                    ):
                        ui.icon("style", size="22px")

                    with ui.column().classes("gap-1 min-w-0 flex-1"):
                        with ui.row().classes("items-center gap-2 flex-wrap"):
                            ui.label(state["title"]).classes(
                                "text-xl font-black text-slate-900 tracking-tight truncate max-w-sm md:max-w-md"
                            )
                            ui.button(
                                "✏️ Đổi tên / Chỉnh sửa",
                                on_click=open_edit_deck_dialog,
                            ).props("flat dense").classes(
                                "text-xs font-bold text-indigo-600 hover:bg-indigo-50 rounded-lg px-2 py-0.5 cursor-pointer"
                            )

                        # Thanh Breadcrumb / Tag trực quan dưới tiêu đề
                        with ui.row().classes("items-center gap-2 flex-wrap text-xs"):
                            cid = int(state["category_id"]) if state.get("category_id") is not None else None
                            if cid and cid in cat_map:
                                cat_data = cat_map[cid]
                                c_color = cat_data.get("color_code") or "#3B82F6"
                                ui.badge(
                                    cat_data.get("name", "Môn học"),
                                    color=c_color,
                                ).props("rounded").classes(
                                    "text-xs font-bold px-2.5 py-0.5 shadow-2xs text-white"
                                ).style(f"background-color: {c_color};")

                            fid = int(state["folder_id"]) if state.get("folder_id") is not None else None
                            if fid and fid in folder_options:
                                f_label = folder_options[fid]
                                ui.label(f_label).classes("text-xs text-slate-500 font-medium")
                            else:
                                ui.label("📁 Thư mục gốc (Root)").classes("text-xs text-slate-400 italic")

                            ui.button(
                                icon="edit",
                                on_click=open_edit_deck_dialog,
                            ).props("flat dense round").classes(
                                "text-slate-400 hover:text-indigo-600 text-xs cursor-pointer -ml-1"
                            ).tooltip("Đổi Thư mục / Môn học")

                        with ui.row().classes("items-center gap-2 pt-1"):
                            ui.label(f"{len(cards_state)} thẻ").classes(
                                "text-xs font-bold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200"
                            )
                            ui.label(f"{len(cards_state)} cần ôn").classes(
                                "text-xs font-bold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-600 border border-amber-200"
                            )

                with ui.row().classes("items-center gap-2 shrink-0"):
                    async def handle_delete_deck():
                        async def on_deck_deleted():
                            dialog.close()
                            await trigger_refresh()

                        await confirm_delete_deck_dialog(deck_id, state["title"], on_deleted=on_deck_deleted)

                    ui.button("🗑️ Xóa Bộ Thẻ", on_click=handle_delete_deck).props("flat dense").classes(
                        "text-xs font-bold text-rose-500 hover:text-rose-700 hover:bg-rose-50 rounded-lg px-2 py-1 cursor-pointer"
                    )
                    ui.button(icon="close", on_click=dialog.close).props("flat dense round").classes(
                        "text-slate-400 hover:text-slate-700 cursor-pointer"
                    )

        with action_bar:
            with ui.row().classes("items-center gap-2 flex-1 min-w-[280px]"):
                def open_add_modal():
                    open_card_dialog(deck_id=deck_id, card=None, on_saved=reload_cards)

                ui.button("+ Thêm Thẻ Mới", icon="add", on_click=open_add_modal).classes(
                    "bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-4 py-2 rounded-xl text-xs cursor-pointer shadow-xs transition"
                )

                def open_io_modal():
                    from pages.decks.components.deck_io_dialog import open_deck_io_dialog
                    open_deck_io_dialog(deck_id=deck_id, deck_title=state["title"], on_imported=reload_cards)

                ui.button("Xuất / Nhập", icon="swap_horiz", on_click=open_io_modal).props("outline").classes(
                    "text-indigo-600 border-indigo-200 bg-indigo-50/50 hover:bg-indigo-50 font-bold px-3 py-2 rounded-xl text-xs cursor-pointer shadow-xs transition"
                )

                def on_search(e):
                    state["search_query"] = (e.value or "").strip().lower()
                    render_cards()

                ui.input(
                    placeholder="Tìm kiếm nhanh câu hỏi...",
                    on_change=on_search,
                ).props("outlined dense clearable").classes("flex-1 max-w-xs text-xs bg-slate-50 rounded-xl")

            ui.button(
                "Ôn tập ngay (Focus Mode)",
                icon="bolt",
                on_click=lambda did=deck_id: ui.navigate.to(f"/study?deck_id={did}"),
            ).classes(
                "bg-amber-500 hover:bg-amber-600 text-white font-bold px-4 py-2 rounded-xl text-xs cursor-pointer shadow-md shadow-amber-500/20 transition"
            )

        def render_cards() -> None:
            cards_scroll.clear()
            q_filter = state["search_query"]
            displayed_cards = [
                c for c in cards_state
                if not q_filter or q_filter in (c.get("question") or "").lower()
            ]

            with cards_scroll:
                if not displayed_cards:
                    with ui.column().classes("w-full py-10 items-center text-center gap-2 text-slate-400"):
                        ui.icon("inbox", size="36px")
                        ui.label(
                            "Không tìm thấy thẻ nào phù hợp."
                            if q_filter
                            else "Bộ thẻ này hiện chưa có flashcard nào. Hãy bấm '+ Thêm Thẻ Mới' để bắt đầu."
                        ).classes("text-xs")
                    return

                for idx, card in enumerate(displayed_cards):
                    async def handle_delete_card(cid: int):
                        del_c_res = await api.delete_card(cid)
                        if isinstance(del_c_res, dict) and del_c_res.get("error"):
                            show_toast(del_c_res.get("message", "Lỗi xóa thẻ"), "negative")
                        else:
                            show_toast("Đã xóa thẻ thành công", "info")
                            cards_state[:] = [c for c in cards_state if c.get("id") != cid]
                            render_header()
                            render_cards()
                            await trigger_refresh()

                    def handle_edit_card(c: Dict[str, Any]):
                        open_card_dialog(deck_id=deck_id, card=c, on_saved=reload_cards)

                    render_card_item(
                        idx=idx,
                        card=card,
                        on_edit=handle_edit_card,
                        on_delete=handle_delete_card,
                    )

        render_header()
        render_cards()
        dialog.open()


# Re-export alias for backward compatibility
open_deck_manager_dialog = open_deck_detail_dialog

__all__ = [
    "open_deck_detail_dialog",
    "open_deck_manager_dialog",
    "build_folder_options",
    "build_category_options",
]
