from __future__ import annotations

import asyncio
import inspect
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
from services import api


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
        # -------------------------------------------------------------------
        # 1. HERO SECTION
        # -------------------------------------------------------------------
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

            # Cụm nút CTA điều hướng mượt
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
                ).classes(
                    "bg-white hover:bg-slate-100 text-slate-800 font-bold px-6 py-3 rounded-2xl "
                    "border border-slate-200 shadow-sm transition duration-200 cursor-pointer"
                )

                ui.button(
                    "THƯ VIỆN DECK",
                    icon="folder_special",
                    on_click=lambda: ui.navigate.to("/decks"),
                ).classes(
                    "bg-white hover:bg-slate-100 text-slate-800 font-bold px-6 py-3 rounded-2xl "
                    "border border-slate-200 shadow-sm transition duration-200 cursor-pointer"
                )

        # -------------------------------------------------------------------
        # 2. WORKSPACE STUDIO SECTION (#workspace-studio)
        # -------------------------------------------------------------------
        # State lưu trữ danh sách tệp nhị phân trong RAM & thẻ AI sinh
        uploaded_ram_files: List[Dict[str, Any]] = []
        generated_cards_state: List[Dict[str, Any]] = []

        with ui.element("div").props('id="workspace-studio"').classes(
            "w-full mt-12 scroll-mt-20"
        ):
            with ui.card().classes(
                "bg-white border border-slate-200 rounded-3xl shadow-xl p-6 md:p-8 max-w-4xl mx-auto w-full gap-6"
            ):
                # Header Studio
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

                # Container nhập liệu
                input_section_container = ui.column().classes("w-full gap-5")

                with input_section_container:
                    # Tabs chuyển đổi giữa Textarea và Dropzone
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
                        # Tab 1: Nhập văn bản nhanh
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

                        # Tab 2: Nạp tài liệu & âm thanh vào RAM
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

                # Loading Skeleton & Progress Bar
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

                # Nút kích hoạt AI Sinh Flashcard
                generate_btn = ui.button(
                    "⚡ Sinh Flashcard Tự Động",
                ).classes(
                    f"w-full py-4 text-base font-extrabold text-white rounded-2xl bg-{TOKENS['primary']} "
                    f"hover:bg-{TOKENS['primary_hover']} shadow-lg shadow-indigo-600/30 hover:shadow-indigo-600/50 "
                    "transition duration-200 cursor-pointer"
                )

                # -----------------------------------------------------------
                # 3. RESULT PREVIEW SECTION (Duyệt & chỉnh sửa trước khi lưu)
                # -----------------------------------------------------------
                preview_container = ui.column().classes(
                    "w-full gap-6 mt-6 pt-6 border-t border-slate-100"
                )
                preview_container.set_visibility(False)

                async def render_preview_cards() -> None:
                    """Hiển thị danh sách thẻ xem trước và bộ công cụ lưu vào Deck."""
                    preview_container.clear()
                    if not generated_cards_state:
                        preview_container.set_visibility(False)
                        return

                    preview_container.set_visibility(True)

                    with preview_container:
                        # Thanh Header Preview & Lưu vào Deck
                        with ui.row().classes(
                            "w-full items-center justify-between pb-3 border-b border-slate-100 flex-wrap gap-4"
                        ):
                            with ui.row().classes("items-center gap-2"):
                                ui.icon("check_circle", size="24px").classes(
                                    "text-emerald-600"
                                )
                                ui.label(
                                    f"Xem trước {len(generated_cards_state)} Flashcards sinh từ AI"
                                ).classes("text-lg font-bold text-slate-900")

                            with ui.row().classes("items-center gap-2"):
                                ui.button(
                                    "+ Thêm thẻ thủ công",
                                    icon="add",
                                    on_click=add_empty_preview_card,
                                ).props("flat dense").classes(
                                    f"text-xs font-bold text-{TOKENS['primary']} hover:underline"
                                )
                                ui.button(
                                    "Làm mới / Hủy",
                                    icon="refresh",
                                    on_click=reset_to_input_state,
                                ).props("flat dense").classes(
                                    "text-xs font-semibold text-rose-500 hover:underline"
                                )

                        # Cụm Lưu vào Deck chính: Dropdown chọn Deck hoặc tạo mới
                        decks_resp = await api.get_decks()
                        existing_decks: List[Dict[str, Any]] = (
                            decks_resp if isinstance(decks_resp, list) else []
                        )
                        deck_options = {
                            d["id"]: d.get("title", f"Deck #{d['id']}")
                            for d in existing_decks
                            if isinstance(d, dict) and "id" in d
                        }
                        default_deck_id = (
                            list(deck_options.keys())[0] if deck_options else None
                        )

                        with ui.card().classes(
                            "w-full bg-slate-50 border border-slate-200/80 rounded-2xl p-4 gap-3"
                        ):
                            with ui.row().classes(
                                "items-center justify-between w-full flex-wrap gap-3"
                            ):
                                with ui.row().classes(
                                    "items-center gap-3 flex-1 min-w-[280px]"
                                ):
                                    ui.icon("folder", size="20px").classes(
                                        f"text-{TOKENS['primary']}"
                                    )
                                    deck_select = (
                                        ui.select(
                                            options=deck_options,
                                            value=default_deck_id,
                                            label="Chọn Deck chính",
                                        )
                                        .props("outlined dense")
                                        .classes("w-64 bg-white rounded-lg")
                                    )

                                    new_deck_input = (
                                        ui.input(placeholder="Hoặc gõ tên Deck mới...")
                                        .props("outlined dense")
                                        .classes("w-64 bg-white rounded-lg")
                                    )

                                save_all_btn = ui.button(
                                    "Lưu vào Deck chính",
                                    icon="save",
                                ).classes(
                                    "bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-6 py-2.5 rounded-xl shadow-md transition duration-200 cursor-pointer"
                                )

                                async def save_to_deck() -> None:
                                    save_all_btn.props("loading disable")
                                    try:
                                        target_deck_id = deck_select.value
                                        new_name = (
                                            new_deck_input.value.strip()
                                            if new_deck_input.value
                                            else ""
                                        )

                                        # Tạo Deck mới nếu người dùng nhập tên
                                        if new_name:
                                            created_deck = await api.create_deck(
                                                title=new_name
                                            )
                                            if (
                                                isinstance(created_deck, dict)
                                                and "id" in created_deck
                                            ):
                                                target_deck_id = created_deck["id"]
                                                show_toast(
                                                    f"Đã tạo Deck mới: {new_name}",
                                                    "positive",
                                                )
                                            elif isinstance(
                                                created_deck, dict
                                            ) and created_deck.get("error"):
                                                show_toast(
                                                    created_deck.get(
                                                        "message", "Lỗi tạo Deck"
                                                    ),
                                                    "negative",
                                                )
                                                return

                                        if not target_deck_id:
                                            # Tự động tạo 1 Deck mặc định nếu chưa có
                                            fallback_deck = await api.create_deck(
                                                title="Bài học mới"
                                            )
                                            target_deck_id = fallback_deck.get("id", 1)

                                        # Lưu hoặc cập nhật toàn bộ thẻ vào deck
                                        saved_count = 0
                                        for c in generated_cards_state:
                                            q = c.get("question", "").strip()
                                            a = c.get("answer", "").strip()
                                            exp = c.get("explanation", "").strip()
                                            diff = c.get("difficulty", "Trung bình")
                                            if not q or not a:
                                                continue

                                            if c.get("id"):
                                                await api.update_card(
                                                    c["id"],
                                                    question=q,
                                                    answer=a,
                                                    explanation=exp,
                                                    difficulty=diff,
                                                    deck_id=target_deck_id,
                                                )
                                            else:
                                                await api.create_card(
                                                    question=q,
                                                    answer=a,
                                                    explanation=exp,
                                                    difficulty=diff,
                                                    deck_id=target_deck_id,
                                                )
                                            saved_count += 1

                                        show_toast(
                                            f"Đã lưu thành công {saved_count} thẻ vào Deck #{target_deck_id}!",
                                            "positive",
                                        )
                                        # Điều hướng sang trang ôn tập
                                        ui.navigate.to(
                                            f"/study?deck_id={target_deck_id}"
                                        )
                                    except Exception as exc:
                                        show_toast(
                                            f"Lỗi khi lưu thẻ vào Deck: {exc}",
                                            "negative",
                                        )
                                    finally:
                                        save_all_btn.props(remove="loading disable")

                                save_all_btn.on_click(save_to_deck)

                        # Danh sách lưới xem trước các thẻ (Grid Preview)
                        with ui.element("div").classes(
                            "grid grid-cols-1 md:grid-cols-2 gap-4 w-full"
                        ):
                            for idx, card in enumerate(generated_cards_state):
                                with ui.card().classes(
                                    "w-full bg-white border border-slate-200 rounded-2xl p-5 shadow-xs gap-3 hover:shadow-md transition-shadow relative"
                                ):
                                    with ui.row().classes(
                                        "items-center justify-between w-full"
                                    ):
                                        ui.label(f"Thẻ #{idx + 1}").classes(
                                            f"text-xs font-extrabold px-2.5 py-1 rounded-md bg-{TOKENS['primary_light']} text-{TOKENS['primary']}"
                                        )

                                        def make_delete_cb(
                                            target_idx: int, card_id: Optional[int]
                                        ):
                                            async def remove_card():
                                                if card_id:
                                                    await api.delete_card(card_id)
                                                generated_cards_state.pop(target_idx)
                                                show_toast(
                                                    "Đã loại bỏ thẻ khỏi danh sách",
                                                    "info",
                                                )
                                                await render_preview_cards()

                                            return remove_card

                                        ui.button(
                                            icon="delete_outline",
                                            on_click=make_delete_cb(
                                                idx, card.get("id")
                                            ),
                                        ).props("flat dense round").classes(
                                            "text-slate-400 hover:text-rose-600"
                                        )

                                    # Trường chỉnh sửa trực tiếp câu hỏi & đáp án
                                    q_input = (
                                        ui.textarea(
                                            label="Câu hỏi",
                                            value=card.get("question", ""),
                                        )
                                        .props("rows=2 outlined dense")
                                        .classes("w-full bg-slate-50/50 text-sm")
                                    )
                                    a_input = (
                                        ui.textarea(
                                            label="Đáp án", value=card.get("answer", "")
                                        )
                                        .props("rows=2 outlined dense")
                                        .classes("w-full bg-slate-50/50 text-sm")
                                    )
                                    exp_input = (
                                        ui.input(
                                            label="Giải thích chi tiết",
                                            value=card.get("explanation", ""),
                                        )
                                        .props("outlined dense")
                                        .classes("w-full bg-slate-50/50 text-xs")
                                    )

                                    # Đồng bộ state khi người dùng nhập chỉnh sửa
                                    def bind_card_fields(
                                        target_c=card,
                                        qi=q_input,
                                        ai=a_input,
                                        ei=exp_input,
                                    ):
                                        target_c["question"] = qi.value
                                        target_c["answer"] = ai.value
                                        target_c["explanation"] = ei.value

                                    q_input.on("blur", lambda: bind_card_fields())
                                    a_input.on("blur", lambda: bind_card_fields())
                                    exp_input.on("blur", lambda: bind_card_fields())

                def add_empty_preview_card():
                    generated_cards_state.append(
                        {
                            "question": "Câu hỏi mới...",
                            "answer": "Đáp án...",
                            "explanation": "",
                            "difficulty": "Trung bình",
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

                # Xử lý sự kiện nhấn nút "⚡ Sinh Flashcard"
                async def execute_generate_workflow() -> None:
                    # Lấy file nhị phân trong RAM hoặc văn bản textarea
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

                    # Micro-interaction: disable nút, ẩn nội dung nhập, hiển thị loading state
                    generate_btn.props("loading disable")
                    generate_btn.set_visibility(False)
                    input_section_container.set_visibility(False)
                    loading_container.set_visibility(True)
                    status_badge.text = "AI Đang Xử Lý..."

                    try:
                        cards_fetched: List[Dict[str, Any]] = []

                        # Trường hợp 1: Có tệp tải lên trong RAM
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
                                    file_bytes=file_bytes, filename=filename
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
                                        doc_id=doc_id, deck_id=None
                                    )
                                    cards_fetched = _extract_cards_list(gen_resp)
                                else:
                                    # Fallback văn bản nếu là text thuần
                                    if filename.lower().endswith((".txt", ".md")):
                                        text_str = file_bytes.decode(
                                            "utf-8", errors="ignore"
                                        )
                                        gen_resp = await api.generate_flashcards(
                                            text=text_str
                                        )
                                        cards_fetched = _extract_cards_list(gen_resp)

                        # Trường hợp 2: Nhập văn bản trực tiếp qua textarea
                        elif raw_text:
                            ai_badge.text = (
                                "[AI Processing: Flan-T5 inference flashcards...]"
                            )
                            loading_detail.text = (
                                "Mô hình ngôn ngữ đang tóm tắt và sinh flashcards..."
                            )
                            gen_resp = await api.generate_flashcards(text=raw_text)
                            cards_fetched = _extract_cards_list(gen_resp)

                        # Xử lý kết quả
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

        # -------------------------------------------------------------------
        # 4. FOOTER
        # -------------------------------------------------------------------
        render_footer()
