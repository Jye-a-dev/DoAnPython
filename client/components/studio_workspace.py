import inspect
from typing import Any, Callable, Dict, List, Optional
from nicegui import events, ui

from components.layout import TOKENS, show_toast
from components.dropzone import format_file_size


def render_studio_workspace(
    on_generate_cards: Callable[[List[Dict[str, Any]], str, Callable[[str], None]], Any],
) -> Dict[str, Any]:
    """Khối Studio Workspace Section (Khu vực chuyển đổi tài liệu).

    - Thiết kế Card bo tròn lớn rounded-3xl shadow-xl border border-slate-200/80 bg-white
    - Tiêu đề: 1. Tải tài liệu hoặc dán bài giảng
    - 2 Tabs trực quan: Tệp tài liệu (PDF/TXT) & Âm thanh bài giảng (MP3/WAV/M4A)
    - Quản lý bộ đệm RAM (Zero disk write)
    - Textarea phụ trợ nhập văn bản nhanh
    - Nút kích hoạt: ⚡ Kích hoạt AI sinh Flashcard kèm hiệu ứng bóng đổ và spinner
    """
    in_memory_files: List[Dict[str, Any]] = []

    with ui.element("div").props('id="studio-section"').classes("w-full mt-14 scroll-mt-24"):
        with ui.card().classes(
            "rounded-3xl shadow-xl border border-slate-200/80 bg-white p-6 md:p-10 max-w-4xl mx-auto w-full gap-6"
        ):
            # Tiêu đề phân khu
            with ui.row().classes("items-center justify-between w-full pb-4 border-b border-slate-100"):
                with ui.row().classes("items-center gap-3"):
                    with ui.element("div").classes(
                        f"w-10 h-10 rounded-xl bg-{TOKENS['primary_light']} flex items-center justify-center text-{TOKENS['primary']}"
                    ):
                        ui.icon("auto_fix_high", size="22px")
                    with ui.column().classes("gap-0.5"):
                        ui.label("1. Tải tài liệu hoặc dán bài giảng").classes(
                            f"text-xl font-extrabold text-{TOKENS['text_primary']} tracking-tight"
                        )
                        ui.label("Chọn tải file vào RAM hoặc dán văn bản để AI tạo thẻ học").classes(
                            f"text-xs text-{TOKENS['text_secondary']}"
                        )

                files_badge = ui.label("0 tệp trong RAM").classes(
                    f"text-xs font-semibold px-3 py-1 rounded-full bg-{TOKENS['bg_subtle']} text-{TOKENS['text_secondary']} border border-{TOKENS['border']}"
                )

            # Danh sách hiển thị các tệp đã nạp trong RAM
            file_chips_container = ui.row().classes("w-full flex-wrap gap-2 items-center")

            def refresh_file_chips() -> None:
                file_chips_container.clear()
                count = len(in_memory_files)
                files_badge.text = f"{count} tệp trong RAM"
                if count > 0:
                    files_badge.classes(
                        add="bg-emerald-50 text-emerald-700 border-emerald-200 font-bold",
                        remove=f"bg-{TOKENS['bg_subtle']} text-{TOKENS['text_secondary']}",
                    )
                    with file_chips_container:
                        for idx, f in enumerate(in_memory_files):
                            with ui.row().classes(
                                "items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-50 border border-slate-200 text-xs font-medium"
                            ):
                                icon = "description" if f["category"] == "document" else "graphic_eq"
                                color = f"text-{TOKENS['primary']}" if f["category"] == "document" else "text-purple-600"
                                ui.icon(icon, size="16px").classes(color)
                                ui.label(f"{f['name']} ({f['size_formatted']})").classes("text-slate-700")

                                def make_remove_cb(target_idx: int):
                                    def remove_file():
                                        in_memory_files.pop(target_idx)
                                        refresh_file_chips()
                                        show_toast("Đã gỡ tệp khỏi bộ đệm RAM", "info")
                                    return remove_file

                                ui.button(icon="close", on_click=make_remove_cb(idx)).props("flat dense round").classes(
                                    "text-slate-400 hover:text-rose-500 text-xs"
                                )
                else:
                    files_badge.classes(
                        add=f"bg-{TOKENS['bg_subtle']} text-{TOKENS['text_secondary']}",
                        remove="bg-emerald-50 text-emerald-700 border-emerald-200 font-bold",
                    )

            async def handle_binary_upload(e: events.UploadEventArguments, category: str) -> None:
                """Nạp nhị phân trực tiếp vào bộ đệm RAM không ghi đĩa trung gian."""
                try:
                    filename = getattr(e, "name", "file")
                    content_reader = e.content.read() if hasattr(e, "content") else b""
                    bytes_data = (
                        await content_reader if inspect.isawaitable(content_reader) else content_reader
                    )
                    if not bytes_data:
                        show_toast("Tệp rỗng hoặc không đọc được nội dung", "warning")
                        return

                    size = len(bytes_data)
                    in_memory_files.append({
                        "name": filename,
                        "bytes": bytes_data,
                        "size": size,
                        "size_formatted": format_file_size(size),
                        "category": category,
                    })
                    refresh_file_chips()
                    show_toast(f"Đã nạp '{filename}' ({format_file_size(size)}) vào RAM", "positive")
                except Exception as err:
                    show_toast(f"Lỗi khi nạp file vào RAM: {str(err)}", "negative")

            # 2 Tabs chuyển đổi trực quan
            with ui.tabs().classes(
                f"w-full border-b border-{TOKENS['border']} text-{TOKENS['text_secondary']}"
            ) as studio_tabs:
                tab_doc = ui.tab("doc", label="Tệp tài liệu (PDF / TXT)", icon="description").classes(
                    f"font-semibold text-sm hover:text-{TOKENS['primary']}"
                )
                tab_audio = ui.tab("audio", label="Âm thanh bài giảng (MP3 / WAV / M4A)", icon="graphic_eq").classes(
                    "font-semibold text-sm hover:text-purple-600"
                )

            with ui.tab_panels(studio_tabs, value=tab_doc).classes("w-full bg-transparent p-0 mt-3"):
                # Tab 1: Tài liệu học tập (.pdf, .txt, .md)
                with ui.tab_panel(tab_doc).classes("p-0"):
                    with ui.column().classes(
                        "w-full border-2 border-dashed border-slate-300 hover:border-indigo-500 rounded-2xl "
                        "bg-slate-50/70 p-6 items-center justify-center text-center transition-all duration-200 gap-2"
                    ):
                        ui.icon("upload_file", size="38px").classes(f"text-{TOKENS['primary']}")
                        ui.label("Kéo thả tài liệu giáo trình hoặc bấm để chọn tệp").classes(
                            f"text-sm font-bold text-{TOKENS['text_primary']}"
                        )
                        ui.label("Hỗ trợ định dạng .pdf, .txt, .md (Tối đa 15MB, nạp trực tiếp vào RAM)").classes(
                            f"text-xs text-{TOKENS['text_secondary']} mb-2"
                        )
                        ui.upload(
                            auto_upload=True,
                            max_file_size=15_000_000,
                            on_upload=lambda e: handle_binary_upload(e, "document"),
                            on_rejected=lambda: show_toast("Tệp tài liệu vượt quá dung lượng 15MB", "warning"),
                        ).props('accept=".pdf,.txt,.md" flat bordered color="indigo"').classes(
                            "w-full max-w-md bg-white rounded-xl shadow-2xs"
                        )

                # Tab 2: Âm thanh bài giảng (.mp3, .wav, .m4a)
                with ui.tab_panel(tab_audio).classes("p-0"):
                    with ui.column().classes(
                        "w-full border-2 border-dashed border-slate-300 hover:border-purple-500 rounded-2xl "
                        "bg-slate-50/70 p-6 items-center justify-center text-center transition-all duration-200 gap-2"
                    ):
                        ui.icon("graphic_eq", size="38px").classes("text-purple-600")
                        ui.label("Kéo thả bản ghi âm bài giảng hoặc bấm để chọn tệp").classes(
                            f"text-sm font-bold text-{TOKENS['text_primary']}"
                        )
                        ui.label("Hỗ trợ định dạng .mp3, .wav, .m4a (Bóc băng tự động bằng Whisper)").classes(
                            f"text-xs text-{TOKENS['text_secondary']} mb-2"
                        )
                        ui.upload(
                            auto_upload=True,
                            max_file_size=25_000_000,
                            on_upload=lambda e: handle_binary_upload(e, "audio"),
                            on_rejected=lambda: show_toast("Tệp âm thanh vượt quá 25MB", "warning"),
                        ).props('accept=".mp3,.wav,.m4a" flat bordered color="purple"').classes(
                            "w-full max-w-md bg-white rounded-xl shadow-2xs"
                        )

            # Textarea nhập văn bản nhanh
            with ui.column().classes("w-full gap-1.5 mt-2"):
                ui.label("Hoặc dán nhanh nội dung bài học nếu không có sẵn tệp:").classes(
                    f"text-xs font-bold text-{TOKENS['text_primary']} uppercase tracking-wider"
                )
                text_input = ui.textarea(
                    placeholder="Dán tóm tắt lý thuyết, nội dung ghi chú bài giảng hoặc các định nghĩa cần tạo câu hỏi ôn tập tại đây..."
                ).classes(
                    "w-full border border-slate-200 rounded-2xl p-4 bg-slate-50/60 focus:bg-white text-sm text-slate-800 transition-all"
                ).props('rows="4" autogrow')

            # Thanh trạng thái tiến trình
            progress_container = ui.row().classes("w-full items-center justify-center gap-3 py-2")
            progress_container.set_visibility(False)
            with progress_container:
                ui.spinner(size="md", color="indigo")
                progress_status = ui.label("AI đang xử lý...").classes(
                    f"text-sm font-semibold text-{TOKENS['primary']}"
                )

            # Nút kích hoạt hành động lớn
            generate_btn = ui.button("⚡ Kích hoạt AI sinh Flashcard").classes(
                f"w-full py-4 text-base font-extrabold text-white rounded-2xl bg-{TOKENS['primary']} "
                f"hover:bg-{TOKENS['primary_hover']} shadow-lg shadow-indigo-600/30 hover:shadow-indigo-600/50 "
                "hover:-translate-y-0.5 active:translate-y-0 transition-all duration-200 cursor-pointer"
            )

            def set_status_text(msg: str) -> None:
                progress_status.text = msg

            async def handle_generate_click() -> None:
                text_val = text_input.value.strip()
                if not in_memory_files and not text_val:
                    show_toast("Vui lòng tải lên tệp tài liệu/ghi âm hoặc dán nội dung bài học", "warning")
                    return

                generate_btn.props("loading")
                progress_container.set_visibility(True)
                try:
                    res = on_generate_cards(in_memory_files, text_val, set_status_text)
                    if inspect.isawaitable(res):
                        await res
                finally:
                    generate_btn.props(remove="loading")
                    progress_container.set_visibility(False)

            generate_btn.on_click(handle_generate_click)

    return {
        "get_files": lambda: list(in_memory_files),
        "clear_files": lambda: (in_memory_files.clear(), refresh_file_chips()),
    }

