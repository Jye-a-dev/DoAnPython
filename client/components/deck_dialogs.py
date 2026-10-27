from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from nicegui import ui

from components.deck_detail_dialog import render_deck_detail_dialog
from components.deck_manager_dialog import open_deck_manager_dialog
from components.layout import TOKENS, show_toast
from services import api


def render_create_category_dialog(
    active_user_id: int,
    on_created: Callable[[], Any],
) -> Dict[str, Any]:
    """Create category dialog with color presets palette and backend integration."""
    with ui.dialog() as dialog, ui.card().classes(
        "w-full max-w-md p-6 rounded-3xl bg-white shadow-2xl border border-slate-100 gap-4"
    ):
        with ui.row().classes(
            "items-center justify-between w-full pb-2 border-b border-slate-100"
        ):
            with ui.row().classes("items-center gap-2"):
                with ui.element("div").classes(
                    f"w-8 h-8 rounded-lg bg-{TOKENS['primary_light']} flex items-center justify-center text-{TOKENS['primary']}"
                ):
                    ui.icon("category", size="20px")
                ui.label("Tạo Danh Mục Môn Học").classes(
                    "text-lg font-bold text-slate-900"
                )
            ui.button(icon="close", on_click=dialog.close).props(
                "flat dense round"
            ).classes("text-slate-400 hover:text-slate-700")

        cat_name_input = (
            ui.input(
                label="Tên danh mục môn học",
                placeholder="Ví dụ: Toán Cao Cấp, Y Khoa, Tiếng Anh...",
            )
            .props("outlined dense")
            .classes("w-full")
        )

        cat_desc_input = (
            ui.textarea(
                label="Mô tả danh mục (tùy chọn)",
                placeholder="Ghi chú tổng quan...",
            )
            .props("outlined dense rows=2")
            .classes("w-full")
        )

        cat_color_input = (
            ui.input(label="Mã màu nhận diện (HEX)", value="#3B82F6")
            .props("outlined dense")
            .classes("w-full")
        )

        with ui.row().classes("items-center gap-2 w-full pt-1"):
            ui.label("Màu gợi ý:").classes("text-xs text-slate-400 font-medium")
            for c_hex in [
                "#3B82F6",
                "#10B981",
                "#F59E0B",
                "#EF4444",
                "#8B5CF6",
                "#EC4899",
                "#06B6D4",
            ]:
                with ui.element("button").classes(
                    "w-6 h-6 rounded-full border border-slate-300 shadow-2xs cursor-pointer hover:scale-110 transition-transform"
                ).style(f"background-color: {c_hex}"):
                    pass

                def make_color_setter(h=c_hex):
                    return lambda: setattr(cat_color_input, "value", h)

                ui.element("span").on("click", make_color_setter(c_hex))

        async def handle_create_category() -> None:
            name_val = cat_name_input.value.strip() if cat_name_input.value else ""
            if not name_val:
                show_toast("Vui lòng nhập tên danh mục môn học", "warning")
                return
            desc_val = cat_desc_input.value.strip() if cat_desc_input.value else ""
            color_val = (
                cat_color_input.value.strip()
                if cat_color_input.value
                else "#3B82F6"
            )

            res = await api.create_category(
                name=name_val,
                description=desc_val,
                color_code=color_val,
                user_id=active_user_id,
            )
            if isinstance(res, dict) and "id" in res:
                show_toast(f"Đã tạo danh mục '{name_val}'!", "positive")
                dialog.close()
                cat_name_input.value = ""
                cat_desc_input.value = ""
                await on_created()
            elif isinstance(res, dict) and res.get("error"):
                show_toast(res.get("message", "Lỗi tạo danh mục"), "negative")

        ui.button(
            "TẠO DANH MỤC", icon="check", on_click=handle_create_category
        ).classes(
            f"w-full py-3 bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold rounded-xl shadow-md transition duration-200 cursor-pointer"
        )

    return {"dialog": dialog, "open": dialog.open}


def render_create_folder_dialog(
    active_user_id: int,
    on_created: Callable[[], Any],
) -> Dict[str, Any]:
    """Create hierarchical folder dialog with parent folder and category bindings."""
    with ui.dialog() as dialog, ui.card().classes(
        "w-full max-w-md p-6 rounded-3xl bg-white shadow-2xl border border-slate-100 gap-4"
    ):
        with ui.row().classes(
            "items-center justify-between w-full pb-2 border-b border-slate-100"
        ):
            with ui.row().classes("items-center gap-2"):
                with ui.element("div").classes(
                    f"w-8 h-8 rounded-lg bg-{TOKENS['primary_light']} flex items-center justify-center text-{TOKENS['primary']}"
                ):
                    ui.icon("folder_open", size="20px")
                ui.label("Tạo Thư Mục Mới").classes(
                    "text-lg font-bold text-slate-900"
                )
            ui.button(icon="close", on_click=dialog.close).props(
                "flat dense round"
            ).classes("text-slate-400 hover:text-slate-700")

        folder_name_input = (
            ui.input(
                label="Tên thư mục",
                placeholder="Ví dụ: Học kỳ 1, Chương 2 - Đại số...",
            )
            .props("outlined dense")
            .classes("w-full")
        )

        folder_parent_select = (
            ui.select(
                options={None: "-- Thư mục gốc (Không có cha) --"},
                value=None,
                label="Thư mục cha (Cấu trúc phân cấp)",
            )
            .props("outlined dense")
            .classes("w-full")
        )

        folder_cat_select = (
            ui.select(
                options={None: "-- Gắn vào Danh mục (Tùy chọn) --"},
                value=None,
                label="Thuộc Danh mục",
            )
            .props("outlined dense")
            .classes("w-full")
        )

        folder_desc_input = (
            ui.textarea(
                label="Mô tả thư mục (tùy chọn)", placeholder="Ghi chú khái quát..."
            )
            .props("outlined dense rows=2")
            .classes("w-full")
        )

        async def handle_create_folder() -> None:
            fname = (
                folder_name_input.value.strip() if folder_name_input.value else ""
            )
            if not fname:
                show_toast("Vui lòng nhập tên thư mục", "warning")
                return
            parent_val = folder_parent_select.value
            cat_val = folder_cat_select.value
            desc_val = (
                folder_desc_input.value.strip() if folder_desc_input.value else ""
            )

            res = await api.create_folder(
                name=fname,
                user_id=active_user_id,
                parent_id=parent_val,
                category_id=cat_val,
                description=desc_val,
            )
            if isinstance(res, dict) and "id" in res:
                show_toast(f"Đã tạo thư mục '{fname}'!", "positive")
                dialog.close()
                folder_name_input.value = ""
                folder_desc_input.value = ""
                await on_created()
            elif isinstance(res, dict) and res.get("error"):
                show_toast(res.get("message", "Lỗi tạo thư mục"), "negative")

        ui.button(
            "TẠO THƯ MỤC", icon="check", on_click=handle_create_folder
        ).classes(
            f"w-full py-3 bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold rounded-xl shadow-md transition duration-200 cursor-pointer"
        )

    return {
        "dialog": dialog,
        "open": dialog.open,
        "parent_select": folder_parent_select,
        "cat_select": folder_cat_select,
    }


def render_create_deck_dialog(
    active_user_id: int,
    on_created: Callable[[], Any],
) -> Dict[str, Any]:
    """Create deck dialog with category and folder bindings."""
    with ui.dialog() as dialog, ui.card().classes(
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
            ui.button(icon="close", on_click=dialog.close).props(
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

        deck_category_select = (
            ui.select(
                options={None: "-- Chọn Danh mục (Tùy chọn) --"},
                value=None,
                label="Danh mục môn học",
            )
            .props("outlined dense")
            .classes("w-full")
        )

        deck_folder_select = (
            ui.select(
                options={None: "-- Chọn Thư mục (Tùy chọn) --"},
                value=None,
                label="Thư mục chứa bộ thẻ",
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
            cat_id_val = deck_category_select.value
            folder_id_val = deck_folder_select.value

            res = await api.create_deck(
                title=title_val,
                description=desc_val,
                user_id=active_user_id,
                category_id=cat_id_val,
                folder_id=folder_id_val,
            )
            if isinstance(res, dict) and "id" in res:
                show_toast(f"Tạo thành công bộ thẻ '{title_val}'!", "positive")
                dialog.close()
                deck_title_input.value = ""
                deck_desc_input.value = ""
                await on_created()
            elif isinstance(res, dict) and res.get("error"):
                show_toast(res.get("message", "Lỗi tạo Deck"), "negative")

        ui.button(
            "TẠO BỘ THẺ NGAY", icon="check", on_click=handle_create_deck
        ).classes(
            f"w-full py-3 bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold rounded-xl shadow-md transition duration-200 cursor-pointer"
        )

    return {
        "dialog": dialog,
        "open": dialog.open,
        "category_select": deck_category_select,
        "folder_select": deck_folder_select,
    }


__all__ = [
    "render_create_category_dialog",
    "render_create_folder_dialog",
    "render_create_deck_dialog",
    "render_deck_detail_dialog",
    "open_deck_manager_dialog",
]

