import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure client directory is prioritized in sys.path
_CLIENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CLIENT_DIR.parent

for _p in [str(_CLIENT_DIR), str(_PROJECT_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

load_dotenv(_CLIENT_DIR / ".env")

from nicegui import ui
from components import TOKENS, app_shell
from pages.home import render_home_page

port = int(os.getenv("PORT", 5000))
host = os.getenv("HOST", "0.0.0.0")


@ui.page("/")
def index():
    """Trang chủ EduFlash AI - Landing Page & Studio tạo bài học."""
    render_home_page()


@ui.page("/study")
def study_page():
    """Kho ôn tập Spaced Repetition (SM-2)."""
    with app_shell(active_tab="study", title="EduFlash AI - Tiến độ SM-2"):
        with ui.column().classes("w-full items-center text-center py-20 gap-4"):
            with ui.element("div").classes(
                f"w-16 h-16 rounded-2xl bg-{TOKENS['primary_light']} text-{TOKENS['primary']} flex items-center justify-center shadow-xs"
            ):
                ui.icon("school", size="36px")
            ui.label("Kho Ôn Tập Spaced Repetition").classes(
                f"text-3xl font-extrabold text-{TOKENS['text_primary']}"
            )
            ui.label(
                "Không gian ôn tập thẻ bài giảng theo chu kỳ ngắt quãng SM-2 tối ưu não bộ."
            ).classes(f"text-base text-{TOKENS['text_secondary']} max-w-md")
            ui.button(
                "Quay lại Studio tạo bài học",
                icon="arrow_back",
                on_click=lambda: ui.navigate.to("/"),
            ).classes(
                f"bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold px-6 py-2.5 rounded-xl shadow-xs mt-2"
            )


@ui.page("/decks")
def decks_page():
    """Thư viện quản lý các bộ thẻ Flashcard."""
    with app_shell(active_tab="decks", title="EduFlash AI - Thư viện bộ thẻ"):
        with ui.column().classes("w-full items-center text-center py-20 gap-4"):
            with ui.element("div").classes(
                f"w-16 h-16 rounded-2xl bg-{TOKENS['primary_light']} text-{TOKENS['primary']} flex items-center justify-center shadow-xs"
            ):
                ui.icon("style", size="36px")
            ui.label("Thư Viện Bộ Thẻ Bài Giảng").classes(
                f"text-3xl font-extrabold text-{TOKENS['text_primary']}"
            )
            ui.label(
                "Quản lý danh sách các bộ thẻ được sinh tự động từ giáo trình và file ghi âm."
            ).classes(f"text-base text-{TOKENS['text_secondary']} max-w-md")
            ui.button(
                "Tạo bài học mới",
                icon="add",
                on_click=lambda: ui.navigate.to("/"),
            ).classes(
                f"bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold px-6 py-2.5 rounded-xl shadow-xs mt-2"
            )


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="EduFlash AI - Smart Repetition",
        host=host,
        port=port,
        reload=True,
        show=False,
        uvicorn_logging_level="info",
        uvicorn_reload_dirs=str(_CLIENT_DIR),
    )
