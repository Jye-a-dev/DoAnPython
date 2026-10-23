from nicegui import ui
from components.layout import TOKENS


def render_features_grid() -> ui.element:
    """Khối Features & Benefits Grid (Lợi ích cốt lõi).

    Lưới 3 cột chuẩn Tailwind UI:
    - Cột 1: AI Trích xuất cốt lõi (Mô hình Flan-T5 tóm tắt và lọc câu hỏi đắt giá).
    - Cột 2: Bóc băng bài giảng (OpenAI Whisper nhận dạng âm thanh chính xác).
    - Cột 3: Khoa học ghi nhớ SM-2 (Thuật toán lặp lại ngắt quãng tối ưu não bộ).
    """
    with ui.element("div").classes("w-full max-w-6xl mx-auto mt-24") as grid_wrapper:
        with ui.column().classes("text-center items-center gap-2 mb-12"):
            ui.label("CÔNG NGHỆ ĐỘT PHÁ").classes(
                f"text-xs font-bold uppercase tracking-wider text-{TOKENS['primary']}"
            )
            ui.label("Kiến trúc Học tập Thông minh Tối ưu Não bộ").classes(
                f"text-2xl md:text-3xl font-extrabold text-{TOKENS['text_primary']} tracking-tight"
            )
            ui.label(
                "Sự kết hợp giữa mô hình ngôn ngữ lớn xử lý cục bộ và thuật toán ghi nhớ ngắt quãng chuẩn khoa học."
            ).classes(f"text-sm text-{TOKENS['text_secondary']} max-w-xl")

        with ui.element("div").classes("grid grid-cols-1 md:grid-cols-3 gap-6 mt-6"):
            # Cột 1: Flan-T5
            with ui.card().classes(
                f"bg-{TOKENS['bg_card']} border border-{TOKENS['border']} rounded-2xl p-6 shadow-sm "
                "hover:shadow-md hover:border-indigo-200 transition-all duration-200 gap-4"
            ):
                with ui.row().classes("items-center justify-between w-full"):
                    with ui.element("div").classes(
                        f"w-12 h-12 rounded-xl bg-{TOKENS['primary_light']} text-{TOKENS['primary']} flex items-center justify-center"
                    ):
                        ui.icon("psychology", size="26px")
                    ui.label("Flan-T5 Core").classes(
                        f"text-xs font-bold text-{TOKENS['primary']} bg-{TOKENS['primary_light']} border border-indigo-200/60 px-2.5 py-1 rounded-full"
                    )
                ui.label("AI Trích xuất cốt lõi").classes(
                    f"text-lg font-bold text-{TOKENS['text_primary']}"
                )
                ui.label(
                    "Mô hình Flan-T5 tóm tắt và lọc câu hỏi đắt giá từ tài liệu giáo trình, tự động loại bỏ thông tin thừa và cô đọng kiến thức trọng tâm."
                ).classes(f"text-sm text-{TOKENS['text_secondary']} leading-relaxed")

            # Cột 2: Whisper
            with ui.card().classes(
                f"bg-{TOKENS['bg_card']} border border-{TOKENS['border']} rounded-2xl p-6 shadow-sm "
                "hover:shadow-md hover:border-purple-200 transition-all duration-200 gap-4"
            ):
                with ui.row().classes("items-center justify-between w-full"):
                    with ui.element("div").classes(
                        "w-12 h-12 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center"
                    ):
                        ui.icon("graphic_eq", size="26px")
                    ui.label("Whisper STT").classes(
                        "text-xs font-bold text-purple-600 bg-purple-50 border border-purple-200/60 px-2.5 py-1 rounded-full"
                    )
                ui.label("Bóc băng bài giảng").classes(
                    f"text-lg font-bold text-{TOKENS['text_primary']}"
                )
                ui.label(
                    "Whisper chuyển giọng nói từ bản ghi âm bài giảng MP3, WAV thành văn bản chính xác với dấu câu tự nhiên, hỗ trợ tiếng Việt mượt mà."
                ).classes(f"text-sm text-{TOKENS['text_secondary']} leading-relaxed")

            # Cột 3: SM-2 Spaced Repetition
            with ui.card().classes(
                f"bg-{TOKENS['bg_card']} border border-{TOKENS['border']} rounded-2xl p-6 shadow-sm "
                "hover:shadow-md hover:border-emerald-200 transition-all duration-200 gap-4"
            ):
                with ui.row().classes("items-center justify-between w-full"):
                    with ui.element("div").classes(
                        "w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center"
                    ):
                        ui.icon("history_edu", size="26px")
                    ui.label("SuperMemo-2").classes(
                        "text-xs font-bold text-emerald-600 bg-emerald-50 border border-emerald-200/60 px-2.5 py-1 rounded-full"
                    )
                ui.label("Khoa học ghi nhớ SM-2").classes(
                    f"text-lg font-bold text-{TOKENS['text_primary']}"
                )
                ui.label(
                    "Tự động tính toán ngày ôn tập ngắt quãng tối ưu não bộ theo đường cong quên lãng Ebbinghaus, tăng hiệu suất ghi nhớ vĩnh viễn với số lần lặp ít nhất."
                ).classes(f"text-sm text-{TOKENS['text_secondary']} leading-relaxed")

    return grid_wrapper

