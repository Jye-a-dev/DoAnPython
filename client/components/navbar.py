from typing import Optional
from nicegui import ui
from components.layout import TOKENS, show_toast


def render_navbar(active_tab: str = "home") -> ui.header:
    """Thanh điều hướng độc lập chuẩn EdTech Clean Minimalist.

    - Brand Header: Icon auto_stories, text 'EduFlash AI', phụ đề 'Smart Repetition'.
    - Quick Navigation Tabs:
        * Soạn bài / Tải tài liệu ('/', icon: 'post_add')
        * Thư viện ôn tập ('/decks', icon: 'style')
        * Tiến độ SM-2 ('/study', icon: 'school')
    - Quản lý trạng thái active nổi bật (bg-white text-indigo-600 shadow-sm), chuyển mượt transition-all duration-200.
    """
    normalized_tab = active_tab.strip("/").lower() or "home"
    if active_tab == "/":
        normalized_tab = "home"

    header = ui.header().classes(
        "sticky top-0 z-50 bg-white/85 backdrop-blur-md border-b border-slate-200 "
        "text-slate-900 px-6 py-3 shadow-none flex items-center justify-between"
    )

    with header:
        # 1. Brand Header
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
                ui.label("Smart Repetition").classes(
                    f"text-[10px] font-semibold text-{TOKENS['text_secondary']} uppercase tracking-wider"
                )

        # 2. Quick Navigation Tabs
        nav_items = [
            {
                "id": "home",
                "label": "Soạn bài / Tải tài liệu",
                "path": "/",
                "icon": "post_add",
            },
            {
                "id": "decks",
                "label": "Thư viện ôn tập",
                "path": "/decks",
                "icon": "style",
            },
            {
                "id": "study",
                "label": "Tiến độ SM-2",
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

        # 3. Profile Avatar & Dropdown Menu
        with ui.row().classes("items-center gap-3"):
            with ui.avatar(size="38px").classes(
                f"cursor-pointer ring-2 ring-indigo-100 bg-gradient-to-br from-indigo-50 to-{TOKENS['primary_light']} "
                f"text-{TOKENS['primary']} font-bold select-none hover:ring-indigo-300 transition-all duration-200 shadow-xs"
            ):
                ui.label("EF")
                with ui.menu().classes(
                    "rounded-2xl shadow-xl border border-slate-100 py-1.5 min-w-[200px] bg-white"
                ):
                    with ui.column().classes(
                        "px-4 py-2 border-b border-slate-100 gap-0.5"
                    ):
                        ui.label("Học viên").classes(
                            f"text-xs font-semibold text-{TOKENS['text_secondary']}"
                        )
                        ui.label("student@eduflash.ai").classes(
                            f"text-sm font-bold text-{TOKENS['text_primary']} truncate max-w-[170px]"
                        )

                    with ui.menu_item(
                        on_click=lambda: show_toast("Chuyển tới Hồ sơ cá nhân", "info")
                    ).classes("px-4 py-2 hover:bg-slate-50 cursor-pointer"):
                        with ui.row().classes("items-center gap-2.5"):
                            ui.icon("person_outline", size="18px").classes(
                                f"text-{TOKENS['text_secondary']}"
                            )
                            ui.label("Hồ sơ").classes(
                                f"text-sm font-medium text-{TOKENS['text_primary']}"
                            )

                    with ui.menu_item(
                        on_click=lambda: show_toast(
                            "Chuyển tới Cài đặt tài khoản", "info"
                        )
                    ).classes("px-4 py-2 hover:bg-slate-50 cursor-pointer"):
                        with ui.row().classes("items-center gap-2.5"):
                            ui.icon("settings", size="18px").classes(
                                f"text-{TOKENS['text_secondary']}"
                            )
                            ui.label("Cài đặt").classes(
                                f"text-sm font-medium text-{TOKENS['text_primary']}"
                            )

                    ui.separator().classes("my-1 border-slate-100")

                    with ui.menu_item(
                        on_click=lambda: show_toast(
                            "Đã đăng xuất thành công", "positive"
                        )
                    ).classes(
                        "px-4 py-2 hover:bg-rose-50 text-rose-600 cursor-pointer"
                    ):
                        with ui.row().classes("items-center gap-2.5"):
                            ui.icon("logout", size="18px").classes("text-rose-500")
                            ui.label("Đăng xuất").classes(
                                "text-sm font-semibold text-rose-600"
                            )

    return header
