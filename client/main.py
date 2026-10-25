from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Ưu tiên thư mục client và thư mục gốc trong sys.path
_CLIENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CLIENT_DIR.parent

for _p in [str(_CLIENT_DIR), str(_PROJECT_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

load_dotenv(_CLIENT_DIR / ".env")

from nicegui import ui

from pages.home import render_home_page
from pages.study import render_study_page
from pages.decks import render_decks_page
from pages.login import render_login_page
from pages.register import render_register_page
from pages.profile import render_profile_page
from services.auth_guard import require_auth, redirect_if_authenticated

port = int(os.getenv("PORT", 5000))
host = os.getenv("HOST", "0.0.0.0")


# ===========================================================================
# SPA ROUTER: ĐĂNG KÝ TOÀN BỘ CÁC ROUTES CHUẨN CỦA ỨNG DỤNG
# ===========================================================================
@ui.page("/")
def home_route() -> None:
    """Route công khai: Studio tạo bài học SPA kết hợp Hero và AI Card Generator."""
    render_home_page()


@ui.page("/login")
def login_route() -> None:
    """Route công khai: Màn hình Đăng nhập (Guard: Chuyển hướng sang /decks nếu đã xác thực)."""
    if redirect_if_authenticated("/decks"):
        return
    render_login_page()


@ui.page("/register")
def register_route() -> None:
    """Route công khai: Màn hình Đăng ký tài khoản (Guard: Chuyển hướng nếu đã xác thực)."""
    if redirect_if_authenticated("/decks"):
        return
    render_register_page()


@ui.page("/decks")
async def decks_route() -> None:
    """Route bảo vệ (Protected): Quản lý các bộ thẻ Flashcard (Decks), thống kê và thẻ đến hạn."""
    if not require_auth():
        return
    await render_decks_page()


@ui.page("/study")
async def study_route(deck_id: Optional[int] = None) -> None:
    """Route bảo vệ (Protected): Lặp lại ngắt quãng SM-2 Focus Mode kèm Hotkeys 1-4 & Space."""
    if not require_auth():
        return
    await render_study_page(deck_id=deck_id)


@ui.page("/profile")
async def profile_route() -> None:
    """Route bảo vệ (Protected): Hồ sơ cá nhân, KPI ghi nhớ SM-2 và cài đặt mục tiêu học tập."""
    if not require_auth():
        return
    await render_profile_page()


# Bí danh tương thích ngược cho test runner & import alias
index = home_route
render_study = study_route
render_decks = decks_route
render_login = login_route
render_register = register_route
render_profile = profile_route


# ===========================================================================
# KHỞI CHẠY ỨNG DỤNG NICEGUI
# ===========================================================================
if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="EduFlash AI - Smart Repetition",
        host=host,
        port=port,
        reload=True,
        show=False,
        uvicorn_logging_level="info",
        uvicorn_reload_dirs=str(_CLIENT_DIR),
        storage_secret=os.getenv("STORAGE_SECRET", "eduflash_secret_key_2026"),
    )
