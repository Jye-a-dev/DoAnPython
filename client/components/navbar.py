from __future__ import annotations

from typing import Any, Dict, Optional
from nicegui import app, ui

from components.layout import TOKENS, show_toast
from services.auth_guard import get_current_user, set_current_user, logout


def render_navbar(
    active_tab: str = "home", current_user: Optional[Dict[str, Any]] = None
) -> ui.header:
    """Thanh điều hướng NiceGUI thích ứng theo trạng thái xác thực (Guest vs Authenticated).

    - Khi Guest (chưa đăng nhập):
        * Quick Links: 'Trang chủ' (/), 'Tính năng AI' (/#workspace-studio).
        * User Actions: Cụm nút 'Đăng nhập' (/login) & 'Bắt đầu ngay' (/register).
    - Khi Authenticated (đã đăng nhập):
        * Quick Links: 'Soạn bài' (/), 'Bộ thẻ' (/decks), 'Ôn tập SM-2' (/study).
        * User Actions: Avatar ký tự đầu người dùng thật, menu 'Hồ sơ học tập' (/profile) & 'Đăng xuất'.
    """
    normalized_tab = active_tab.strip("/").lower() or "home"
    if active_tab == "/":
        normalized_tab = "home"

    # Ưu tiên current_user truyền vào, fallback kiểm tra session storage
    user = current_user if current_user is not None else get_current_user()

    header = ui.header().classes(
        "sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-slate-200 "
        "text-slate-900 px-6 py-3 shadow-none flex items-center justify-between"
    )

    with header:
        # 1. Brand Identity
        with ui.link(target="/").classes(
            "flex items-center gap-3 no-underline group select-none"
        ):
            with ui.element("div").classes(
                f"w-10 h-10 rounded-xl bg-gradient-to-tr from-{TOKENS['primary']} to-indigo-500 "
                "flex items-center justify-center text-white shadow-sm shadow-indigo-200 "
                "group-hover:scale-105 transition-all duration-200"
            ):
                ui.icon("auto_stories", size="22px")
            with ui.column().classes("gap-0 leading-tight"):
                ui.label("EduFlash AI").classes(
                    f"text-lg font-extrabold tracking-tight text-{TOKENS['text_primary']}"
                )
                with ui.element("div").classes(
                    "inline-flex items-center px-1.5 py-0.2 rounded text-[10px] font-bold text-indigo-600 bg-indigo-50 border border-indigo-100/80 uppercase tracking-wider"
                ):
                    ui.label("Smart Repetition")

        # 2. Navigation Quick Links theo trạng thái người dùng
        if user is None:
            nav_items = [
                {
                    "id": "home",
                    "label": "Trang chủ",
                    "path": "/",
                    "icon": "home",
                },
                {
                    "id": "features",
                    "label": "Tính năng AI",
                    "path": "/#workspace-studio",
                    "icon": "auto_awesome",
                },
            ]
        else:
            nav_items = [
                {
                    "id": "home",
                    "label": "Soạn bài",
                    "path": "/",
                    "icon": "post_add",
                },
                {
                    "id": "decks",
                    "label": "Bộ thẻ",
                    "path": "/decks",
                    "icon": "style",
                },
                {
                    "id": "study",
                    "label": "Ôn tập SM-2",
                    "path": "/study",
                    "icon": "school",
                },
            ]

        with ui.row().classes(
            "items-center bg-slate-100/90 p-1.5 rounded-xl border border-slate-200/80 gap-1"
        ):
            for item in nav_items:
                is_active = (normalized_tab == item["id"]) or (
                    active_tab == item["path"]
                )
                tab_classes = (
                    "flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-semibold "
                    "transition-all duration-200 no-underline "
                )
                if is_active:
                    tab_classes += (
                        "bg-white text-indigo-600 shadow-sm border border-slate-200/60"
                    )
                else:
                    tab_classes += f"text-{TOKENS['text_secondary']} hover:text-{TOKENS['text_primary']} hover:bg-white/60"

                with ui.link(target=item["path"]).classes(tab_classes):
                    ui.icon(item["icon"], size="18px").classes(
                        "text-indigo-600"
                        if is_active
                        else f"text-{TOKENS['text_secondary']}"
                    )
                    ui.label(item["label"])

        # 3. User Actions (Góc phải)
        if user is None:
            # GUEST: Cụm nút Đăng nhập và Bắt đầu ngay (Không avatar / email giả)
            with ui.row().classes("items-center gap-2"):
                with ui.link(target="/login").classes("no-underline"):
                    ui.button("Đăng nhập").props("flat").classes(
                        "text-slate-700 hover:text-indigo-600 font-semibold px-4 py-2 cursor-pointer transition-colors duration-150"
                    )

                with ui.link(target="/register").classes("no-underline"):
                    ui.button("Bắt đầu ngay").classes(
                        f"bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold px-4 py-2 rounded-xl shadow-sm transition-all duration-150 cursor-pointer"
                    )
        else:
            # AUTHENTICATED: Avatar ký tự đầu người dùng thật và menu dropdown
            raw_name = (
                user.get("display_name")
                or user.get("full_name")
                or user.get("username")
                or user.get("name")
                or "User"
            )
            user_name = str(raw_name).strip()
            user_email = user.get("email") or ""
            initial = (user_name[:1] if user_name else "U").upper()

            with ui.row().classes("items-center gap-3"):
                with ui.avatar(size="38px").classes(
                    f"cursor-pointer ring-2 ring-indigo-100 bg-gradient-to-br from-indigo-50 to-{TOKENS['primary_light']} "
                    f"text-{TOKENS['primary']} font-bold select-none hover:ring-indigo-300 transition-all duration-200 shadow-xs"
                ):
                    ui.label(initial)
                    with ui.menu().classes(
                        "rounded-2xl shadow-xl border border-slate-100 py-1.5 min-w-[210px] bg-white"
                    ):
                        with ui.column().classes(
                            "px-4 py-2 border-b border-slate-100 gap-0.5"
                        ):
                            ui.label(user_name).classes(
                                f"text-xs font-semibold text-{TOKENS['text_secondary']}"
                            )
                            if user_email:
                                ui.label(user_email).classes(
                                    f"text-sm font-bold text-{TOKENS['text_primary']} truncate max-w-[180px]"
                                )

                        with ui.menu_item(
                            on_click=lambda: ui.navigate.to("/profile")
                        ).classes("px-4 py-2 hover:bg-slate-50 cursor-pointer"):
                            with ui.row().classes("items-center gap-2.5"):
                                ui.icon("person_outline", size="18px").classes(
                                    f"text-{TOKENS['text_secondary']}"
                                )
                                ui.label("Hồ sơ học tập").classes(
                                    f"text-sm font-medium text-{TOKENS['text_primary']}"
                                )

                        ui.separator().classes("my-1 border-slate-100")

                        with ui.menu_item(on_click=logout).classes(
                            "px-4 py-2 hover:bg-rose-50 text-rose-600 cursor-pointer"
                        ):
                            with ui.row().classes("items-center gap-2.5"):
                                ui.icon("logout", size="18px").classes("text-rose-500")
                                ui.label("Đăng xuất").classes(
                                    "text-sm font-semibold text-rose-600"
                                )

    return header
