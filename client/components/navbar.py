import reflex as rx
from state.auth_state import AuthState
from state.cart_state import CartState
from state.detect_state import DetectState
from state.product_state import ProductState


def navbar() -> rx.Component:
    """Header điều hướng thích ứng động theo 3 phân quyền: Khách vãng lai, Người dùng và Quản trị viên."""

    # 1. Khối thương hiệu và Logo
    brand_logo = rx.link(
        rx.hstack(
            rx.box(
                rx.icon("scan-eye", size=24, color="white"),
                background="linear-gradient(135deg, #6366f1, #8b5cf6)",
                padding="6px",
                border_radius="10px",
                box_shadow="0 2px 10px rgba(99, 102, 241, 0.4)",
            ),
            rx.vstack(
                rx.heading("VisionStore AI", size="4", weight="bold", letter_spacing="-0.02em"),
                rx.text("Smart Visual E-Commerce", size="1", color="gray"),
                spacing="0",
            ),
            align="center",
            spacing="2",
        ),
        href="/",
        underline="none",
        color="inherit",
    )

    # 2. Thanh tìm kiếm nhanh cho sản phẩm
    quick_search_bar = rx.hstack(
        rx.input(
            placeholder="Tìm kiếm sản phẩm, nhãn AI...",
            value=ProductState.search_query,
            on_change=ProductState.set_search_query,
            on_key_down=ProductState.handle_search_key,
            size="2",
            width="250px",
            radius="large",
        ),
        rx.icon_button(
            rx.icon("search", size=16),
            on_click=ProductState.apply_search,
            variant="surface",
            color_scheme="gray",
            size="2",
            radius="large",
        ),
        align="center",
        spacing="1",
        display=["none", "none", "flex"],
    )

    # 3. Nút Quét AI nổi bật với hiệu ứng phát sáng (Glowing border)
    ai_scan_button = rx.button(
        rx.hstack(
            rx.icon("sparkles", size=16, color="white"),
            rx.text("Quét AI", size="2", weight="bold", color="white"),
            rx.badge("AI Powered", color_scheme="amber", variant="solid", radius="full", size="1"),
            align="center",
            spacing="2",
        ),
        on_click=DetectState.open_modal,
        size="2",
        radius="large",
        background="linear-gradient(135deg, #6366f1, #8b5cf6)",
        box_shadow="0 0 16px rgba(139, 92, 246, 0.45)",
        border="1px solid rgba(255, 255, 255, 0.2)",
        cursor="pointer",
        _hover={"transform": "translateY(-1px)", "box_shadow": "0 0 22px rgba(139, 92, 246, 0.65)"},
    )

    # 4. Icon Giỏ hàng kèm Popover nhắc nhở cho Khách chưa đăng nhập
    guest_cart_popover = rx.popover.root(
        rx.popover.trigger(
            rx.icon_button(
                rx.icon("shopping-cart", size=18),
                variant="ghost",
                color_scheme="gray",
                size="2",
                radius="large",
            ),
        ),
        rx.popover.content(
            rx.vstack(
                rx.hstack(
                    rx.icon("info", size=18, color="var(--accent-9)"),
                    rx.heading("Giỏ hàng", size="2", weight="bold"),
                    align="center",
                    spacing="2",
                ),
                rx.text("Vui lòng đăng nhập để lưu trữ và quản lý các mặt hàng trong giỏ.", size="1", color="gray"),
                rx.link(
                    rx.button("Đăng nhập ngay", size="2", color_scheme="indigo", width="100%"),
                    href="/login",
                    width="100%",
                ),
                spacing="3",
                width="220px",
            ),
            side="bottom",
            align="end",
        ),
    )

    # 5. Icon Giỏ hàng có Badge số lượng cho người dùng đã đăng nhập
    user_cart_button = rx.button(
        rx.hstack(
            rx.icon("shopping-bag", size=18),
            rx.badge(
                CartState.total_items,
                color_scheme="ruby",
                variant="solid",
                radius="full",
                size="1",
            ),
            align="center",
            spacing="1",
        ),
        on_click=CartState.open_cart,
        variant="ghost",
        color_scheme="gray",
        size="2",
        radius="large",
    )

    # 6. Khu vực điều hướng cho Khách vãng lai (Unauthorized)
    unauthorized_nav = rx.hstack(
        rx.link(rx.text("Danh mục", size="2", weight="medium"), href="#catalog-section", color="inherit"),
        rx.link(rx.text("Khám phá", size="2", weight="medium"), href="#features-section", color="inherit"),
        rx.link(rx.text("Về chúng tôi", size="2", weight="medium"), href="#footer-section", color="inherit"),
        guest_cart_popover,
        rx.link(
            rx.button(
                rx.hstack(
                    rx.icon("log-in", size=16),
                    rx.text("Đăng nhập", size="2"),
                    align="center",
                ),
                color_scheme="indigo",
                variant="solid",
                size="2",
                radius="large",
            ),
            href="/login",
            underline="none",
        ),
        align="center",
        spacing="4",
    )

    # 7. Khu vực điều hướng cho Người dùng cá nhân (User - Role ID = 2)
    user_nav = rx.hstack(
        ai_scan_button,
        user_cart_button,
        rx.menu.root(
            rx.menu.trigger(
                rx.button(
                    rx.hstack(
                        rx.avatar(
                            fallback="U",
                            src=AuthState.current_user.get("avatar_url", ""),
                            size="1",
                            radius="full",
                        ),
                        rx.text(
                            rx.cond(
                                AuthState.current_user.get("full_name"),
                                AuthState.current_user.get("full_name"),
                                AuthState.current_user.get("email", "Tài khoản"),
                            ),
                            size="2",
                            weight="medium",
                            max_width="110px",
                            truncate=True,
                        ),
                        rx.icon("chevron-down", size=14),
                        align="center",
                        spacing="2",
                    ),
                    variant="surface",
                    color_scheme="gray",
                    size="2",
                    radius="large",
                ),
            ),
            rx.menu.content(
                rx.menu.item(
                    rx.hstack(rx.icon("history", size=14), rx.text("Lịch sử quét của tôi")),
                    on_click=DetectState.open_modal,
                ),
                rx.menu.item(
                    rx.hstack(rx.icon("package", size=14), rx.text("Đơn hàng của tôi")),
                    on_click=CartState.open_cart,
                ),
                rx.menu.separator(),
                rx.menu.item(
                    rx.hstack(rx.icon("log-out", size=14), rx.text("Đăng xuất")),
                    color="red",
                    on_click=AuthState.logout,
                ),
            ),
        ),
        align="center",
        spacing="3",
    )

    # 8. Khu vực điều hướng cho Quản trị viên (Admin - Role ID = 1)
    admin_nav = rx.hstack(
        rx.badge("ADMIN PANEL", color_scheme="ruby", variant="solid", radius="full", size="2"),
        rx.link(
            rx.button(
                rx.hstack(rx.icon("scan-line", size=14), rx.text("OCR Reviews", size="1")),
                variant="ghost",
                size="2",
            ),
            href="/admin",
        ),
        rx.link(
            rx.button(
                rx.hstack(rx.icon("boxes", size=14), rx.text("Kho hàng", size="1")),
                variant="ghost",
                size="2",
            ),
            href="/admin",
        ),
        rx.link(
            rx.button(
                rx.hstack(rx.icon("trending-up", size=14), rx.text("Doanh thu", size="1")),
                variant="ghost",
                size="2",
            ),
            href="/admin",
        ),
        ai_scan_button,
        user_cart_button,
        rx.link(
            rx.button(
                rx.hstack(rx.icon("layout-dashboard", size=16), rx.text("Dashboard")),
                color_scheme="amber",
                variant="surface",
                size="2",
                radius="large",
            ),
            href="/admin",
            underline="none",
        ),
        rx.icon_button(
            rx.icon("log-out", size=16),
            color_scheme="red",
            variant="ghost",
            size="2",
            on_click=AuthState.logout,
        ),
        align="center",
        spacing="2",
    )

    return rx.box(
        rx.hstack(
            brand_logo,
            quick_search_bar,
            rx.spacer(),
            # Render có điều kiện thích ứng chính xác theo 3 phân quyền
            rx.cond(
                AuthState.is_authenticated,
                rx.cond(AuthState.is_admin, admin_nav, user_nav),
                unauthorized_nav,
            ),
            rx.color_mode.button(radius="large"),
            width="100%",
            align="center",
            padding_x=["1rem", "1.5rem", "2rem"],
            padding_y="0.85rem",
            spacing="3",
        ),
        border_bottom="1px solid var(--gray-4)",
        background_color="var(--color-surface)",
        backdrop_filter="blur(16px)",
        position="sticky",
        top="0",
        z_index="30",
        width="100%",
    )
