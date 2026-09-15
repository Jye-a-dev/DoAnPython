import os
from pathlib import Path
from dotenv import load_dotenv
import reflex as rx

CLIENT_DIR = Path(__file__).resolve().parent
load_dotenv(CLIENT_DIR / ".env")
load_dotenv()

CLIENT_PORT = os.getenv("CLIENT_PORT", "5000")
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:3000")

print(f"\n[+] Client Web UI dang chay tai: http://localhost:{CLIENT_PORT}")
print(f"    🎯 API Server Gateway: {SERVER_URL}\n", flush=True)

try:
    from state import DetectorState
except ImportError:
    from client.state import DetectorState


def navbar() -> rx.Component:
    """Header component displaying brand title, architectural badges, and theme toggle."""
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.icon("scan-eye", size=28, color="var(--accent-9)"),
                rx.vstack(
                    rx.heading("Smart Object Detector", size="5", weight="bold"),
                    rx.text("Reflex Client + FastAPI Server + YOLO Pipeline", size="1", color="gray"),
                    spacing="0",
                ),
                align="center",
                spacing="3",
            ),
            rx.spacer(),
            rx.hstack(
                rx.badge("3-Tier Architecture", color_scheme="green", variant="surface"),
                rx.color_mode.button(),
                spacing="3",
                align="center",
            ),
            width="100%",
            align="center",
            padding_x="1.5rem",
            padding_y="1rem",
        ),
        border_bottom="1px solid var(--gray-4)",
        background_color="var(--color-surface)",
        position="sticky",
        top="0",
        z_index="10",
        width="100%",
    )


def upload_section() -> rx.Component:
    """File upload dropzone conforming to Reflex v0.6+ upload conventions."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("upload-cloud", size=20, color="var(--accent-9)"),
                rx.heading("1. Tải lên hình ảnh", size="4"),
                align="center",
                spacing="2",
            ),
            rx.upload(
                rx.vstack(
                    rx.icon("image-up", size=36, color="var(--gray-9)"),
                    rx.text("Kéo thả ảnh hoặc nhấp để chọn tệp", size="2", weight="medium"),
                    rx.text("Hỗ trợ JPG, PNG, WEBP", size="1", color="gray"),
                    align="center",
                    justify="center",
                    padding="2rem",
                ),
                id="upload_image",
                border="2px dashed var(--gray-6)",
                border_radius="10px",
                width="100%",
                background_color="var(--gray-2)",
                cursor="pointer",
            ),
            rx.hstack(
                rx.foreach(
                    rx.selected_files("upload_image"),
                    lambda file: rx.badge(file, variant="soft", color_scheme="blue")
                ),
                wrap="wrap",
                spacing="2",
            ),
            rx.hstack(
                rx.button(
                    rx.hstack(
                        rx.icon("sparkles", size=18),
                        rx.text("Phân tích & Thuyết minh"),
                        align="center",
                    ),
                    on_click=DetectorState.handle_upload(rx.upload_files(upload_id="upload_image")),
                    loading=DetectorState.is_processing,
                    color_scheme="indigo",
                    size="3",
                    width="100%",
                ),
                rx.button(
                    "Đặt lại",
                    on_click=DetectorState.clear_state,
                    variant="soft",
                    color_scheme="gray",
                    size="3",
                ),
                width="100%",
                spacing="3",
            ),
            spacing="3",
            width="100%",
        ),
        padding="1.25rem",
        width="100%",
    )


def image_preview_section() -> rx.Component:
    """Displays original or bounding-box annotated inference image preview."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("image", size=20, color="var(--accent-9)"),
                rx.heading("2. Khung nhìn hình ảnh", size="4"),
                align="center",
                spacing="2",
            ),
            rx.cond(
                DetectorState.uploaded_image_url != "",
                rx.box(
                    rx.image(
                        src=DetectorState.uploaded_image_url,
                        alt="Annotated detection preview",
                        border_radius="8px",
                        max_height="400px",
                        object_fit="contain",
                        width="100%",
                    ),
                    width="100%",
                    text_align="center",
                ),
                rx.box(
                    rx.vstack(
                        rx.icon("camera-off", size=40, color="var(--gray-8)"),
                        rx.text("Chưa có ảnh nào được phân tích", size="2", color="gray"),
                        align="center",
                        justify="center",
                        height="280px",
                    ),
                    border="1px dashed var(--gray-5)",
                    border_radius="8px",
                    width="100%",
                ),
            ),
            spacing="3",
            width="100%",
        ),
        padding="1.25rem",
        width="100%",
    )


def audio_player_section() -> rx.Component:
    """HTML5 audio element automatically streaming synthesized TTS speech."""
    return rx.cond(
        DetectorState.audio_url != "",
        rx.card(
            rx.vstack(
                rx.hstack(
                    rx.icon("volume-2", size=20, color="var(--accent-9)"),
                    rx.heading("Giọng đọc thuyết minh (TTS)", size="4"),
                    rx.spacer(),
                    rx.badge("Microsoft Neural Voice", color_scheme="blue", variant="soft"),
                    align="center",
                    width="100%",
                ),
                rx.el.audio(
                    src=DetectorState.audio_url,
                    controls=True,
                    auto_play=True,
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            padding="1.25rem",
            width="100%",
            border="1px solid var(--accent-6)",
        ),
    )


def summary_and_json_section() -> rx.Component:
    """Presents Vietnamese text summary callout and formatted JSON schema viewer."""
    return rx.vstack(
        rx.cond(
            DetectorState.summary_text != "",
            rx.callout(
                DetectorState.summary_text,
                icon="message-square",
                color_scheme="green",
                size="3",
                width="100%",
            ),
        ),
        rx.cond(
            DetectorState.json_output != "",
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.icon("file-json", size=20, color="var(--accent-9)"),
                        rx.heading("Chuẩn hóa JSON (Detection Schema)", size="4"),
                        align="center",
                        spacing="2",
                    ),
                    rx.box(
                        rx.code_block(
                            DetectorState.json_output,
                            language="json",
                            can_copy=True,
                        ),
                        max_height="320px",
                        overflow_y="auto",
                        width="100%",
                    ),
                    spacing="3",
                    width="100%",
                ),
                padding="1.25rem",
                width="100%",
            ),
        ),
        spacing="3",
        width="100%",
    )


def history_row(item: dict) -> rx.Component:
    """Individual table row displaying historical detection thumbnail and summary."""
    return rx.table.row(
        rx.table.cell(
            rx.image(
                src=item["image_url"],
                width="48px",
                height="48px",
                object_fit="cover",
                border_radius="4px",
            )
        ),
        rx.table.cell(rx.text(item["created_at"], size="2")),
        rx.table.cell(rx.text(item["summary"], size="2", weight="medium")),
        rx.table.cell(
            rx.button(
                rx.icon("eye", size=16),
                "Xem lại",
                size="1",
                variant="surface",
                on_click=lambda: DetectorState.select_history_item(item),
            )
        ),
    )


def history_section() -> rx.Component:
    """Tabular listing of recent detections loaded from SQLite."""
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.icon("history", size=20, color="var(--accent-9)"),
                rx.heading("Lịch sử nhận diện gần đây", size="4"),
                rx.spacer(),
                rx.button(
                    rx.icon("refresh-cw", size=14),
                    "Làm mới",
                    size="1",
                    variant="ghost",
                    on_click=DetectorState.fetch_history,
                ),
                align="center",
                width="100%",
            ),
            rx.table.root(
                rx.table.header(
                    rx.table.row(
                        rx.table.column_header_cell("Ảnh"),
                        rx.table.column_header_cell("Thời gian"),
                        rx.table.column_header_cell("Tóm tắt kết quả"),
                        rx.table.column_header_cell("Thao tác"),
                    ),
                ),
                rx.table.body(
                    rx.foreach(DetectorState.history, history_row)
                ),
                width="100%",
                variant="surface",
            ),
            spacing="3",
            width="100%",
        ),
        padding="1.25rem",
        width="100%",
    )


def index() -> rx.Component:
    """Root application layout integrating all dashboard cards."""
    return rx.box(
        navbar(),
        rx.container(
            rx.vstack(
                rx.cond(
                    DetectorState.error_message != "",
                    rx.callout(
                        DetectorState.error_message,
                        icon="alert-triangle",
                        color_scheme="red",
                        size="2",
                        width="100%",
                    ),
                ),
                rx.grid(
                    rx.vstack(
                        upload_section(),
                        image_preview_section(),
                        spacing="4",
                        width="100%",
                    ),
                    rx.vstack(
                        audio_player_section(),
                        summary_and_json_section(),
                        spacing="4",
                        width="100%",
                    ),
                    columns=rx.breakpoints(initial="1", md="2"),
                    spacing="4",
                    width="100%",
                ),
                rx.divider(margin_y="1rem"),
                history_section(),
                spacing="4",
                width="100%",
                padding_y="1.5rem",
            ),
            size="3",
        ),
        min_height="100vh",
        background_color="var(--gray-1)",
    )


app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        accent_color="indigo",
    )
)
app.add_page(
    index,
    title="Smart Object Detector | Reflex & FastAPI",
    on_load=DetectorState.fetch_history,
)

