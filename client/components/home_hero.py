from __future__ import annotations

from nicegui import ui

from components.layout import TOKENS


def render_home_hero() -> None:
    """Render Hero section with quick value prop badges and CTA navigation buttons."""
    with ui.column().classes(
        "w-full rounded-3xl py-12 md:py-16 px-6 md:px-12 "
        "bg-gradient-to-b from-indigo-50/60 via-white to-slate-50 "
        "border border-slate-200/80 shadow-sm items-center text-center gap-6 relative overflow-hidden"
    ):
        with ui.row().classes(
            "items-center gap-2 px-4 py-1.5 rounded-full bg-white/90 border border-indigo-200/80 shadow-xs backdrop-blur-xs"
        ):
            ui.label(
                "✨ Trợ lý học tập thông minh tích hợp AI Offline & Thuật toán SM-2"
            ).classes(f"text-xs md:text-sm font-bold text-{TOKENS['primary']}")

        ui.label("Tạo Flashcard Tự Động Từ Bài Giảng Chỉ Trong Vài Giây").classes(
            "text-3xl md:text-5xl font-black text-slate-900 leading-tight max-w-4xl tracking-tight"
        )

        ui.label(
            "Nạp trực tiếp giáo trình PDF hoặc file ghi âm bài giảng MP3 để AI phân tích trọng tâm, "
            "sinh câu hỏi thông minh và tối ưu hóa chu kỳ ôn tập dài hạn."
        ).classes(
            "text-sm md:text-base text-slate-600 max-w-2xl font-normal leading-relaxed"
        )

        with ui.row().classes("items-center justify-center gap-4 mt-2 flex-wrap"):
            ui.button(
                "⚡ VÀO STUDIO TẠO THẺ",
                icon="bolt",
                on_click=lambda: ui.run_javascript(
                    'document.getElementById("workspace-studio").scrollIntoView({behavior: "smooth"})'
                ),
            ).classes(
                f"bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold px-6 py-3 rounded-2xl "
                "shadow-lg hover:shadow-indigo-500/25 transition duration-200 cursor-pointer"
            )

            ui.button(
                "ÔN TẬP SM-2",
                icon="school",
                on_click=lambda: ui.navigate.to("/study"),
            ).props('text-color="black"').classes(
                "bg-white hover:bg-slate-100 !text-black text-black font-bold px-6 py-3 rounded-2xl "
                "border border-slate-200 shadow-sm transition duration-200 cursor-pointer"
            )

            ui.button(
                "THƯ VIỆN DECK",
                icon="folder_special",
                on_click=lambda: ui.navigate.to("/decks"),
            ).props('text-color="black"').classes(
                "bg-white hover:bg-slate-100 !text-black text-black font-bold px-6 py-3 rounded-2xl "
                "border border-slate-200 shadow-sm transition duration-200 cursor-pointer"
            )

