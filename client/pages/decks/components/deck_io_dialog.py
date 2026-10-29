"""
deck_io_dialog.py — Dialog Xuất & Nhập Bộ Thẻ (Export & Import Deck).
Hỗ trợ Import CSV/Excel/Anki Tab-text và Export PDF Printable A4 2 mặt, Anki TXT, JSON, CSV.
"""

from __future__ import annotations

import asyncio
import inspect
from typing import Any, Callable, Dict, Optional
from nicegui import events, ui
from components.layout import show_toast
from services import api


def open_deck_io_dialog(
    deck_id: int,
    deck_title: str,
    on_imported: Optional[Callable[[], Any]] = None,
) -> None:
    """Mở hộp thoại Xuất / Nhập linh hoạt cho bộ thẻ."""
    dialog = ui.dialog().props("maximized=false persistent=false")
    dialog.on("hide", dialog.delete)

    with dialog, ui.card().classes(
        "w-full max-w-2xl max-h-[88vh] flex flex-col p-6 md:p-8 rounded-3xl bg-white shadow-2xl border border-slate-100 gap-4 overflow-hidden"
    ):
        # Header cố định ở đầu dialog
        with ui.row().classes(
            "w-full items-center justify-between pb-3 border-b border-slate-100 shrink-0"
        ):
            with ui.row().classes("items-center gap-3"):
                with ui.element("div").classes(
                    "w-10 h-10 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center border border-indigo-100 shadow-2xs"
                ):
                    ui.icon("swap_horiz", size="24px")
                with ui.column().classes("gap-0"):
                    ui.label(f"Xuất / Nhập: {deck_title}").classes(
                        "text-lg font-black text-slate-900 truncate max-w-sm"
                    )
                    ui.label(f"ID Bộ thẻ #{deck_id}").classes(
                        "text-xs text-slate-400 font-medium"
                    )

            ui.button(icon="close", on_click=dialog.close).props(
                "flat round dense"
            ).classes("text-slate-400 hover:text-slate-700")

        # Tabs điều hướng Nhập vs Xuất (shrink-0)
        with ui.tabs().classes(
            "w-full border-b border-slate-200 text-slate-600 bg-slate-50 rounded-2xl p-1 shrink-0"
        ) as io_tabs:
            tab_import = ui.tab(
                "import", label="1. Nhập Thẻ (Import)", icon="file_upload"
            ).classes("font-bold text-xs")
            tab_export = ui.tab(
                "export", label="2. Xuất Thẻ (Export)", icon="file_download"
            ).classes("font-bold text-xs")

        # Nội dung tab scrollable theo chiều dọc khi vượt quá chiều cao màn hình
        with ui.tab_panels(io_tabs, value=tab_import).classes(
            "w-full bg-transparent p-0 mt-2 flex-1 overflow-y-auto pr-1"
        ):
            # -------------------------------------------------------------
            # TAB 1: IMPORT THẺ
            # -------------------------------------------------------------
            with ui.tab_panel(tab_import).classes("w-full p-0 flex flex-col gap-4"):
                ui.label(
                    "Tải lên file CSV / Excel (.xlsx) hoặc dán văn bản Tab-delimited copy từ Quizlet/Anki:"
                ).classes("text-xs text-slate-600 leading-relaxed")

                # Vùng dán text có scroll nội bộ (rows=6), không làm đẩy modal tràn màn hình
                text_input = (
                    ui.textarea(
                        label="Dán văn bản (Mỗi dòng một thẻ, cách nhau bởi Tab hoặc dấu phẩy)",
                        placeholder="Question [Tab] Answer [Tab] Ghi chú cá nhân...",
                    )
                    .props("outlined rows=6")
                    .classes("w-full text-xs font-mono bg-slate-50 rounded-xl")
                )

                upload_state: Dict[str, Any] = {"file_bytes": None, "filename": None}

                async def handle_upload(e: events.UploadEventArguments):
                    try:
                        # Tương thích NiceGUI 3.x (e.file) và các phiên bản NiceGUI khác (e.content)
                        f_obj = getattr(e, "file", None) or getattr(e, "content", None)
                        if f_obj is None:
                            show_toast("Không nhận diện được tệp tải lên", "warning")
                            return

                        f_name = str(
                            getattr(
                                f_obj,
                                "filename",
                                getattr(f_obj, "name", getattr(e, "name", "file")),
                            )
                        )
                        read_fn = getattr(f_obj, "read", None)
                        if callable(read_fn):
                            res = read_fn()
                            raw_data = await res if inspect.isawaitable(res) else res
                            if isinstance(raw_data, bytes):
                                f_bytes = raw_data
                            elif isinstance(raw_data, bytearray):
                                f_bytes = bytes(raw_data)
                            elif isinstance(raw_data, str):
                                f_bytes = raw_data.encode("utf-8")
                            elif isinstance(raw_data, memoryview):
                                f_bytes = raw_data.tobytes()
                            else:
                                f_bytes = b""
                        else:
                            f_bytes = b""

                        if not f_bytes:
                            show_toast("Tệp trống không có nội dung", "warning")
                            return

                        upload_state["file_bytes"] = f_bytes
                        upload_state["filename"] = f_name

                        size_kb = len(f_bytes) / 1024
                        file_badge.text = f"📄 {f_name} ({size_kb:.1f} KB)"
                        file_info_container.set_visibility(True)
                        show_toast(f"Đã nạp file {f_name} ({size_kb:.1f} KB)", "info")
                    except Exception as err:
                        show_toast(f"Lỗi đọc file: {str(err)}", "negative")

                def clear_uploaded_file():
                    upload_state["file_bytes"] = None
                    upload_state["filename"] = None
                    file_info_container.set_visibility(False)
                    show_toast("Đã bỏ chọn file tải lên", "info")

                with ui.column().classes("w-full gap-2"):
                    with ui.row().classes(
                        "w-full items-center justify-between flex-wrap gap-2"
                    ):
                        ui.upload(
                            label="Hoặc chọn file .csv / .xlsx / .txt / .tsv",
                            on_upload=handle_upload,
                            auto_upload=True,
                            max_file_size=10_000_000,
                        ).props(
                            "flat dense color=indigo accept=.csv,.xlsx,.txt,.tsv"
                        ).classes(
                            "w-full max-w-sm"
                        )

                    with ui.row().classes(
                        "items-center justify-between px-3 py-2 bg-emerald-50 rounded-xl border border-emerald-200 w-full"
                    ) as file_info_container:
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("check_circle", size="18px").classes(
                                "text-emerald-600"
                            )
                            file_badge = ui.label("").classes(
                                "text-xs text-emerald-800 font-bold"
                            )
                        ui.button(
                            icon="close",
                            on_click=clear_uploaded_file,
                        ).props(
                            "flat round dense size=sm"
                        ).classes("text-emerald-700 hover:text-rose-600 cursor-pointer")
                    file_info_container.set_visibility(False)

                import_button: Dict[str, Any] = {}

                async def do_import():
                    button = import_button["button"]
                    button.props("loading")
                    try:
                        raw_text = (
                            text_input.value.strip() if text_input.value else None
                        )
                        f_bytes = upload_state["file_bytes"]
                        f_name = upload_state["filename"]

                        if not raw_text and not f_bytes:
                            show_toast(
                                "Vui lòng dán nội dung thẻ hoặc tải lên file dữ liệu",
                                "warning",
                            )
                            return

                        res = await api.import_deck_cards(
                            deck_id=deck_id,
                            raw_text=raw_text,
                            file_bytes=f_bytes,
                            filename=f_name,
                        )

                        if isinstance(res, dict) and res.get("error"):
                            err_msg = str(
                                res.get("message")
                                or res.get("error")
                                or "Lỗi không xác định"
                            )
                            show_toast(err_msg, "negative")
                        else:
                            count = res.get("created_count", 0)
                            show_toast(
                                f"Đã nhập thành công {count} flashcards!", "positive"
                            )
                            dialog.close()
                            if on_imported:
                                cb = on_imported()
                                if asyncio.iscoroutine(cb):
                                    await cb
                    finally:
                        button.props(remove="loading")

                import_button["button"] = ui.button(
                    "TIẾN HÀNH NẠP THẺ VÀO DECK",
                    icon="cloud_upload",
                    on_click=do_import,
                ).classes(
                    "w-full py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-extrabold rounded-2xl shadow-md"
                )

            # -------------------------------------------------------------
            # TAB 2: EXPORT THẺ
            # -------------------------------------------------------------
            with ui.tab_panel(tab_export).classes("w-full p-0 flex flex-col gap-4"):
                ui.label(
                    "Chọn định dạng xuất để tải về hoặc in ấn phục vụ học tập:"
                ).classes("text-xs text-slate-600")

                export_options = [
                    (
                        "pdf",
                        "🖨️ PDF Printable A4 (In 2 mặt cắt rời)",
                        "Lưới A4 chuẩn 8 thẻ/trang; mặt trước Câu hỏi, mặt sau Đáp án khớp vị trí cắt",
                    ),
                    (
                        "anki",
                        "⚡ Anki / AnkiDroid (.txt Tab-delimited)",
                        "Bao gồm toàn bộ trường SM-2 (Ease Factor, Interval) để nạp vào Anki",
                    ),
                    (
                        "json",
                        "📦 Dữ liệu JSON Toàn Phần",
                        "Kết xuất đầy đủ Metadata, siêu dữ liệu phân tích và danh sách thẻ",
                    ),
                    (
                        "csv",
                        "📊 Bảng tính CSV (Excel / Sheets)",
                        "Định dạng bảng tính cột Question, Answer, Personal Notes, Tags",
                    ),
                ]

                format_radio = (
                    ui.radio(
                        {opt[0]: f"{opt[1]} — {opt[2]}" for opt in export_options},
                        value="pdf",
                    )
                    .props("dense")
                    .classes("flex flex-col gap-2 text-xs")
                )

                def do_export():
                    fmt = format_radio.value or "pdf"
                    url = api.get_export_deck_url(deck_id, export_format=fmt)
                    ui.download(url)
                    show_toast(
                        f"Đang bắt đầu tải xuống định dạng {fmt.upper()}...", "positive"
                    )

                ui.button(
                    "TẢI XUỐNG NGAY",
                    icon="download",
                    on_click=do_export,
                ).classes(
                    "w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold rounded-2xl shadow-md"
                )

    dialog.open()
