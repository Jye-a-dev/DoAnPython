import inspect
import mimetypes
from typing import Any, Callable, Dict, List, Optional
from nicegui import ui
from components.layout import TOKENS, show_toast


def format_file_size(size_bytes: int) -> str:
    """Format dung lượng bytes thành định dạng chuẩn (B, KB, MB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


def render_dropzone(
    on_upload_callback: Optional[Callable[[str, bytes, str], Any]] = None,
) -> Dict[str, Any]:
    """Component Drag & Drop Upload tài liệu và âm thanh trực tiếp vào RAM (In-Memory BLOB).

    - Giao diện 2 Tabs: Tài liệu học tập (.pdf, .txt, .md) & Âm thanh bài giảng (.mp3, .wav, .m4a).
    - ui.upload: auto_upload=True, max_file_size=10_000_000 (10MB).
    - Đọc nội dung qua e.content.read() / e.file.read() vào RAM, tuyệt đối không lưu file tạm ra đĩa cục bộ.
    - Hiển thị danh sách file trực quan kèm định dạng, dung lượng KB/MB và trạng thái RAM.
    """
    in_memory_files: List[Dict[str, Any]] = []

    with ui.card().classes(
        f"w-full bg-{TOKENS['bg_card']} border border-{TOKENS['border']} rounded-2xl p-6 shadow-sm gap-5"
    ):
        # Header Tiêu đề
        with ui.row().classes("items-center justify-between w-full"):
            with ui.row().classes("items-center gap-2.5"):
                with ui.element("div").classes(
                    f"w-8 h-8 rounded-lg bg-{TOKENS['primary_light']} flex items-center justify-center text-{TOKENS['primary']}"
                ):
                    ui.icon("cloud_upload", size="20px")
                with ui.column().classes("gap-0"):
                    ui.label("Tải Lên Bộ Nhớ Tạm (In-Memory Upload)").classes(
                        f"text-base font-bold text-{TOKENS['text_primary']}"
                    )
                    ui.label(
                        "Đọc nhị phân trực tiếp vào RAM, không lưu file tạm ra đĩa"
                    ).classes(f"text-xs text-{TOKENS['text_secondary']}")

            buffer_count_badge = ui.label("0 file trong RAM").classes(
                f"text-xs font-semibold px-2.5 py-1 rounded-full bg-{TOKENS['bg_subtle']} text-{TOKENS['text_secondary']} border border-{TOKENS['border']}"
            )

        # Giao diện 2 Tabs sử dụng ui.tabs
        with ui.tabs().classes(
            f"w-full border-b border-{TOKENS['border']} text-{TOKENS['text_secondary']}"
        ) as tabs:
            tab_docs = ui.tab(
                "docs", label="Tài liệu học tập", icon="description"
            ).classes(f"hover:text-{TOKENS['primary']} font-medium text-sm")
            tab_audio = ui.tab(
                "audio", label="Âm thanh bài giảng", icon="graphic_eq"
            ).classes(f"hover:text-{TOKENS['primary']} font-medium text-sm")

        file_list_container = ui.column().classes("w-full gap-2 mt-2")

        def update_file_list_ui():
            """Cập nhật giao diện danh sách file đang nạp trong RAM."""
            file_list_container.clear()
            count = len(in_memory_files)
            buffer_count_badge.text = f"{count} file trong RAM"
            if count > 0:
                buffer_count_badge.classes(
                    add="bg-emerald-50 text-emerald-700 border-emerald-200 font-bold",
                    remove=f"bg-{TOKENS['bg_subtle']} text-{TOKENS['text_secondary']}",
                )
            else:
                buffer_count_badge.classes(
                    add=f"bg-{TOKENS['bg_subtle']} text-{TOKENS['text_secondary']}",
                    remove="bg-emerald-50 text-emerald-700 border-emerald-200 font-bold",
                )

            if not in_memory_files:
                return

            with file_list_container:
                with ui.row().classes(
                    "items-center justify-between w-full pt-2 pb-1 border-t border-slate-100"
                ):
                    ui.label("Danh sách tệp trong RAM Buffer:").classes(
                        f"text-xs font-bold uppercase tracking-wider text-{TOKENS['text_secondary']}"
                    )
                    ui.button("Xóa sạch RAM", on_click=clear_all_files).props(
                        "flat dense"
                    ).classes("text-xs text-rose-500 hover:text-rose-700 font-semibold")

                for idx, item in enumerate(in_memory_files):
                    with ui.row().classes(
                        "w-full items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200/80 hover:bg-indigo-50/40 transition-colors"
                    ):
                        with ui.row().classes("items-center gap-3 min-w-0"):
                            icon_name = (
                                "description"
                                if item["category"] == "document"
                                else "audiotrack"
                            )
                            icon_color = (
                                "text-indigo-600"
                                if item["category"] == "document"
                                else "text-purple-600"
                            )
                            ui.icon(icon_name, size="20px").classes(icon_color)

                            with ui.column().classes("gap-0 min-w-0"):
                                ui.label(item["name"]).classes(
                                    f"text-sm font-semibold text-{TOKENS['text_primary']} truncate max-w-xs md:max-w-md"
                                )
                                ui.label(item["type"]).classes(
                                    "text-[11px] text-slate-400 font-mono"
                                )

                        with ui.row().classes("items-center gap-2"):
                            # Badge định dạng và dung lượng (KB/MB)
                            ui.label(item["size_formatted"]).classes(
                                "text-xs font-mono font-bold px-2 py-0.5 rounded bg-white text-slate-700 border border-slate-200 shadow-2xs"
                            )
                            # Badge trạng thái In-Memory
                            ui.label("In-Memory BLOB").classes(
                                "text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/60"
                            )
                            ui.button(
                                icon="close",
                                on_click=lambda i=idx: remove_file(i),
                            ).props("flat round dense size=sm").classes(
                                "text-slate-400 hover:text-rose-500"
                            )

        def clear_all_files():
            in_memory_files.clear()
            update_file_list_ui()
            show_toast("Đã giải phóng bộ đệm RAM", "info")

        def remove_file(index: int):
            if 0 <= index < len(in_memory_files):
                removed = in_memory_files.pop(index)
                update_file_list_ui()
                show_toast(f"Đã giải phóng {removed['name']} khỏi RAM", "info")

        async def handle_binary_upload(e: Any, category: str):
            """Đọc binary trực tiếp vào RAM, không lưu file ra đĩa cục bộ."""
            filename = "file"
            file_type = "application/octet-stream"
            bytes_data = b""

            try:
                # Đọc in-memory binary tương thích NiceGUI 3.x (e.file) và NiceGUI <3.x (e.content)
                if hasattr(e, "content") and e.content is not None:
                    filename = getattr(e, "name", getattr(e.content, "name", "file"))
                    file_type = (
                        getattr(e, "type", "")
                        or mimetypes.guess_type(filename)[0]
                        or "application/octet-stream"
                    )
                    content_reader = e.content.read()
                    bytes_data = (
                        await content_reader
                        if inspect.isawaitable(content_reader)
                        else content_reader
                    )
                elif hasattr(e, "file") and e.file is not None:
                    filename = getattr(e.file, "name", "file")
                    file_type = (
                        getattr(e.file, "content_type", "")
                        or mimetypes.guess_type(filename)[0]
                        or "application/octet-stream"
                    )
                    content_reader = e.file.read()
                    bytes_data = (
                        await content_reader
                        if inspect.isawaitable(content_reader)
                        else content_reader
                    )
                else:
                    show_toast("Không nhận diện được đối tượng tệp tải lên", "negative")
                    return

                size_bytes = len(bytes_data)
                formatted_size = format_file_size(size_bytes)

                # Nạp vào RAM buffer
                in_memory_files.append(
                    {
                        "name": filename,
                        "bytes": bytes_data,
                        "size": size_bytes,
                        "size_formatted": formatted_size,
                        "type": file_type,
                        "category": category,
                    }
                )
                update_file_list_ui()
                show_toast(
                    f"Đã nạp thành công '{filename}' ({formatted_size}) vào RAM",
                    "positive",
                )

                if on_upload_callback:
                    res = on_upload_callback(filename, bytes_data, file_type)
                    if inspect.isawaitable(res):
                        await res

            except Exception as err:
                show_toast(f"Lỗi khi đọc file vào RAM: {str(err)}", "negative")

        # Nội dung Panels 2 Tabs
        with ui.tab_panels(tabs, value=tab_docs).classes(
            "w-full bg-transparent p-0 mt-3"
        ):
            # Tab 1: Tài liệu học tập (.pdf, .txt, .md)
            with ui.tab_panel(tab_docs).classes("p-0"):
                with ui.column().classes(
                    "border-2 border-dashed border-slate-300 hover:border-indigo-500 rounded-2xl "
                    "bg-slate-50/60 p-6 transition duration-200 items-center justify-center text-center w-full"
                ):
                    ui.icon("description", size="36px").classes(
                        f"text-{TOKENS['primary']} mb-1"
                    )
                    ui.label("Kéo thả tài liệu học tập hoặc nhấp để chọn").classes(
                        f"text-sm font-bold text-{TOKENS['text_primary']}"
                    )
                    ui.label("Chấp nhận .pdf, .txt, .md (Tối đa 10MB)").classes(
                        f"text-xs text-{TOKENS['text_secondary']} mb-4"
                    )

                    ui.upload(
                        auto_upload=True,
                        max_file_size=10_000_000,
                        on_upload=lambda e: handle_binary_upload(e, "document"),
                        on_rejected=lambda: show_toast(
                            "File không hợp lệ hoặc vượt quá 10MB", "warning"
                        ),
                    ).props(
                        'accept=".pdf,.txt,.md" flat bordered color="indigo"'
                    ).classes(
                        "w-full max-w-md bg-white rounded-xl shadow-2xs"
                    )

            # Tab 2: Âm thanh bài giảng (.mp3, .wav, .m4a)
            with ui.tab_panel(tab_audio).classes("p-0"):
                with ui.column().classes(
                    "border-2 border-dashed border-slate-300 hover:border-indigo-500 rounded-2xl "
                    "bg-slate-50/60 p-6 transition duration-200 items-center justify-center text-center w-full"
                ):
                    ui.icon("graphic_eq", size="36px").classes("text-purple-600 mb-1")
                    ui.label("Kéo thả bản ghi âm bài giảng hoặc nhấp để chọn").classes(
                        f"text-sm font-bold text-{TOKENS['text_primary']}"
                    )
                    ui.label("Chấp nhận .mp3, .wav, .m4a (Tối đa 10MB)").classes(
                        f"text-xs text-{TOKENS['text_secondary']} mb-4"
                    )

                    ui.upload(
                        auto_upload=True,
                        max_file_size=10_000_000,
                        on_upload=lambda e: handle_binary_upload(e, "audio"),
                        on_rejected=lambda: show_toast(
                            "File âm thanh không hợp lệ hoặc vượt quá 10MB", "warning"
                        ),
                    ).props(
                        'accept=".mp3,.wav,.m4a" flat bordered color="purple"'
                    ).classes(
                        "w-full max-w-md bg-white rounded-xl shadow-2xs"
                    )

    return {
        "get_files": lambda: list(in_memory_files),
        "clear_files": clear_all_files,
    }
