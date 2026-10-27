from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from nicegui import ui

from components import (
    TOKENS,
    app_shell,
    format_file_size,
    render_dropzone,
    render_footer,
    show_toast,
)
from components.generator_preview import render_generator_preview
from components.home_hero import render_home_hero
from services import api
from services.auth_guard import get_current_user


def _extract_cards_list(raw_response: Any) -> List[Dict[str, Any]]:
    """Trích xuất mảng danh sách flashcards từ cấu trúc dữ liệu phản hồi API."""
    if isinstance(raw_response, list):
        return [c for c in raw_response if isinstance(c, dict)]
    if isinstance(raw_response, dict):
        if "cards" in raw_response and isinstance(raw_response["cards"], list):
            return [c for c in raw_response["cards"] if isinstance(c, dict)]
        if "data" in raw_response and isinstance(raw_response["data"], list):
            return [c for c in raw_response["data"] if isinstance(c, dict)]
    return []


def render_home_page() -> None:
    """Studio tạo bài học SPA kết hợp Hero section và AI Card Generator."""
    with app_shell(
        active_tab="home", title="EduFlash AI - Studio Khởi Tạo Bài Học Thông Minh"
    ):
        cur_user = get_current_user() or {}
        active_user_id = int(cur_user.get("id") or cur_user.get("user_id") or 1)

        # 1. Hero Section Component
        render_home_hero()

        # 2. Workspace Studio Section (#workspace-studio)
        uploaded_ram_files: List[Dict[str, Any]] = []
        generated_cards_state: List[Dict[str, Any]] = []

        with ui.element("div").props('id="workspace-studio"').classes(
            "w-full mt-12 scroll-mt-20"
        ):
            with ui.card().classes(
                "bg-white border border-slate-200 rounded-3xl shadow-xl p-6 md:p-8 max-w-4xl mx-auto w-full gap-6"
            ):
                with ui.row().classes(
                    "items-center justify-between w-full pb-4 border-b border-slate-100"
                ):
                    with ui.row().classes("items-center gap-3"):
                        with ui.element("div").classes(
                            f"w-10 h-10 rounded-xl bg-{TOKENS['primary_light']} flex items-center justify-center text-{TOKENS['primary']}"
                        ):
                            ui.icon("auto_fix_high", size="22px")
                        with ui.column().classes("gap-0"):
                            ui.label("Studio Khởi Tạo Flashcard AI").classes(
                                f"text-xl font-extrabold text-{TOKENS['text_primary']} tracking-tight"
                            )
                            ui.label(
                                "Dán văn bản bài giảng hoặc nạp tệp trực tiếp vào bộ nhớ RAM"
                            ).classes(f"text-xs text-{TOKENS['text_secondary']}")

                    status_badge = ui.label("Sẵn sàng").classes(
                        f"text-xs font-semibold px-3 py-1 rounded-full bg-{TOKENS['bg_subtle']} text-{TOKENS['text_secondary']} border border-{TOKENS['border']}"
                    )

                input_section_container = ui.column().classes("w-full gap-5")

                with input_section_container:
                    with ui.tabs().classes(
                        f"w-full border-b border-{TOKENS['border']} text-{TOKENS['text_secondary']}"
                    ) as input_tabs:
                        tab_text = ui.tab(
                            "text", label="1. Nhập văn bản nhanh", icon="edit_note"
                        ).classes(f"hover:text-{TOKENS['primary']} font-bold text-sm")
                        tab_files = ui.tab(
                            "files",
                            label="2. Nạp tài liệu & âm thanh",
                            icon="cloud_upload",
                        ).classes(f"hover:text-{TOKENS['primary']} font-bold text-sm")

                    with ui.tab_panels(input_tabs, value=tab_text).classes(
                        "w-full bg-transparent p-0 mt-1"
                    ):
                        with ui.tab_panel(tab_text).classes("p-0"):
                            ui.label("Nội dung bài giảng / tóm tắt lý thuyết:").classes(
                                f"text-xs font-bold text-{TOKENS['text_secondary']} uppercase tracking-wider mb-2"
                            )
                            text_input = (
                                ui.textarea(
                                    placeholder="Dán toàn bộ bài học, các khái niệm định nghĩa, công thức hoặc đoạn văn bản cần tạo thẻ câu hỏi ôn tập tại đây..."
                                )
                                .props('rows="6" autogrow outlined')
                                .classes(
                                    "w-full bg-slate-50/60 text-slate-800 text-sm rounded-2xl"
                                )
                            )

                        with ui.tab_panel(tab_files).classes("p-0"):

                            def handle_dropzone_upload(
                                filename: str, file_bytes: bytes, mime_type: str
                            ) -> None:
                                is_audio = any(
                                    filename.lower().endswith(ext)
                                    for ext in [".mp3", ".wav", ".m4a", ".ogg"]
                                )
                                uploaded_ram_files.clear()
                                uploaded_ram_files.append(
                                    {
                                        "name": filename,
                                        "bytes": file_bytes,
                                        "size": len(file_bytes),
                                        "category": "audio" if is_audio else "document",
                                    }
                                )
                                status_badge.text = f"Đã nạp {filename}"
                                status_badge.classes(
                                    add="bg-emerald-50 text-emerald-700 border-emerald-200 font-bold",
                                    remove=f"bg-{TOKENS['bg_subtle']} text-{TOKENS['text_secondary']}",
                                )
                                show_toast(
                                    f"Đã lưu '{filename}' ({format_file_size(len(file_bytes))}) vào RAM",
                                    "positive",
                                )

                            dropzone_ref = render_dropzone(
                                on_upload_callback=handle_dropzone_upload
                            )

                loading_container = ui.column().classes(
                    "w-full items-center justify-center py-8 gap-4 border border-dashed border-indigo-200 rounded-2xl bg-indigo-50/30"
                )
                loading_container.set_visibility(False)

                with loading_container:
                    ui.spinner("dots", size="lg", color="indigo")
                    ai_badge = ui.label(
                        "[AI Processing: Flan-T5 / Whisper inference...]"
                    ).classes(
                        "text-xs md:text-sm font-bold text-indigo-700 bg-white px-4 py-1.5 rounded-full shadow-xs border border-indigo-200 animate-pulse"
                    )
                    loading_detail = ui.label(
                        "Mô hình đang phân tích ngữ nghĩa và trích xuất flashcard..."
                    ).classes("text-xs text-slate-500 font-medium")

                generate_btn = ui.button(
                    "⚡ Sinh Flashcard Tự Động",
                ).classes(
                    f"w-full py-4 text-base font-extrabold text-white rounded-2xl bg-{TOKENS['primary']} "
                    f"hover:bg-{TOKENS['primary_hover']} shadow-lg shadow-indigo-600/30 hover:shadow-indigo-600/50 "
                    "transition duration-200 cursor-pointer"
                )

                preview_container = ui.column().classes(
                    "w-full gap-6 mt-6 pt-6 border-t border-slate-100"
                )
                preview_container.set_visibility(False)

                async def render_preview_cards() -> None:
                    await render_generator_preview(
                        preview_container=preview_container,
                        generated_cards_state=generated_cards_state,
                        active_user_id=active_user_id,
                        on_add_card=add_empty_preview_card,
                        on_reset=reset_to_input_state,
                        on_rerender=render_preview_cards,
                    )

                def add_empty_preview_card():
                    generated_cards_state.append(
                        {
                            "question": "Câu hỏi mới...",
                            "answer": "Đáp án...",
                            "explanation": "",
                            "difficulty": "Trung bình",
                            "tags": [],
                        }
                    )
                    asyncio.ensure_future(render_preview_cards())

                def reset_to_input_state():
                    generated_cards_state.clear()
                    input_section_container.set_visibility(True)
                    generate_btn.set_visibility(True)
                    preview_container.set_visibility(False)
                    status_badge.text = "Sẵn sàng"
                    status_badge.classes(
                        add=f"bg-{TOKENS['bg_subtle']} text-{TOKENS['text_secondary']}",
                        remove="bg-emerald-50 text-emerald-700 border-emerald-200 font-bold",
                    )

                async def execute_generate_workflow() -> None:
                    current_files = (
                        dropzone_ref["get_files"]()
                        if "dropzone_ref" in locals() and dropzone_ref
                        else uploaded_ram_files
                    )
                    raw_text = text_input.value.strip() if text_input.value else ""

                    if not current_files and not raw_text:
                        show_toast(
                            "Vui lòng nhập văn bản bài giảng hoặc tải tài liệu/âm thanh vào RAM",
                            "warning",
                        )
                        return

                    generate_btn.props("loading disable")
                    generate_btn.set_visibility(False)
                    input_section_container.set_visibility(False)
                    loading_container.set_visibility(True)
                    status_badge.text = "AI Đang Xử Lý..."

                    try:
                        cards_fetched: List[Dict[str, Any]] = []

                        if current_files:
                            target_file = current_files[0]
                            file_bytes = target_file.get("bytes", b"")
                            filename = target_file.get("name", "document.pdf")
                            category = target_file.get("category", "document")

                            if category == "audio":
                                ai_badge.text = f"[AI Processing: Whisper STT bóc băng '{filename}'...]"
                                loading_detail.text = "Whisper AI đang chuyển âm thanh thành phụ đề văn bản..."
                                audio_resp = await api.transcribe_audio(
                                    file_bytes=file_bytes, filename=filename
                                )
                                transcript_text = ""
                                if isinstance(audio_resp, dict):
                                    transcript_text = audio_resp.get(
                                        "text", ""
                                    ) or audio_resp.get("transcript", "")
                                if not transcript_text:
                                    show_toast(
                                        "Không nhận dạng được âm thanh từ file",
                                        "warning",
                                    )
                                    return

                                ai_badge.text = (
                                    "[AI Processing: Flan-T5 inference flashcards...]"
                                )
                                loading_detail.text = "Flan-T5 đang trích xuất câu hỏi từ bản bóc băng âm thanh..."
                                gen_resp = await api.generate_flashcards(
                                    text=transcript_text
                                )
                                cards_fetched = _extract_cards_list(gen_resp)

                            else:
                                ai_badge.text = f"[AI Processing: Đang nạp '{filename}' lên Server...]"
                                loading_detail.text = (
                                    "Đang xử lý tài liệu PDF/Text qua Backend..."
                                )
                                doc_resp = await api.upload_doc(
                                    file_bytes=file_bytes,
                                    filename=filename,
                                    user_id=active_user_id,
                                )
                                doc_id = None
                                if isinstance(doc_resp, dict):
                                    doc_id = doc_resp.get("id") or doc_resp.get(
                                        "document_id"
                                    )

                                if doc_id:
                                    ai_badge.text = "[AI Processing: Flan-T5 inference flashcards...]"
                                    loading_detail.text = "Mô hình đang tổng hợp câu hỏi trắc nghiệm và câu trả lời..."
                                    gen_resp = await api.generate_cards(
                                        doc_id=doc_id,
                                        deck_id=None,
                                        user_id=active_user_id,
                                    )
                                    cards_fetched = _extract_cards_list(gen_resp)
                                else:
                                    if filename.lower().endswith((".txt", ".md")):
                                        text_str = file_bytes.decode(
                                            "utf-8", errors="ignore"
                                        )
                                        gen_resp = await api.generate_flashcards(
                                            text=text_str
                                        )
                                        cards_fetched = _extract_cards_list(gen_resp)

                        elif raw_text:
                            ai_badge.text = (
                                "[AI Processing: Flan-T5 inference flashcards...]"
                            )
                            loading_detail.text = (
                                "Mô hình ngôn ngữ đang tóm tắt và sinh flashcards..."
                            )
                            gen_resp = await api.generate_flashcards(text=raw_text)
                            cards_fetched = _extract_cards_list(gen_resp)

                        if cards_fetched:
                            generated_cards_state.clear()
                            generated_cards_state.extend(cards_fetched)
                            show_toast(
                                f"AI đã sinh thành công {len(cards_fetched)} thẻ Flashcard!",
                                "positive",
                            )
                            await render_preview_cards()
                        else:
                            show_toast(
                                "Không tìm thấy nội dung trọng tâm để sinh câu hỏi",
                                "warning",
                            )
                            input_section_container.set_visibility(True)
                            generate_btn.set_visibility(True)
                    except Exception as err:
                        show_toast(
                            f"Lỗi trong quá trình sinh thẻ AI: {err}", "negative"
                        )
                        input_section_container.set_visibility(True)
                        generate_btn.set_visibility(True)
                    finally:
                        loading_container.set_visibility(False)
                        generate_btn.props(remove="loading disable")

                generate_btn.on_click(execute_generate_workflow)

        # 3. Footer Component
        render_footer()
