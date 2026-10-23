from contextlib import contextmanager
from typing import Any, Dict
from nicegui import ui

# ---------------------------------------------------------------------------
# Design System Tokens (Theme & Semantics)
# ---------------------------------------------------------------------------
TOKENS: Dict[str, str] = {
    # Primary Palette
    "primary": "indigo-600",
    "primary_hover": "indigo-700",
    "primary_light": "indigo-50",
    "primary_hex": "#4f46e5",
    "primary_hover_hex": "#4338ca",
    "primary_light_hex": "#eef2ff",
    # Neutral Palette
    "bg_app": "slate-50",
    "bg_subtle": "slate-100",
    "bg_card": "white",
    "border": "slate-200",
    "text_primary": "slate-900",
    "text_secondary": "slate-500",
    "bg_app_hex": "#f8fafc",
    "bg_subtle_hex": "#f1f5f9",
    "bg_card_hex": "#ffffff",
    "border_hex": "#e2e8f0",
    "text_primary_hex": "#0f172a",
    "text_secondary_hex": "#64748b",
    # Semantic SRS SM-2
    "srs_again": "red-500",
    "srs_hard": "amber-500",
    "srs_good": "blue-600",
    "srs_easy": "emerald-600",
    "srs_again_hex": "#ef4444",
    "srs_hard_hex": "#f59e0b",
    "srs_good_hex": "#2563eb",
    "srs_easy_hex": "#059669",
}

# ---------------------------------------------------------------------------
# Toast Notification Configuration
# ---------------------------------------------------------------------------
TOAST_CONFIGS: Dict[str, Dict[str, str]] = {
    "positive": {
        "icon": "check_circle",
        "color": "emerald-600",
        "classes": "rounded-xl shadow-lg border border-emerald-500/30 text-white font-medium px-4 py-3",
    },
    "warning": {
        "icon": "warning_amber",
        "color": "amber-500",
        "classes": "rounded-xl shadow-lg border border-amber-500/30 text-white font-medium px-4 py-3",
    },
    "negative": {
        "icon": "error_outline",
        "color": "rose-600",
        "classes": "rounded-xl shadow-lg border border-rose-500/30 text-white font-medium px-4 py-3",
    },
    "info": {
        "icon": "info",
        "color": "indigo-600",
        "classes": "rounded-xl shadow-lg border border-indigo-500/30 text-white font-medium px-4 py-3",
    },
}

CATEGORY_ALIASES: Dict[str, str] = {
    "success": "positive",
    "easy": "positive",
    "warn": "warning",
    "hard": "warning",
    "error": "negative",
    "danger": "negative",
    "again": "negative",
    "good": "info",
}


def show_toast(message: str, category: str = "info") -> None:
    """Hiển thị toast notification góc trên bên phải (top-right).

    Hỗ trợ 4 loại trạng thái: positive, warning, negative, info.
    Bo góc rounded-xl, đổ bóng shadow-lg, có nút đóng ✕.
    """
    normalized_category = CATEGORY_ALIASES.get(category.lower(), category.lower())
    config = TOAST_CONFIGS.get(normalized_category, TOAST_CONFIGS["info"])

    ui.notify(
        message=message,
        position="top-right",
        icon=config["icon"],
        color=config["color"],
        close_button="✕",
        classes=config["classes"],
    )


# ---------------------------------------------------------------------------
# Base Shell Layout Context Manager
# ---------------------------------------------------------------------------
@contextmanager
def app_shell(active_tab: str = "home", title: str = "EduFlash AI"):
    """Base Shell Layout theo phong cách Clean Minimalist / EdTech UI.

    - Tự động nhúng Google Font Plus Jakarta Sans & Inter
    - Background toàn cục slate-50
    - Sticky Header Bar mờ gương (backdrop-blur) với Brand Logo, Quick Nav, Profile Avatar Menu
    - Body Container max-w-6xl mx-auto px-4 py-8
    """
    ui.page_title(title)

    # Nhúng Google Fonts và Style bổ trợ
    ui.add_head_html("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap" rel="stylesheet">
    <style>
        body {
            font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #f8fafc;
            color: #0f172a;
        }
        .q-notification {
            border-radius: 0.75rem !important;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1) !important;
        }
        .q-notification__actions .q-btn {
            font-size: 0.8rem !important;
            font-weight: 700 !important;
        }
    </style>
    """)

    # Áp dụng nền và typography toàn cục cho thẻ body
    ui.query("body").classes(
        f"bg-{TOKENS['bg_app']} text-{TOKENS['text_primary']} min-h-screen antialiased m-0 p-0"
    )

    # 1. Header Bar (Render từ Navbar Component độc lập)
    from components.navbar import render_navbar

    render_navbar(active_tab=active_tab)

    # 2. Body Container
    with ui.column().classes("w-full max-w-6xl mx-auto px-4 py-8") as container:
        yield container
