from typing import Any, Dict, Optional
from nicegui import app, ui
from components.layout import TOKENS, show_toast


def get_current_user() -> Optional[Dict[str, Any]]:
    """Lấy thông tin người dùng từ session storage (None nếu là khách)."""
    try:
        return app.storage.user.get("user", None)
    except Exception:
        return None


def set_current_user(user: Optional[Dict[str, Any]]) -> None:
    """Ghi hoặc xóa dữ liệu người dùng khỏi session storage."""
    try:
        if user:
            app.storage.user["user"] = user
        else:
            app.storage.user.pop("user", None)
    except Exception:
        pass


def render_auth_dialog() -> Dict[str, Any]:
    """Modal Dialog đăng nhập / đăng ký chuẩn Clean EdTech UI."""
    with ui.dialog() as dialog, ui.card().classes(
        "w-full max-w-md p-6 rounded-3xl bg-white shadow-2xl border border-slate-100 gap-4"
    ):
        with ui.row().classes(
            "w-full items-center justify-between pb-2 border-b border-slate-100"
        ):
            with ui.row().classes("items-center gap-2"):
                with ui.element("div").classes(
                    f"w-8 h-8 rounded-lg bg-{TOKENS['primary_light']} flex items-center justify-center text-{TOKENS['primary']}"
                ):
                    ui.icon("lock", size="18px")
                dialog_title = ui.label("Đăng nhập").classes(
                    f"text-lg font-extrabold text-{TOKENS['text_primary']}"
                )
            ui.button(icon="close", on_click=dialog.close).props(
                "flat dense round"
            ).classes("text-slate-400 hover:text-slate-700")

        with ui.tabs().classes(
            f"w-full border-b border-{TOKENS['border']} text-{TOKENS['text_secondary']}"
        ) as auth_tabs:
            tab_login = ui.tab("login", label="Đăng nhập").classes("font-bold text-sm")
            tab_register = ui.tab("register", label="Đăng ký").classes(
                "font-bold text-sm"
            )

        with ui.tab_panels(auth_tabs, value=tab_login).classes(
            "w-full bg-transparent p-0 mt-2"
        ):
            # Panel Đăng nhập
            with ui.tab_panel(tab_login).classes("p-0 gap-3 flex flex-col"):
                login_email = (
                    ui.input(
                        label="Email hoặc Tên đăng nhập",
                        placeholder="student@eduflash.ai",
                    )
                    .props("outlined dense")
                    .classes("w-full")
                )

                login_password = (
                    ui.input(
                        label="Mật khẩu",
                        password=True,
                        password_toggle_button=True,
                    )
                    .props("outlined dense")
                    .classes("w-full")
                )

                async def handle_login() -> None:
                    email_val = login_email.value.strip() if login_email.value else ""
                    pass_val = (
                        login_password.value.strip() if login_password.value else ""
                    )

                    if not email_val or not pass_val:
                        show_toast("Vui lòng điền đầy đủ email và mật khẩu", "warning")
                        return

                    user_payload = {
                        "email": email_val,
                        "name": email_val.split("@")[0].capitalize(),
                        "user_id": 1,
                    }
                    set_current_user(user_payload)
                    show_toast(
                        f"Đăng nhập thành công! Chào mừng {user_payload['name']}",
                        "positive",
                    )
                    dialog.close()
                    ui.run_javascript("location.reload()")

                ui.button("ĐĂNG NHẬP", on_click=handle_login).classes(
                    f"w-full py-2.5 mt-2 bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold rounded-xl shadow-sm transition-all"
                )

            # Panel Đăng ký
            with ui.tab_panel(tab_register).classes("p-0 gap-3 flex flex-col"):
                reg_name = (
                    ui.input(
                        label="Họ và tên",
                        placeholder="Nguyễn Văn A",
                    )
                    .props("outlined dense")
                    .classes("w-full")
                )

                reg_email = (
                    ui.input(
                        label="Địa chỉ Email",
                        placeholder="user@eduflash.ai",
                    )
                    .props("outlined dense")
                    .classes("w-full")
                )

                reg_password = (
                    ui.input(
                        label="Mật khẩu",
                        password=True,
                        password_toggle_button=True,
                    )
                    .props("outlined dense")
                    .classes("w-full")
                )

                async def handle_register() -> None:
                    email_val = reg_email.value.strip() if reg_email.value else ""
                    pass_val = reg_password.value.strip() if reg_password.value else ""
                    name_val = reg_name.value.strip() if reg_name.value else ""

                    if not email_val or not pass_val:
                        show_toast("Vui lòng nhập email và mật khẩu", "warning")
                        return

                    user_payload = {
                        "email": email_val,
                        "name": name_val or email_val.split("@")[0].capitalize(),
                        "user_id": 1,
                    }
                    set_current_user(user_payload)
                    show_toast("Đăng ký tài khoản thành công!", "positive")
                    dialog.close()
                    ui.run_javascript("location.reload()")

                ui.button("TẠO TÀI KHOẢN", on_click=handle_register).classes(
                    f"w-full py-2.5 mt-2 bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold rounded-xl shadow-sm transition-all"
                )

    def open_modal(mode: str = "login") -> None:
        if mode == "register":
            auth_tabs.set_value(tab_register)
            dialog_title.text = "Đăng ký tài khoản"
        else:
            auth_tabs.set_value(tab_login)
            dialog_title.text = "Đăng nhập"
        dialog.open()

    return {"dialog": dialog, "open": open_modal}


def render_navbar(
    active_tab: str = "home", current_user: Optional[Dict[str, Any]] = None
) -> ui.header:
    """Thanh điều hướng độc lập hỗ trợ Authentication State và đồng bộ theme TOKENS.

    - Brand Identity: Icon auto_stories, logo 'EduFlash AI', sub-badge 'Smart Repetition' (indigo-600).
    - Navigation Links:
        * Soạn bài / Tải tài liệu ('/', icon: 'post_add')
        * Thư viện ôn tập ('/decks', icon: 'style')
        * Tiến độ SM-2 ('/study', icon: 'school')
        * Trạng thái tab được chọn: bg-white text-indigo-600 shadow-sm rounded-lg.
    - User Actions:
        * Guest (current_user is None): Nút 'Đăng nhập' (flat) & 'Bắt đầu ngay' (bg-indigo-600 text-white rounded-xl shadow-sm).
        * Authenticated: Avatar tròn mang chữ cái đầu kèm menu dropdown (Hồ sơ, Đăng xuất).
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
        auth_ctrl = render_auth_dialog()

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

        # 2. Navigation Links
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

        # 3. User Actions (Góc phải)
        if user is None:
            with ui.row().classes("items-center gap-2"):
                ui.button(
                    "Đăng nhập",
                    on_click=lambda: auth_ctrl["open"]("login"),
                ).props("flat").classes(
                    "text-slate-700 hover:text-indigo-600 font-semibold px-4 py-2 cursor-pointer transition-colors duration-150"
                )

                ui.button(
                    "Bắt đầu ngay",
                    on_click=lambda: auth_ctrl["open"]("register"),
                ).classes(
                    f"bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold px-4 py-2 rounded-xl shadow-sm transition-all duration-150 cursor-pointer"
                )
        else:
            user_name = user.get("name") or "User"
            user_email = user.get("email") or "user@eduflash.ai"
            initial = (user_name[:1]).upper()

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
                            ui.label(user_email).classes(
                                f"text-sm font-bold text-{TOKENS['text_primary']} truncate max-w-[180px]"
                            )

                        with ui.menu_item(
                            on_click=lambda: show_toast(
                                "Chuyển tới Hồ sơ học tập", "info"
                            )
                        ).classes("px-4 py-2 hover:bg-slate-50 cursor-pointer"):
                            with ui.row().classes("items-center gap-2.5"):
                                ui.icon("person_outline", size="18px").classes(
                                    f"text-{TOKENS['text_secondary']}"
                                )
                                ui.label("Hồ sơ học tập").classes(
                                    f"text-sm font-medium text-{TOKENS['text_primary']}"
                                )

                        ui.separator().classes("my-1 border-slate-100")

                        def do_logout() -> None:
                            set_current_user(None)
                            show_toast("Đã đăng xuất thành công", "positive")
                            ui.run_javascript("location.reload()")

                        with ui.menu_item(on_click=do_logout).classes(
                            "px-4 py-2 hover:bg-rose-50 text-rose-600 cursor-pointer"
                        ):
                            with ui.row().classes("items-center gap-2.5"):
                                ui.icon("logout", size="18px").classes("text-rose-500")
                                ui.label("Đăng xuất").classes(
                                    "text-sm font-semibold text-rose-600"
                                )

    return header
