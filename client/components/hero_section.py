from typing import Any, Callable, Optional
from nicegui import ui
from components.layout import TOKENS


def render_hero_section(
    on_start_studio: Optional[Callable[[], Any]] = None,
    on_go_study: Optional[Callable[[], Any]] = None,
) -> ui.column:
    """Khối Hero Section (Phần đầu trang) theo phong cách EdTech Clean Minimalist.

    - Nền dải gradient nhẹ nhàng: from-indigo-50/50 via-white to-slate-50
    - Badge: ✨ Trợ lý học tập thông minh tích hợp AI Offline & Thuật toán SM-2
    - Tiêu đề chính lớn và phụ đề súc tích
    - Cụm nút CTA kép: Bắt đầu tạo bài học & Ôn tập ngay (/study)
    """
    default_scroll = lambda: ui.run_javascript(
        'document.getElementById("workspace-studio").scrollIntoView({behavior: "smooth"})'
    )
    default_study = lambda: ui.navigate.to("/study")

    scroll_action = on_start_studio or default_scroll
    study_action = on_go_study or default_study

    with ui.column().classes(
        "w-full rounded-3xl py-14 md:py-20 px-6 md:px-12 "
        "bg-gradient-to-b from-indigo-50/50 via-white to-slate-50 "
        "border border-slate-200/80 shadow-sm items-center text-center gap-6 relative overflow-hidden"
    ) as hero_col:
        # Badge nổi bật trên cùng
        with ui.row().classes(
            "items-center gap-2 px-4 py-1.5 rounded-full bg-white/90 border border-indigo-200/80 shadow-xs backdrop-blur-xs"
        ):
            ui.label(
                "✨ Trợ lý học tập thông minh tích hợp AI Offline & Thuật toán SM-2"
            ).classes(f"text-xs md:text-sm font-bold text-{TOKENS['primary']}")

        # Tiêu đề chính lớn
        ui.label(
            "Học nhanh hơn, nhớ lâu hơn với Flashcard tự động từ bài giảng."
        ).classes(
            "text-4xl md:text-6xl font-black text-slate-900 leading-tight max-w-4xl tracking-tight"
        )

        # Phụ đề súc tích
        ui.label(
            "Tải lên giáo trình PDF hoặc file ghi âm bài giảng MP3 để AI tự động trích xuất ý chính và tối ưu chu kỳ ôn tập của bạn."
        ).classes(
            "text-base md:text-lg text-slate-600 max-w-2xl font-normal leading-relaxed"
        )

        # Cụm nút CTA
        with ui.row().classes("items-center justify-center gap-4 mt-6"):
            ui.button(
                "BẮT ĐẦU TẠO BÀI HỌC",
                icon="bolt",
                on_click=scroll_action,
            ).classes(
                "bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-6 py-3 rounded-2xl "
                "shadow-lg hover:shadow-indigo-500/25 transition duration-200"
            )

            ui.button(
                "XEM BỘ THẺ (/STUDY)",
                icon="school",
                on_click=study_action,
            ).classes(
                "bg-white hover:bg-slate-100 text-black !text-black font-bold px-6 py-3 rounded-2xl "
                "border border-slate-200 shadow-sm transition duration-200"
            )

    return hero_col
