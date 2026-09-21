import reflex as rx
from state.detect_state import DetectState


def hero_section() -> rx.Component:
    """Hero banner section displaying application value proposition and visual search CTA."""
    return rx.box(
        rx.vstack(
            rx.badge("AI-Powered Visual Search & Audio Assistant", color_scheme="indigo", variant="surface", size="2"),
            rx.heading(
                "Mua Sắm Thông Minh Cùng Thị Giác Máy Tính AI",
                size="8",
                weight="bold",
                text_align="center",
                max_width="720px",
            ),
            rx.text(
                "Chụp hoặc tải lên hình ảnh đồ vật. Pipeline YOLOv8 phân tích nhãn, giọng đọc AI thuyết minh trực tiếp và tự động ghép nối sản phẩm trong giỏ hàng.",
                size="3",
                color="gray",
                text_align="center",
                max_width="600px",
            ),
            rx.hstack(
                rx.button(
                    rx.hstack(
                        rx.icon("camera", size=18),
                        rx.text("Quét Camera / Tải Ảnh"),
                        align="center",
                        spacing="2",
                    ),
                    on_click=DetectState.open_modal,
                    size="3",
                    color_scheme="indigo",
                ),
                rx.link(
                    rx.button(
                        rx.hstack(
                            rx.icon("shopping-bag", size=18),
                            rx.text("Khám Phá Cửa Hàng"),
                            align="center",
                            spacing="2",
                        ),
                        size="3",
                        variant="soft",
                        color_scheme="gray",
                    ),
                    href="#catalog-section",
                    underline="none",
                ),
                spacing="3",
                padding_top="1rem",
            ),
            align="center",
            spacing="4",
            padding_y="3.5rem",
            padding_x="1rem",
        ),
        background="radial-gradient(ellipse 80% 50% at 50% -20%, var(--accent-3), transparent)",
        width="100%",
    )

