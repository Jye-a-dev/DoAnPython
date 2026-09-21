import reflex as rx


def footer() -> rx.Component:
    """Standardized e-commerce footer component containing platform info and navigation links."""
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.icon("scan", size=22, color="var(--accent-9)"),
                        rx.heading("SmartVision Commerce", size="3", weight="bold"),
                        align="center",
                        spacing="2",
                    ),
                    rx.text(
                        "Hệ thống bán lẻ thế hệ mới tích hợp thị giác máy tính YOLOv8, phân tích nhận dạng thời gian thực và tổng hợp giọng nói thuyết minh sản phẩm.",
                        size="1",
                        color="gray",
                        max_width="360px",
                    ),
                    spacing="2",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.vstack(
                        rx.text("Khám Phá", size="2", weight="bold"),
                        rx.link("Trang chủ", href="/", size="1", color="gray"),
                        rx.link("Visual Search AI", href="#", size="1", color="gray"),
                        rx.link("Danh mục sản phẩm", href="#", size="1", color="gray"),
                        spacing="1",
                        align="start",
                    ),
                    rx.vstack(
                        rx.text("Công Nghệ", size="2", weight="bold"),
                        rx.text("FastAPI / RESTx Gateway", size="1", color="gray"),
                        rx.text("YOLO Detection Pipeline", size="1", color="gray"),
                        rx.text("Edge-TTS Audio Stream", size="1", color="gray"),
                        spacing="1",
                        align="start",
                    ),
                    rx.vstack(
                        rx.text("Hỗ Trợ", size="2", weight="bold"),
                        rx.text("Hotline: 1900 6868", size="1", color="gray"),
                        rx.text("Email: support@smartvision.vn", size="1", color="gray"),
                        rx.text("Địa chỉ: TP. Hồ Chí Minh", size="1", color="gray"),
                        spacing="1",
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
                rx.text("© 2026 SmartVision Inc. All rights reserved.", size="1", color="gray"),
                rx.spacer(),
                rx.badge("Reflex Fullstack Python", variant="surface", color_scheme="indigo", size="1"),
                width="100%",
                align="center",
            ),
            width="100%",
            max_width="1200px",
            margin_x="auto",
            padding_x="1.5rem",
            padding_y="2.5rem",
            spacing="4",
        ),
        border_top="1px solid var(--gray-4)",
        background_color="var(--gray-2)",
        width="100%",
        margin_top="auto",
    )

