from nicegui import ui
from components.layout import TOKENS


def render_footer() -> ui.element:
    """Khối Footer thương hiệu và điều hướng hệ thống EduFlash AI."""
    with ui.element("footer").classes(
        f"w-full border-t border-{TOKENS['border']} mt-24 pt-10 pb-14 flex flex-col items-center gap-6 text-center"
    ) as footer_elem:
        with ui.row().classes("items-center gap-2.5"):
            with ui.element("div").classes(
                f"w-9 h-9 rounded-xl bg-gradient-to-tr from-{TOKENS['primary']} to-indigo-500 "
                "flex items-center justify-center text-white shadow-xs"
            ):
                ui.icon("auto_stories", size="20px")
            with ui.column().classes("gap-0 text-left"):
                ui.label("EduFlash AI").classes(
                    f"text-base font-extrabold tracking-tight text-{TOKENS['text_primary']}"
                )
                ui.label("Smart Repetition Platform").classes(
                    f"text-[10px] font-bold text-{TOKENS['text_secondary']} uppercase tracking-wider"
                )

        with ui.row().classes(
            f"items-center justify-center gap-6 flex-wrap text-sm font-semibold text-{TOKENS['text_secondary']}"
        ):
            ui.link("Tạo bài học", target="/").classes(
                f"hover:text-{TOKENS['primary']} transition-colors no-underline"
            )
            ui.link("Thư viện bộ thẻ (/decks)", target="/decks").classes(
                f"hover:text-{TOKENS['primary']} transition-colors no-underline"
            )
            ui.link("Kho ôn tập SM-2 (/study)", target="/study").classes(
                f"hover:text-{TOKENS['primary']} transition-colors no-underline"
            )

        ui.label(
            "© 2026 EduFlash AI. Vận hành bởi mô hình AI Offline & Thuật toán lặp lại ngắt quãng SM-2. Dữ liệu an toàn tuyệt đối."
        ).classes(f"text-xs text-{TOKENS['text_secondary']} font-normal")

    return footer_elem

