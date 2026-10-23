from typing import Any, Callable, Dict, List
from nicegui import ui

from components import (
    app_shell,
    show_toast,
    render_hero_section,
    render_studio_workspace,
    render_interactive_demo,
    render_features_grid,
    render_footer,
)
from services.api import (
    upload_doc,
    generate_cards,
    transcribe_audio,
    generate_flashcards,
)


def _extract_cards_list(raw_response: Any) -> List[Dict[str, Any]]:
    """Trích xuất an toàn danh sách thẻ bài học từ phản hồi Backend."""
    if isinstance(raw_response, list):
        return [c for c in raw_response if isinstance(c, dict)]
    if isinstance(raw_response, dict):
        cards_val = raw_response.get("cards")
        if isinstance(cards_val, list):
            return [c for c in cards_val if isinstance(c, dict)]
    return []


def render_home_page() -> None:
    """Trang chủ Landing Page EdTech chuẩn UI/UX cao cấp cho EduFlash AI.

    Được module hóa thành 5 component độc lập:
    1. Hero Section (client/components/hero_section.py)
    2. Studio Workspace (client/components/studio_workspace.py)
    3. Interactive Demo (client/components/interactive_demo.py)
    4. Features & Benefits Grid (client/components/features_grid.py)
    5. Footer (client/components/footer.py)
    """
    with app_shell(
        active_tab="home", title="EduFlash AI - Học nhanh, nhớ lâu với AI & SM-2"
    ):
        # 1. Khối Hero Section
        render_hero_section()

        # Khởi tạo tham chiếu controller cho Demo trước để Studio có thể cập nhật
        demo_ctrl_holder: Dict[str, Any] = {"ctrl": None}

        # 2. Xử lý logic sinh Flashcard từ Studio Workspace
        async def on_generate_cards(
            files: List[Dict[str, Any]],
            text_input: str,
            set_status: Callable[[str], None],
        ) -> None:
            cards_result: List[Dict[str, Any]] = []

            if files:
                last_item = files[-1]
                if last_item["category"] == "document":
                    set_status(f"Đang trích xuất tài liệu '{last_item['name']}'...")
                    doc_res = await upload_doc(last_item["bytes"], last_item["name"])
                    if isinstance(doc_res, dict) and doc_res.get("error"):
                        # Fallback đọc chuỗi trực tiếp nếu là tệp text/markdown
                        if last_item["name"].lower().endswith((".txt", ".md")):
                            txt_raw = last_item["bytes"].decode(
                                "utf-8", errors="ignore"
                            )
                            gen_res = await generate_flashcards(txt_raw)
                            cards_result = _extract_cards_list(gen_res)
                        if not cards_result:
                            show_toast(
                                doc_res.get("message", "Lỗi nạp tài liệu"), "negative"
                            )
                    else:
                        doc_id = doc_res.get("id") or doc_res.get("document_id")
                        if doc_id:
                            set_status(
                                "Mô hình Flan-T5 đang tổng hợp câu hỏi trắc nghiệm..."
                            )
                            gen_res = await generate_cards(doc_id=doc_id)
                            cards_result = _extract_cards_list(gen_res)
                            if not cards_result and isinstance(gen_res, dict) and gen_res.get("error"):
                                show_toast(
                                    gen_res.get("message", "Lỗi sinh thẻ"), "negative"
                                )
                elif last_item["category"] == "audio":
                    set_status(
                        f"Mô hình Whisper đang bóc băng âm thanh '{last_item['name']}'..."
                    )
                    audio_res = await transcribe_audio(
                        last_item["bytes"], last_item["name"]
                    )
                    if isinstance(audio_res, dict) and audio_res.get("error"):
                        show_toast(
                            audio_res.get("message", "Lỗi bóc băng âm thanh"),
                            "negative",
                        )
                    else:
                        transcript = audio_res.get("text", "") or audio_res.get(
                            "transcript", ""
                        )
                        if transcript:
                            set_status(
                                "Flan-T5 đang chuyển bản bóc băng thành flashcards..."
                            )
                            gen_res = await generate_flashcards(transcript)
                            cards_result = _extract_cards_list(gen_res)
            elif text_input:
                set_status("Flan-T5 đang trích xuất câu hỏi từ văn bản...")
                gen_res = await generate_flashcards(text_input)
                cards_result = _extract_cards_list(gen_res)
                if not cards_result and isinstance(gen_res, dict) and gen_res.get("error"):
                    show_toast(gen_res.get("message", "Lỗi sinh flashcard"), "negative")

            if len(cards_result) > 0:
                show_toast(
                    f"Đã tạo thành công {len(cards_result)} thẻ flashcard!", "positive"
                )
                first_card: Dict[str, Any] = cards_result[0]
                card_preview = {
                    "id": str(first_card.get("id", "ai-01")),
                    "question": first_card.get("question")
                    or first_card.get("front", "Câu hỏi mới"),
                    "answer": first_card.get("answer")
                    or first_card.get("back", "Đáp án mới"),
                    "explanation": first_card.get(
                        "explanation", "Trích xuất tự động bởi Flan-T5"
                    ),
                    "hint": first_card.get("hint", ""),
                    "deck_name": first_card.get("deck_name", "Bài giảng mới"),
                    "difficulty": first_card.get("difficulty", "Trung bình"),
                    "review_count": 0,
                }
                if demo_ctrl_holder["ctrl"]:
                    demo_ctrl_holder["ctrl"].update_card(card_preview)
                    demo_ctrl_holder["ctrl"].log(
                        f"Đã nạp thẻ mới vừa tạo: '{card_preview['question'][:40]}...'"
                    )
                ui.run_javascript(
                    "document.getElementById('demo-section').scrollIntoView({behavior: 'smooth'})"
                )

        # 2. Khối Studio Workspace
        render_studio_workspace(on_generate_cards=on_generate_cards)

        # 3. Khối Interactive Demo & Spaced Repetition (SM-2 Preview)
        demo_ctrl_holder["ctrl"] = render_interactive_demo()

        # 4. Khối Features & Benefits Grid
        render_features_grid()

        # 5. Khối Footer
        render_footer()
