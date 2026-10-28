import json
from typing import Any, Callable, Dict, List, Optional
from nicegui import ui
from components.layout import TOKENS


class FlashcardController:
    """Điều khiển trạng thái xoay lật và truy xuất thẻ Flashcard."""

    def __init__(
        self,
        toggle_func: Callable[[], None],
        flip_to_func: Callable[[bool], None],
        is_flipped_func: Callable[[], bool],
        element: ui.element,
    ):
        self._toggle = toggle_func
        self._flip_to = flip_to_func
        self._is_flipped = is_flipped_func
        self.element = element

    def toggle_flip(self) -> None:
        """Lật mặt thẻ 180 độ."""
        self._toggle()

    def flip_to(self, target_state: bool) -> None:
        """Chuyển trực tiếp sang mặt mong muốn (True: Back/Answer, False: Front/Question)."""
        self._flip_to(target_state)

    @property
    def is_flipped(self) -> bool:
        """Kiểm tra thẻ hiện tại đang ở mặt sau hay mặt trước."""
        return self._is_flipped()


def _get_difficulty_badge(difficulty: str) -> Dict[str, str]:
    """Ánh xạ nhãn và màu độ khó từ Design System TOKENS."""
    d_lower = str(difficulty).strip().lower()
    if d_lower in ["dễ", "easy"]:
        return {
            "text": "Dễ",
            "classes": f"bg-emerald-50 text-{TOKENS['srs_easy']} border-emerald-200/80",
            "icon": "sentiment_very_satisfied",
        }
    if d_lower in ["khó", "hard"]:
        return {
            "text": "Khó",
            "classes": f"bg-rose-50 text-{TOKENS['srs_again']} border-rose-200/80",
            "icon": "sentiment_dissatisfied",
        }
    return {
        "text": "Trung bình",
        "classes": f"bg-amber-50 text-{TOKENS['srs_hard']} border-amber-200/80",
        "icon": "sentiment_neutral",
    }


def render_flashcard(
    card_data: Dict[str, Any],
    is_flipped_default: bool = False,
    on_flip_callback: Optional[Callable[[bool], None]] = None,
) -> FlashcardController:
    """Thẻ Flashcard 3D CSS Flip độc lập theo Design System TOKENS.

    - Khung kích thước cố định responsive: w-full max-w-xl h-80 cursor-pointer select-none.
    - Cơ chế Flip 3D (CSS perspective: 1000px & transform-style: preserve-3d, transition-transform duration-500).
    - Nút TTS loa volume_up chỉ hiển thị khi card_data["tts_text"] có giá trị.
    - Sự kiện click.stop trên nút TTS ngăn triệt để sự kiện nổi bọt lên flip container.
    - Mặt trước (Front / Question):
        * Cụm Badge trên cùng: Độ khó (TOKENS), Tag chủ đề (bg-slate-100 text-slate-600).
        * Câu hỏi căn giữa font lớn (text-xl font-bold text-slate-800 text-center).
        * Gợi ý tương tác mờ ở đáy: 'Nhấp hoặc bấm [Space] để xem đáp án'.
    - Mặt sau (Back / Answer):
        * Nhãn 'ĐÁP ÁN' in đậm màu indigo-600.
        * Nội dung đáp án rõ ràng (text-lg font-semibold text-slate-900).
        * Khung giải thích chi tiết (bg-slate-50 rounded-xl p-3 border border-slate-200 text-sm text-slate-600 w-full mt-2).
    """
    ui.add_head_html("""
    <style>
    .perspective-1000 {
        perspective: 1000px;
    }
    .transform-style-preserve-3d {
        transform-style: preserve-3d;
        -webkit-transform-style: preserve-3d;
    }
    .backface-hidden {
        backface-visibility: hidden;
        -webkit-backface-visibility: hidden;
    }
    .rotate-y-180 {
        transform: rotateY(180deg);
    }
    </style>
    """)

    # Trích xuất dữ liệu thẻ card_data
    question_text = card_data.get("question", "Nội dung câu hỏi")
    answer_text = card_data.get("answer", "Nội dung đáp án")
    explanation_text = card_data.get("explanation", "")
    difficulty_meta = _get_difficulty_badge(card_data.get("difficulty", "Trung bình"))

    # Trích xuất thông tin TTS
    tts_text = card_data.get("tts_text")
    tts_lang = card_data.get("tts_lang") or "en-US"
    has_tts = bool(tts_text and str(tts_text).strip())

    # Xử lý danh sách tags hoặc tag đơn từ card_data
    raw_tags = card_data.get("tags")
    tag_list = []
    if isinstance(raw_tags, list):
        for t in raw_tags:
            if isinstance(t, dict):
                name = t.get("name", "")
                if name:
                    tag_list.append(name)
            elif isinstance(t, str) and t.strip():
                tag_list.append(t.strip())
    elif isinstance(raw_tags, str) and raw_tags.strip():
        tag_list = [raw_tags.strip()]
    elif card_data.get("tag"):
        tag_list = [str(card_data.get("tag"))]
    elif card_data.get("deck_name"):
        tag_list = [str(card_data.get("deck_name"))]
    else:
        tag_list = ["Chủ đề chung"]

    is_flipped_state = {"value": bool(is_flipped_default)}

    # Outer Container với CSS Perspective
    with ui.element("div").classes(
        "perspective-1000 w-full max-w-xl h-80 cursor-pointer select-none mx-auto"
    ) as card_outer:

        # Inner 3D Container
        initial_rotate = "rotate-y-180" if is_flipped_default else ""
        with ui.element("div").classes(
            f"transform-style-preserve-3d relative w-full h-full rounded-2xl transition-transform duration-500 {initial_rotate}"
        ) as card_inner:

            # -----------------------------------------------------------
            # MẶT TRƯỚC (FRONT / QUESTION)
            # -----------------------------------------------------------
            with ui.element("div").classes(
                "absolute inset-0 w-full h-full backface-hidden bg-white border border-slate-200/90 "
                "rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow duration-200 flex flex-col justify-between"
            ):
                # Cụm Badge trên cùng: Độ khó (TOKENS) + Tag chủ đề + Nút TTS
                with ui.row().classes("w-full items-center justify-between"):
                    with ui.row().classes("items-center gap-1.5 flex-wrap"):
                        for tag in tag_list:
                            with ui.row().classes(
                                "items-center gap-1 px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200/80 text-xs font-medium"
                            ):
                                ui.icon("label", size="12px").classes("text-slate-400")
                                ui.label(tag)

                    with ui.row().classes("items-center gap-2"):
                        # Nút TTS — chỉ hiển thị khi có tts_text
                        tts_btn_front = ui.button(icon="volume_up").props(
                            "flat round dense size=sm color=indigo-600"
                        )
                        if not has_tts:
                            tts_btn_front.set_visibility(False)

                        with ui.row().classes(
                            f"items-center gap-1 px-2.5 py-0.5 rounded-full border text-xs font-bold {difficulty_meta['classes']}"
                        ):
                            ui.icon(difficulty_meta["icon"], size="14px")
                            ui.label(difficulty_meta["text"])

                # Nội dung câu hỏi căn giữa với font chữ lớn
                with ui.column().classes(
                    "w-full items-center justify-center my-auto text-center px-2 py-4"
                ):
                    ui.label(question_text).classes(
                        "text-xl font-bold text-slate-800 text-center leading-relaxed max-w-lg"
                    )

                # Gợi ý tương tác mờ ở đáy
                with ui.row().classes(
                    "w-full items-center justify-center gap-1.5 text-slate-400 text-xs pt-2 border-t border-slate-100"
                ):
                    ui.icon("touch_app", size="15px")
                    ui.label("Nhấp hoặc bấm")
                    ui.element("kbd").classes(
                        "bg-slate-100 text-slate-600 border border-slate-300 px-1.5 py-0.5 rounded text-[11px] font-mono font-bold"
                    ).text = "Space"
                    ui.label("để xem đáp án")

            # -----------------------------------------------------------
            # MẶT SAU (BACK / ANSWER)
            # -----------------------------------------------------------
            with ui.element("div").classes(
                "absolute inset-0 w-full h-full backface-hidden rotate-y-180 bg-white border border-indigo-200 "
                "rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow duration-200 flex flex-col justify-between"
            ):
                # Header Mặt sau + Nút TTS phía sau
                with ui.row().classes(
                    "w-full items-center justify-between pb-2 border-b border-slate-100"
                ):
                    ui.label("ĐÁP ÁN").classes(
                        "text-xs font-bold text-indigo-600 tracking-wider uppercase"
                    )
                    with ui.row().classes("items-center gap-2"):
                        # Nút TTS trên mặt sau — chỉ hiển thị khi có tts_text
                        tts_btn_back = ui.button(icon="volume_up").props(
                            "flat round dense size=sm color=indigo-600"
                        )
                        if not has_tts:
                            tts_btn_back.set_visibility(False)

                        with ui.row().classes(
                            f"items-center gap-1 px-2 py-0.5 rounded-full border text-xs font-bold {difficulty_meta['classes']}"
                        ):
                            ui.icon(difficulty_meta["icon"], size="12px")
                            ui.label(difficulty_meta["text"])

                # Thân Mặt sau: Nội dung đáp án rõ ràng + Khung giải thích chi tiết
                with ui.column().classes("w-full my-auto gap-2 overflow-y-auto pr-1"):
                    ui.label(answer_text).classes(
                        "text-lg font-semibold text-slate-900 leading-snug"
                    )

                    if explanation_text:
                        with ui.column().classes(
                            "bg-slate-50 rounded-xl p-3 border border-slate-200 text-sm text-slate-600 w-full mt-2"
                        ):
                            with ui.row().classes(
                                "items-center gap-1 text-slate-500 mb-0.5"
                            ):
                                ui.icon("info", size="14px").classes("text-indigo-600")
                                ui.label("Giải thích chi tiết").classes(
                                    "text-xs font-bold uppercase tracking-wider"
                                )
                            ui.label(explanation_text).classes(
                                "text-sm text-slate-600 leading-relaxed font-normal"
                            )

                # Footer Mặt sau: Gợi ý đánh giá SM-2
                with ui.row().classes(
                    "w-full items-center justify-center gap-1.5 pt-2 border-t border-slate-100 text-slate-400 text-xs"
                ):
                    ui.icon("school", size="14px").classes("text-indigo-600")
                    ui.label("Đánh giá độ nhớ bằng các nút [1, 2, 3, 4] bên dưới")

    # -------------------------------------------------------------------
    # Flip logic
    # -------------------------------------------------------------------
    def apply_flip(target_state: bool) -> None:
        """Thực thi lật thẻ và thông báo callback."""
        is_flipped_state["value"] = target_state
        if target_state:
            card_inner.classes(add="rotate-y-180")
        else:
            card_inner.classes(remove="rotate-y-180")

        if on_flip_callback:
            on_flip_callback(target_state)

    def toggle() -> None:
        apply_flip(not is_flipped_state["value"])

    card_outer.on("click", toggle)

    # -------------------------------------------------------------------
    # TTS: Web Speech API — click.stop ngăn event nổi bọt lên flip container
    # -------------------------------------------------------------------
    if has_tts:
        tts_text_safe = str(tts_text).strip()
        tts_lang_safe = str(tts_lang).strip() if tts_lang else "en-US"

        def play_tts(e):  # noqa: ARG001
            js_code = f"""
            (function() {{
                window.speechSynthesis.cancel();
                const utterance = new SpeechSynthesisUtterance({json.dumps(str(tts_text_safe))});
                utterance.lang = {json.dumps(tts_lang_safe)};
                window.speechSynthesis.speak(utterance);
            }})();
            """
            ui.run_javascript(js_code)

        # click.stop ngăn event nổi bọt — không kích hoạt flip 3D
        tts_btn_front.on("click.stop", play_tts)
        tts_btn_back.on("click.stop", play_tts)

    return FlashcardController(
        toggle_func=toggle,
        flip_to_func=apply_flip,
        is_flipped_func=lambda: is_flipped_state["value"],
        element=card_outer,
    )
