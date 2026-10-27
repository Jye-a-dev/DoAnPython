from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from nicegui import ui

from components.layout import TOKENS


def render_deck_sidebar(
    categories_list: List[Dict[str, Any]],
    folders_list: List[Dict[str, Any]],
    decks_list: List[Dict[str, Any]],
    filter_state: Dict[str, Any],
    on_filter_change: Callable[[Optional[int], Optional[int]], Any],
    on_create_category: Callable[[], Any],
    on_create_folder: Callable[[], Any],
) -> None:
    """Render Left Sidebar with subject categories and hierarchical folders tree."""
    with ui.card().classes(
        "w-full lg:w-72 shrink-0 bg-white border border-slate-200 rounded-3xl p-5 shadow-xs gap-5"
    ):
        # Khối 1: Danh mục môn học (categories)
        with ui.column().classes("w-full gap-2"):
            with ui.row().classes("items-center justify-between w-full"):
                with ui.row().classes("items-center gap-1.5"):
                    ui.icon("palette", size="18px").classes(f"text-{TOKENS['primary']}")
                    ui.label("Danh Mục Môn").classes(
                        "text-xs font-extrabold uppercase tracking-wider text-slate-700"
                    )
                ui.button(
                    icon="add", on_click=on_create_category
                ).props("flat dense round").classes(
                    "text-slate-400 hover:text-indigo-600 text-xs"
                ).tooltip("Tạo danh mục mới")

            all_cat_active = (
                filter_state["category_id"] is None
                and filter_state["folder_id"] is None
            )
            ui.button(
                "Tất cả danh mục",
                on_click=lambda: on_filter_change(None, None),
            ).props("flat").classes(
                f"w-full text-left justify-start rounded-xl px-3 py-2 text-xs font-bold transition-all "
                + (
                    f"bg-{TOKENS['primary_light']} text-{TOKENS['primary']}"
                    if all_cat_active
                    else "text-slate-600 hover:bg-slate-50"
                )
            )

            with ui.column().classes("w-full gap-1 pl-1 max-h-48 overflow-y-auto pr-1"):
                for cat in categories_list:
                    c_id = cat.get("id")
                    c_name = cat.get("name", "Chưa đặt tên")
                    c_color = cat.get("color_code", "#3B82F6")
                    is_active = filter_state["category_id"] == c_id

                    cat_deck_count = sum(
                        1 for d in decks_list if d.get("category_id") == c_id
                    )

                    with ui.row().classes(
                        f"items-center justify-between w-full px-2.5 py-1.5 rounded-xl text-xs cursor-pointer transition-all "
                        + (
                            "bg-indigo-50 text-indigo-900 font-extrabold shadow-2xs"
                            if is_active
                            else "text-slate-600 hover:bg-slate-50 font-medium"
                        )
                    ).on("click", lambda cid=c_id: on_filter_change(cid, None)):
                        with ui.row().classes("items-center gap-2"):
                            ui.element("span").classes(
                                "w-2.5 h-2.5 rounded-full inline-block shrink-0 shadow-2xs"
                            ).style(f"background-color: {c_color}")
                            ui.label(c_name).classes("truncate max-w-[140px]")
                        ui.label(str(cat_deck_count)).classes(
                            "text-[11px] text-slate-400 font-bold"
                        )

        ui.separator().classes("bg-slate-100")

        # Khối 2: Cây thư mục phân cấp (folders theo parent_id)
        with ui.column().classes("w-full gap-2"):
            with ui.row().classes("items-center justify-between w-full"):
                with ui.row().classes("items-center gap-1.5"):
                    ui.icon("account_tree", size="18px").classes("text-indigo-600")
                    ui.label("Cây Thư Mục").classes(
                        "text-xs font-extrabold uppercase tracking-wider text-slate-700"
                    )
                ui.button(
                    icon="add", on_click=on_create_folder
                ).props("flat dense round").classes(
                    "text-slate-400 hover:text-indigo-600 text-xs"
                ).tooltip("Tạo thư mục mới")

            root_folders = [f for f in folders_list if f.get("parent_id") is None]
            children_by_parent: Dict[int, List[Dict[str, Any]]] = {}
            for f in folders_list:
                p_id = f.get("parent_id")
                if p_id is not None:
                    children_by_parent.setdefault(p_id, []).append(f)

            with ui.column().classes("w-full gap-1 pl-1 max-h-56 overflow-y-auto pr-1"):
                if not folders_list:
                    ui.label("Chưa có thư mục").classes("text-xs text-slate-400 italic py-1")

                for rf in root_folders:
                    rf_id = rf.get("id")
                    rf_name = rf.get("name", "Thư mục")
                    is_rf_active = filter_state["folder_id"] == rf_id
                    rf_deck_count = sum(
                        1 for d in decks_list if d.get("folder_id") == rf_id
                    )

                    with ui.row().classes(
                        f"items-center justify-between w-full px-2 py-1.5 rounded-xl text-xs cursor-pointer transition-all "
                        + (
                            "bg-indigo-50 text-indigo-900 font-extrabold shadow-2xs"
                            if is_rf_active
                            else "text-slate-700 hover:bg-slate-50 font-medium"
                        )
                    ).on("click", lambda fid=rf_id: on_filter_change(None, fid)):
                        with ui.row().classes("items-center gap-1.5"):
                            ui.icon("folder", size="16px").classes("text-indigo-500")
                            ui.label(rf_name).classes("truncate max-w-[130px]")
                        ui.label(str(rf_deck_count)).classes(
                            "text-[11px] text-slate-400 font-bold"
                        )

                    child_folders = (
                        children_by_parent.get(rf_id, []) if rf_id is not None else []
                    )
                    for cf in child_folders:
                        cf_id = cf.get("id")
                        cf_name = cf.get("name", "Thư mục con")
                        is_cf_active = filter_state["folder_id"] == cf_id
                        cf_deck_count = sum(
                            1 for d in decks_list if d.get("folder_id") == cf_id
                        )

                        with ui.row().classes(
                            f"items-center justify-between w-full pl-6 pr-2 py-1 rounded-lg text-xs cursor-pointer transition-all "
                            + (
                                "bg-indigo-100/60 text-indigo-950 font-extrabold"
                                if is_cf_active
                                else "text-slate-500 hover:bg-slate-50 font-normal"
                            )
                        ).on("click", lambda fid=cf_id: on_filter_change(None, fid)):
                            with ui.row().classes("items-center gap-1.5"):
                                ui.icon("subdirectory_arrow_right", size="14px").classes(
                                    "text-slate-400"
                                )
                                ui.label(cf_name).classes("truncate max-w-[110px]")
                            ui.label(str(cf_deck_count)).classes(
                                "text-[10px] text-slate-400"
                            )

