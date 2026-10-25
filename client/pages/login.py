from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional
from nicegui import ui

from components import TOKENS, app_shell, show_toast
from services import api
from services.auth_guard import set_current_user, redirect_if_authenticated


def render_login_page() -> None:
    """Màn hình Đăng nhập Clean EdTech UI tích hợp API Backend POST /api/auth/login."""
    if redirect_if_authenticated("/decks"):
        return

    with app_shell(
        active_tab="login", title="Đăng nhập - EduFlash AI"
    ):
        with ui.column().classes("w-full items-center justify-center py-8"):
            with ui.card().classes(
                "w-full max-w-md p-8 rounded-3xl bg-white shadow-xl border border-slate-200/80 gap-5"
            ):
                # Header & Brand Icon
                with ui.column().classes("items-center text-center w-full gap-2 mb-2"):
                    with ui.element("div").classes(
                        f"w-14 h-14 rounded-2xl bg-{TOKENS['primary_light']} flex items-center justify-center text-{TOKENS['primary']} shadow-inner mb-1"
                    ):
                        ui.icon("lock", size="30px")
                    ui.label("Đăng nhập tài khoản").classes(
                        f"text-2xl font-black text-{TOKENS['text_primary']} tracking-tight"
                    )
                    ui.label("Truy cập kho thẻ ghi nhớ và chu trình ôn tập SM-2").classes(
                        f"text-sm text-{TOKENS['text_secondary']}"
                    )

                # Form Controls
                login_input = (
                    ui.input(
                        label="Email hoặc Tên đăng nhập",
                        placeholder="student@eduflash.ai hoặc username",
                    )
                    .props("outlined clearable")
                    .classes("w-full")
                )

                password_input = (
                    ui.input(
                        label="Mật khẩu",
                        placeholder="••••••••",
                        password=True,
                        password_toggle_button=True,
                    )
                    .props("outlined")
                    .classes("w-full")
                )

                # Feedback Alert Area (Hiển thị khi đăng nhập lỗi)
                error_label = ui.label("").classes(
                    "w-full p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm hidden font-medium text-center"
                )

                async def handle_login() -> None:
                    login_val = (login_input.value or "").strip()
                    pass_val = (password_input.value or "").strip()

                    error_label.classes(add="hidden")

                    if not login_val:
                        show_toast("Vui lòng nhập email hoặc tên đăng nhập", "warning")
                        error_label.text = "Vui lòng nhập email hoặc tên đăng nhập"
                        error_label.classes(remove="hidden")
                        return

                    if not pass_val:
                        show_toast("Vui lòng nhập mật khẩu", "warning")
                        error_label.text = "Vui lòng nhập mật khẩu"
                        error_label.classes(remove="hidden")
                        return

                    login_btn.props("loading")
                    try:
                        res = await api.auth_login(login=login_val, password=pass_val)

                        if isinstance(res, dict) and res.get("error"):
                            err_msg = res.get("message") or "Thông tin đăng nhập không chính xác"
                            show_toast(err_msg, "negative")
                            error_label.text = err_msg
                            error_label.classes(remove="hidden")
                            return

                        # Trích xuất user payload từ phản hồi chuẩn
                        user_data = res.get("user") if isinstance(res, dict) and "user" in res else res
                        if not isinstance(user_data, dict) or not user_data:
                            user_data = {
                                "id": 1,
                                "username": login_val.split("@")[0],
                                "email": login_val if "@" in login_val else f"{login_val}@eduflash.ai",
                                "role": "user",
                            }

                        token = res.get("token") if isinstance(res, dict) else None
                        set_current_user(user_data, token=token)

                        name = (
                            user_data.get("display_name")
                            or user_data.get("full_name")
                            or user_data.get("username")
                            or "bạn"
                        )
                        show_toast(f"Đăng nhập thành công! Chào mừng {name}", "positive")
                        ui.navigate.to("/decks")
                    finally:
                        login_btn.props(remove="loading")

                # Phím tắt Enter khi gõ mật khẩu
                password_input.on("keydown.enter", handle_login)
                login_input.on("keydown.enter", handle_login)

                login_btn = ui.button(
                    "ĐĂNG NHẬP", on_click=handle_login
                ).classes(
                    f"w-full py-3 mt-1 bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold rounded-2xl shadow-md transition-all cursor-pointer"
                )

                # Chuyển hướng sang Đăng ký
                with ui.row().classes("w-full justify-center items-center gap-1.5 mt-2 text-sm"):
                    ui.label("Chưa có tài khoản?").classes(f"text-{TOKENS['text_secondary']}")
                    ui.link("Đăng ký ngay", target="/register").classes(
                        f"text-{TOKENS['primary']} font-bold hover:underline"
                    )

