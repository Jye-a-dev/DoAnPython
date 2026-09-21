import reflex as rx
from layouts.base_layout import base_layout
from state.auth_state import AuthState


def login_page() -> rx.Component:
    """Authentication sign-in page with email input, role switching, and quick dev credentials."""
    login_card = rx.center(
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("lock", size=26, color="var(--accent-9)"),
                    rx.heading("Đăng Nhập Tài Khoản", size="5", weight="bold"),
                    align="center",
                    spacing="2",
                ),
                rx.text("Truy cập hệ thống SmartVision E-Commerce & AI Assistant", size="2", color="gray"),
                rx.separator(width="100%"),

                # Login Email Field
                rx.vstack(
                    rx.text("Địa chỉ Email", size="2", weight="medium"),
                    rx.input(
                        placeholder="admin@system.local hoặc user@example.com",
                        value=AuthState.login_email,
                        on_change=AuthState.set_email,
                        size="3",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),

                # Role Selection Field
                rx.vstack(
                    rx.text("Vai trò truy cập (RBAC)", size="2", weight="medium"),
                    rx.select(
                        ["1 - Quản Trị Viên (Admin)", "2 - Khách Hàng (User)"],
                        default_value="1 - Quản Trị Viên (Admin)",
                        on_change=lambda val: AuthState.set_role(val.split(" - ")[0]),
                        size="3",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),

                # Submit Button
                rx.button(
                    rx.hstack(
                        rx.icon("log-in", size=18),
                        rx.text("Đăng Nhập"),
                        align="center",
                        spacing="2",
                    ),
                    on_click=AuthState.login,
                    loading=AuthState.is_loading,
                    color_scheme="indigo",
                    size="3",
                    width="100%",
                ),

                # Error display
                rx.cond(
                    AuthState.error_message != "",
                    rx.callout(
                        AuthState.error_message,
                        icon="circle-alert",
                        color_scheme="red",
                        size="1",
                        width="100%",
                    ),
                ),

                rx.separator(width="100%"),

                # Quick dev login buttons
                rx.vstack(
                    rx.text("Đăng nhập thử nghiệm nhanh (Development):", size="1", color="gray"),
                    rx.hstack(
                        rx.button(
                            rx.hstack(
                                rx.icon("shield-check", size=14),
                                rx.text("Vào làm Admin", size="1"),
                                align="center",
                            ),
                            variant="surface",
                            color_scheme="amber",
                            size="2",
                            on_click=AuthState.dev_login(1),
                        ),
                        rx.button(
                            rx.hstack(
                                rx.icon("user", size=14),
                                rx.text("Vào làm Khách", size="1"),
                                align="center",
                            ),
                            variant="surface",
                            color_scheme="blue",
                            size="2",
                            on_click=AuthState.dev_login(2),
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    spacing="2",
                    width="100%",
                ),
                spacing="4",
                width="100%",
                padding="1rem",
            ),
            max_width="440px",
            width="100%",
            box_shadow="0 6px 20px rgba(0,0,0,0.1)",
        ),
        min_height="75vh",
        padding="2rem",
        width="100%",
    )

    return base_layout(login_card, role_required="public")

