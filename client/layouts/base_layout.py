import reflex as rx
from components.navbar import navbar
from components.product_card import format_currency_vnd
from components.scan_modal import scan_modal
from state.auth_state import AuthState
from state.cart_state import CartState


def audio_confirmation_drawer() -> rx.Component:
    """Drawer trượt bên phải hiển thị giỏ hàng, form thanh toán và phát âm thanh chốt đơn TTS."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # Tiêu đề giỏ hàng
                rx.hstack(
                    rx.hstack(
                        rx.box(
                            rx.icon("shopping-bag", size=20, color="white"),
                            background="linear-gradient(135deg, #6366f1, #8b5cf6)",
                            padding="6px",
                            border_radius="8px",
                        ),
                        rx.heading("Giỏ Hàng Của Bạn", size="4", weight="bold"),
                        align="center",
                        spacing="2",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.button(
                            rx.icon("x", size=18),
                            variant="ghost",
                            color_scheme="gray",
                            on_click=CartState.close_cart,
                        ),
                    ),
                    width="100%",
                    align="center",
                ),
                rx.separator(width="100%"),

                # Danh sách sản phẩm trong giỏ
                rx.cond(
                    CartState.cart_items.length() > 0,
                    rx.vstack(
                        rx.vstack(
                            rx.foreach(
                                CartState.cart_items,
                                lambda item: rx.card(
                                    rx.hstack(
                                        rx.image(
                                            src=rx.cond(
                                                item["product_image"] != "",
                                                item["product_image"],
                                                "https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=200",
                                            ),
                                            fallback="https://images.unsplash.com/photo-1526170375885-4d8ecf77b99f?w=200",
                                            width="60px",
                                            height="60px",
                                            object_fit="cover",
                                            border_radius="8px",
                                        ),
                                        rx.vstack(
                                            rx.text(item["product_name"], size="2", weight="bold", truncate=True),
                                            rx.text(
                                                rx.cond(
                                                    item["formatted_price"] != "",
                                                    item["formatted_price"],
                                                    item["product_price"].to(str) + " đ",
                                                ),
                                                size="2",
                                                color="var(--accent-9)",
                                                weight="medium",
                                            ),
                                            rx.cond(
                                                item["record_id"] != "",
                                                rx.badge("Khớp từ AI Scan", size="1", color_scheme="violet", variant="surface"),
                                            ),
                                            spacing="1",
                                            align="start",
                                        ),
                                        rx.spacer(),
                                        rx.hstack(
                                            rx.icon_button(
                                                rx.icon("minus", size=14),
                                                size="1",
                                                variant="outline",
                                                on_click=CartState.decrement_item(item["id"]),
                                            ),
                                            rx.text(item["quantity"], size="2", weight="bold"),
                                            rx.icon_button(
                                                rx.icon("plus", size=14),
                                                size="1",
                                                variant="outline",
                                                on_click=CartState.increment_item(item["id"]),
                                            ),
                                            rx.icon_button(
                                                rx.icon("trash-2", size=14),
                                                size="1",
                                                variant="ghost",
                                                color_scheme="red",
                                                on_click=CartState.remove_item(item["id"]),
                                            ),
                                            align="center",
                                            spacing="2",
                                        ),
                                        width="100%",
                                        align="center",
                                    ),
                                    width="100%",
                                    size="1",
                                    border_radius="10px",
                                ),
                            ),
                            width="100%",
                            spacing="2",
                            max_height="260px",
                            overflow_y="auto",
                        ),
                        rx.separator(width="100%"),

                        # Tổng tiền thanh toán
                        rx.hstack(
                            rx.text("Tổng tiền thanh toán:", size="3", weight="medium"),
                            rx.spacer(),
                            rx.text(
                                CartState.formatted_total_amount,
                                size="5",
                                weight="bold",
                                color="var(--accent-9)",
                            ),
                            width="100%",
                            align="center",
                        ),

                        # Form nhập thông tin người nhận
                        rx.vstack(
                            rx.text("Thông tin nhận hàng", size="2", weight="bold"),
                            rx.input(
                                placeholder="Địa chỉ nhận hàng (VD: 123 Nguyễn Trãi, Q.1)",
                                value=CartState.shipping_address,
                                on_change=CartState.set_address,
                                size="2",
                                width="100%",
                                radius="large",
                            ),
                            rx.input(
                                placeholder="Số điện thoại liên hệ (VD: 0901234567)",
                                value=CartState.phone_number,
                                on_change=CartState.set_phone,
                                size="2",
                                width="100%",
                                radius="large",
                            ),
                            spacing="2",
                            width="100%",
                        ),

                        # Nút kích hoạt checkout & phát audio
                        rx.button(
                            rx.hstack(
                                rx.icon("credit-card", size=18),
                                rx.text("Thanh Toán & Xác Nhận Bằng Âm Thanh", size="2", weight="bold"),
                                align="center",
                                spacing="2",
                            ),
                            on_click=CartState.checkout(),
                            loading=CartState.is_checking_out,
                            color_scheme="green",
                            size="3",
                            radius="large",
                            width="100%",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    rx.center(
                        rx.vstack(
                            rx.icon("shopping-basket", size=48, color="gray"),
                            rx.text("Giỏ hàng của bạn đang trống.", size="2", color="gray"),
                            align="center",
                            spacing="2",
                            padding_y="3rem",
                        ),
                        width="100%",
                    ),
                ),

                # Banner xác nhận đặt hàng thành công và Audio Player HTML5
                rx.cond(
                    CartState.checkout_success,
                    rx.card(
                        rx.vstack(
                            rx.hstack(
                                rx.icon("check-check", size=22, color="var(--grass-9)"),
                                rx.heading("Đặt hàng thành công!", size="3", color="var(--grass-9)"),
                                align="center",
                                spacing="2",
                            ),
                            rx.text(
                                f"Mã đơn hàng: {CartState.last_order_id}",
                                size="2",
                                weight="medium",
                            ),
                            rx.cond(
                                CartState.checkout_audio_url != "",
                                rx.vstack(
                                    rx.text("Thông báo giọng đọc xác nhận (Edge-TTS):", size="1", color="gray"),
                                    rx.el.audio(
                                        src=CartState.checkout_audio_url,
                                        controls=True,
                                        auto_play=True,
                                        style={"width": "100%", "height": "40px"},
                                    ),
                                    width="100%",
                                    spacing="1",
                                ),
                            ),
                            spacing="2",
                            width="100%",
                        ),
                        background_color="var(--grass-2)",
                        border="1px solid var(--grass-6)",
                        width="100%",
                        border_radius="10px",
                    ),
                ),
                width="100%",
                spacing="4",
            ),
            max_width="450px",
            width="90vw",
            max_height="88vh",
            overflow_y="auto",
            border_radius="16px",
            padding="1.5rem",
        ),
        open=CartState.is_cart_open,
        on_open_change=CartState.close_cart,
    )


def modern_footer() -> rx.Component:
    """Footer E-Commerce hiện đại với chính sách, cổng thanh toán và trạng thái pipeline AI."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                # Cột 1: Thông tin thương hiệu
                rx.vstack(
                    rx.hstack(
                        rx.box(
                            rx.icon("scan-eye", size=20, color="white"),
                            background="linear-gradient(135deg, #6366f1, #8b5cf6)",
                            padding="5px",
                            border_radius="6px",
                        ),
                        rx.heading("VisionStore AI", size="4", weight="bold"),
                        align="center",
                        spacing="2",
                    ),
                    rx.text(
                        "Nền tảng thương mại điện tử tích hợp Trí tuệ nhân tạo, hỗ trợ quét Camera đối chiếu sản phẩm tức thì và tổng hợp giọng nói xác nhận đơn hàng.",
                        size="1",
                        color="gray",
                        max_width="340px",
                        line_height="1.6",
                    ),
                    rx.hstack(
                        rx.badge("AI Pipeline: Active", color_scheme="grass", variant="surface", size="1"),
                        rx.badge("YOLOv8 + Edge-TTS", color_scheme="indigo", variant="surface", size="1"),
                        spacing="2",
                    ),
                    spacing="2",
                    align="start",
                ),
                rx.spacer(),

                # Cột 2, 3, 4: Liên kết và chính sách
                rx.hstack(
                    rx.vstack(
                        rx.text("Dịch vụ & Mua sắm", size="2", weight="bold"),
                        rx.link("Visual AI Search", href="#", size="1", color="gray"),
                        rx.link("Sản phẩm thịnh hành", href="#catalog-section", size="1", color="gray"),
                        rx.link("Danh mục nổi bật", href="#category-section", size="1", color="gray"),
                        spacing="1",
                        align="start",
                    ),
                    rx.vstack(
                        rx.text("Chính sách & Hỗ trợ", size="2", weight="bold"),
                        rx.link("Chính sách bảo mật", href="#", size="1", color="gray"),
                        rx.link("Quy chế hoạt động", href="#", size="1", color="gray"),
                        rx.link("Đổi trả & Hoàn tiền", href="#", size="1", color="gray"),
                        spacing="1",
                        align="start",
                    ),
                    rx.vstack(
                        rx.text("Cổng thanh toán hỗ trợ", size="2", weight="bold"),
                        rx.hstack(
                            rx.badge("VISA", variant="soft", color_scheme="blue", size="1"),
                            rx.badge("Mastercard", variant="soft", color_scheme="red", size="1"),
                            rx.badge("MoMo", variant="soft", color_scheme="pink", size="1"),
                            rx.badge("VNPay", variant="soft", color_scheme="cyan", size="1"),
                            wrap="wrap",
                            spacing="1",
                        ),
                        rx.text("Hotline: 1900 8899", size="1", color="gray"),
                        rx.text("Email: support@visionstore.ai", size="1", color="gray"),
                        spacing="2",
                        align="start",
                    ),
                    spacing="6",
                    wrap="wrap",
                ),
                width="100%",
                wrap="wrap",
                spacing="5",
            ),
            rx.separator(width="100%"),
            rx.hstack(
                rx.text("© 2026 VisionStore AI Inc. Bản quyền thuộc về hệ thống bán lẻ công nghệ cao.", size="1", color="gray"),
                rx.spacer(),
                rx.hstack(
                    rx.icon("shield-check", size=14, color="var(--grass-9)"),
                    rx.text("Bảo mật SSL 256-bit", size="1", color="gray"),
                    align="center",
                    spacing="1",
                ),
                width="100%",
                align="center",
            ),
            width="100%",
            max_width="1200px",
            margin_x="auto",
            padding_x=["1rem", "1.5rem", "2rem"],
            padding_y="2.5rem",
            spacing="4",
        ),
        border_top="1px solid var(--gray-4)",
        background_color="var(--gray-2)",
        width="100%",
        margin_top="auto",
        id="footer-section",
    )


def base_layout(child_component: rx.Component, role_required: str = "") -> rx.Component:
    """Component Master Layout bọc toàn bộ ứng dụng, quản lý Navbar, Drawer, Modal và Footer."""
    content = child_component
    if role_required == "admin":
        content = rx.cond(
            AuthState.is_admin,
            child_component,
            rx.center(
                rx.vstack(
                    rx.icon("shield-alert", size=48, color="red"),
                    rx.heading("Yêu Cầu Quyền Quản Trị Viên", size="5"),
                    rx.text("Trang này chỉ dành cho quản trị viên hệ thống.", color="gray"),
                    rx.link(rx.button("Về Trang Chủ", variant="soft"), href="/"),
                    spacing="3",
                    align="center",
                    padding="5rem",
                ),
                width="100%",
                min_height="70vh",
            ),
        )

    return rx.box(
        navbar(),
        scan_modal(),
        audio_confirmation_drawer(),
        rx.box(
            content,
            min_height="85vh",
            width="100%",
        ),
        modern_footer(),
        width="100%",
        min_height="100vh",
        display="flex",
        flex_direction="column",
        background_color="var(--color-background)",
        on_mount=[AuthState.check_auth, CartState.fetch_cart],
    )


cart_drawer = audio_confirmation_drawer
