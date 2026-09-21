import reflex as rx
from components.product_card import product_card
from state.detect_state import DetectState
from state.product_state import ProductState


def scan_skeleton_view() -> rx.Component:
    """Khung skeleton loading hiển thị trong quá trình pipeline YOLO & Edge-TTS phân tích."""
    return rx.vstack(
        rx.hstack(
            rx.spinner(size="2", color="var(--accent-9)"),
            rx.text("AI Pipeline đang nhận dạng nhãn vật thể & tổng hợp giọng nói...", size="2", weight="medium"),
            align="center",
            spacing="2",
            padding="0.75rem",
            background_color="var(--accent-2)",
            border_radius="8px",
            width="100%",
        ),
        rx.hstack(
            rx.skeleton(height="260px", border_radius="12px", width="50%"),
            rx.vstack(
                rx.skeleton(height="36px", border_radius="8px", width="100%"),
                rx.skeleton(height="60px", border_radius="8px", width="100%"),
                rx.skeleton(height="40px", border_radius="8px", width="80%"),
                rx.skeleton(height="50px", border_radius="8px", width="100%"),
                width="50%",
                spacing="3",
            ),
            width="100%",
            spacing="4",
        ),
        width="100%",
        spacing="3",
        padding_y="1rem",
    )


def scan_modal() -> rx.Component:
    """Hộp thoại Camera / Upload Visual AI Search với phân tích Bounding Box và Audio Streaming."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # Header hộp thoại
                rx.hstack(
                    rx.hstack(
                        rx.box(
                            rx.icon("scan-face", size=22, color="white"),
                            background="linear-gradient(135deg, #6366f1, #8b5cf6)",
                            padding="6px",
                            border_radius="8px",
                        ),
                        rx.vstack(
                            rx.heading("Trợ Lý Thị Giác AI (Visual Search)", size="4", weight="bold"),
                            rx.text("Tải ảnh hoặc chụp camera để nhận diện tức thì và đối chiếu sản phẩm", size="1", color="gray"),
                            spacing="0",
                        ),
                        align="center",
                        spacing="3",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.button(
                            rx.icon("x", size=18),
                            variant="ghost",
                            color_scheme="gray",
                            on_click=DetectState.close_modal,
                        ),
                    ),
                    width="100%",
                    align="center",
                ),
                rx.separator(width="100%"),

                # Vùng Drag & Drop Upload
                rx.vstack(
                    rx.upload(
                        rx.vstack(
                            rx.icon("camera", size=38, color="var(--accent-9)"),
                            rx.text("Kéo thả ảnh hoặc nhấp để bật Camera / Chọn tệp", size="2", weight="bold"),
                            rx.text("Hỗ trợ định dạng JPG, PNG, WEBP (Tối đa 15MB)", size="1", color="gray"),
                            align="center",
                            justify="center",
                            padding="2rem",
                        ),
                        id="scan_modal_upload",
                        border="2px dashed var(--gray-6)",
                        border_radius="12px",
                        width="100%",
                        background_color="var(--gray-2)",
                        cursor="pointer",
                        _hover={"border_color": "var(--accent-9)", "background_color": "var(--accent-2)"},
                    ),
                    rx.hstack(
                        rx.foreach(
                            rx.selected_files("scan_modal_upload"),
                            lambda f: rx.badge(f, color_scheme="indigo", variant="soft", radius="full"),
                        ),
                        wrap="wrap",
                        spacing="2",
                    ),
                    rx.hstack(
                        rx.button(
                            rx.hstack(
                                rx.icon("sparkles", size=18),
                                rx.text("Phân Tích Bằng AI", size="2", weight="bold"),
                                align="center",
                                spacing="2",
                            ),
                            on_click=DetectState.upload_and_detect(rx.upload_files(upload_id="scan_modal_upload")),
                            loading=DetectState.is_scanning,
                            color_scheme="indigo",
                            size="3",
                            radius="large",
                        ),
                        rx.cond(
                            DetectState.annotated_image_url != "",
                            rx.button(
                                "Quét ảnh mới",
                                variant="outline",
                                color_scheme="gray",
                                on_click=DetectState.clear_scan,
                                size="3",
                                radius="large",
                            ),
                        ),
                        spacing="3",
                    ),
                    width="100%",
                    spacing="3",
                ),

                # Hiển thị thông báo lỗi nếu có
                rx.cond(
                    DetectState.error_message != "",
                    rx.callout(
                        DetectState.error_message,
                        icon="circle-alert",
                        color_scheme="ruby",
                        size="1",
                        width="100%",
                    ),
                ),

                # Loading Skeleton khi đang chạy mô hình
                rx.cond(DetectState.is_scanning, scan_skeleton_view()),

                # Khung kết quả sau khi nhận diện thành công
                rx.cond(
                    (DetectState.annotated_image_url != "") & ~DetectState.is_scanning,
                    rx.vstack(
                        rx.separator(width="100%"),
                        rx.heading("Kết Quả Phân Tích & Thuyết Minh AI", size="3", weight="bold"),
                        rx.hstack(
                            # Cột trái: Ảnh Bounding Box streaming từ /api/v1/media/records/{id}/image
                            rx.box(
                                rx.image(
                                    src=DetectState.annotated_image_url,
                                    alt="YOLO Detection Bounding Boxes",
                                    max_height="280px",
                                    width="100%",
                                    object_fit="contain",
                                    border_radius="10px",
                                    border="1px solid var(--gray-4)",
                                    background_color="var(--gray-1)",
                                ),
                                flex="1",
                            ),

                            # Cột phải: Thuyết minh văn bản + Audio Player HTML5
                            rx.vstack(
                                rx.cond(
                                    DetectState.audio_url != "",
                                    rx.vstack(
                                        rx.hstack(
                                            rx.icon("volume-2", size=18, color="var(--accent-9)"),
                                            rx.text("Giọng đọc thuyết minh tự nhiên (Edge-TTS):", size="2", weight="bold"),
                                            align="center",
                                        ),
                                        rx.el.audio(
                                            src=DetectState.audio_url,
                                            controls=True,
                                            auto_play=True,
                                            style={"width": "100%", "height": "42px"},
                                        ),
                                        width="100%",
                                        spacing="2",
                                    ),
                                ),
                                rx.box(
                                    rx.text(
                                        DetectState.summary_text,
                                        size="2",
                                        color="var(--gray-11)",
                                        line_height="1.5",
                                    ),
                                    background_color="var(--gray-2)",
                                    padding="0.85rem",
                                    border_radius="8px",
                                    border="1px solid var(--gray-4)",
                                    width="100%",
                                ),
                                rx.hstack(
                                    rx.text("Nhãn tìm thấy:", size="1", color="gray", weight="medium"),
                                    rx.foreach(
                                        DetectState.detected_objects,
                                        lambda obj: rx.badge(
                                            obj.get("name", ""),
                                            color_scheme="violet",
                                            variant="surface",
                                            radius="full",
                                        ),
                                    ),
                                    wrap="wrap",
                                    spacing="2",
                                    align="center",
                                ),
                                flex="1",
                                spacing="3",
                            ),
                            width="100%",
                            spacing="4",
                            wrap="wrap",
                        ),

                        # Khu vực dưới: Danh sách sản phẩm khớp với nhãn AI
                        rx.separator(width="100%"),
                        rx.hstack(
                            rx.icon("sparkles", size=18, color="var(--accent-9)"),
                            rx.heading("Sản Phẩm Trong Kho Khớp Với Ảnh Quét", size="3", weight="bold"),
                            align="center",
                            spacing="2",
                        ),
                        rx.cond(
                            ProductState.matched_products.length() > 0,
                            rx.hstack(
                                rx.foreach(
                                    ProductState.matched_products,
                                    lambda p: product_card(p, DetectState.last_record_id),
                                ),
                                wrap="wrap",
                                spacing="3",
                                width="100%",
                            ),
                            rx.center(
                                rx.text("Chưa tìm thấy sản phẩm trùng khớp trong danh mục cửa hàng.", size="2", color="gray"),
                                width="100%",
                                padding="1rem",
                            ),
                        ),
                        width="100%",
                        spacing="3",
                    ),
                ),
                width="100%",
                spacing="4",
            ),
            max_width="780px",
            width="92vw",
            max_height="88vh",
            overflow_y="auto",
            border_radius="16px",
            padding="1.75rem",
        ),
        open=DetectState.is_modal_open,
        on_open_change=DetectState.close_modal,
    )
