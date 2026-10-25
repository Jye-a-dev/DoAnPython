from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional
from nicegui import ui

from components import TOKENS, app_shell, show_toast
from services import api
from services.auth_guard import set_current_user, redirect_if_authenticated


def render_register_page() -> None:
    """Màn hình Đăng ký Clean EdTech UI tích hợp API Backend POST /api/auth/register."""
    if redirect_if_authenticated("/decks"):
        return

    with app_shell(
        active_tab="register", title="Đăng ký tài khoản - EduFlash AI"
    ):
        with ui.column().classes("w-full items-center justify-center py-8"):
            with ui.card().classes(
                "w-full max-w-md p-8 rounded-3xl bg-white shadow-xl border border-slate-200/80 gap-4"
            ):
                # Header & Brand Icon
                with ui.column().classes("items-center text-center w-full gap-2 mb-1"):
                    with ui.element("div").classes(
                        f"w-14 h-14 rounded-2xl bg-{TOKENS['primary_light']} flex items-center justify-center text-{TOKENS['primary']} shadow-inner mb-1"
                    ):
                        ui.icon("person_add", size="30px")
                    ui.label("Tạo tài khoản mới").classes(
                        f"text-2xl font-black text-{TOKENS['text_primary']} tracking-tight"
                    )
                    ui.label("Bắt đầu tự động hóa ghi nhớ với AI & thuật toán SM-2").classes(
                        f"text-sm text-{TOKENS['text_secondary']}"
                    )

                # Form Controls
                name_input = (
                    ui.input(
                        label="Tên hiển thị",
                        placeholder="Nguyễn Văn A",
                    )
                    .props("outlined clearable")
                    .classes("w-full")
                )

                email_input = (
                    ui.input(
                        label="Địa chỉ Email",
                        placeholder="student@eduflash.ai",
                    )
                    .props("outlined clearable")
                    .classes("w-full")
                )

                password_input = (
                    ui.input(
                        label="Mật khẩu",
                        placeholder="Tối thiểu 6 ký tự",
                        password=True,
                        password_toggle_button=True,
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                confirm_password_input = (
                    ui.input(
                        label="Xác nhận mật khẩu",
                        placeholder="Nhập lại mật khẩu",
                        password=True,
                        password_toggle_button=True,
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                # Feedback Alert Area (Hiển thị khi đăng ký lỗi)
                error_label = ui.label("").classes(
                    "w-full p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm hidden font-medium text-center"
                )

                async def handle_register() -> None:
                    name_val = (name_input.value or "").strip()
                    email_val = (email_input.value or "").strip()
                    pass_val = (password_input.value or "").strip()
                    confirm_val = (confirm_password_input.value or "").strip()

                    error_label.classes(add="hidden")

                    if not name_val:
                        show_toast("Vui lòng nhập tên hiển thị", "warning")
                        error_label.text = "Vui lòng nhập tên hiển thị"
                        error_label.classes(remove="hidden")
                        return

                    if not email_val or "@" not in email_val:
                        show_toast("Vui lòng nhập địa chỉ email hợp lệ", "warning")
                        error_label.text = "Vui lòng nhập địa chỉ email hợp lệ"
                        error_label.classes(remove="hidden")
                        return

                    if not pass_val or len(pass_val) < 6:
                        show_toast("Mật khẩu phải chứa ít nhất 6 ký tự", "warning")
                        error_label.text = "Mật khẩu phải chứa ít nhất 6 ký tự"
                        error_label.classes(remove="hidden")
                        return

                    if pass_val != confirm_val:
                        show_toast("Mật khẩu xác nhận không khớp", "warning")
                        error_label.text = "Mật khẩu xác nhận không khớp"
                        error_label.classes(remove="hidden")
                        return

                    register_btn.props("loading")
                    try:
                        res = await api.auth_register(
                            display_name=name_val,
                            email=email_val,
                            password=pass_val,
                        )

                        if isinstance(res, dict) and res.get("error"):
                            err_msg = res.get("message") or "Đăng ký không thành công. Email có thể đã tồn tại."
                            show_toast(err_msg, "negative")
                            error_label.text = err_msg
                            error_label.classes(remove="hidden")
                            return

                        user_data = res.get("user") if isinstance(res, dict) and "user" in res else res
                        if isinstance(user_data, dict) and user_data.get("id"):
                            # Tự động đăng nhập phiên làm việc ngay sau khi tạo tài khoản
                            if "display_name" not in user_data:
                                user_data["display_name"] = name_val
                            set_current_user(user_data)
                            show_toast("Tạo tài khoản thành công! Đang chuyển hướng...", "positive")
                            ui.navigate.to("/decks")
                        else:
                            show_toast("Đăng ký thành công! Vui lòng đăng nhập.", "positive")
                            ui.navigate.to("/login")
                    finally:
                        register_btn.props(remove="loading")

                confirm_password_input.on("keydown.enter", handle_register)

                register_btn = ui.button(
                    "TẠO TÀI KHOẢN", on_click=handle_register
                ).classes(
                    f"w-full py-3 mt-1 bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold rounded-2xl shadow-md transition-all cursor-pointer"
                )

                # Chuyển hướng sang Đăng nhập
                with ui.row().classes("w-full justify-center items-center gap-1.5 mt-2 text-sm"):
                    ui.label("Đã có tài khoản?").classes(f"text-{TOKENS['text_secondary']}")
                    ui.link("Đăng nhập ngay", target="/login").classes(
                        f"text-{TOKENS['primary']} font-bold hover:underline"
                    )

