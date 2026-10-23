from typing import Any, Callable, Dict, Optional
from nicegui import ui
from components.layout import TOKENS


class FlashcardController:
    """Điều khiển trạng thái lật và hiển thị của Flashcard."""

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
        """Chuyển thẻ sang mặt mong muốn (True: Mặt sau / Answer; False: Mặt trước / Question)."""
        self._flip_to(target_state)

    @property
    def is_flipped(self) -> bool:
        """Kiểm tra thẻ hiện có đang ở mặt sau không."""
        return self._is_flipped()


def _get_difficulty_badge_style(difficulty: str) -> Dict[str, str]:
    """Xác định màu sắc và style của badge độ khó theo TOKENS."""
    d_lower = str(difficulty).strip().lower()
    if d_lower in ["dễ", "easy"]:
        return {
            "text": "Dễ",
            "classes": "bg-emerald-50 text-emerald-700 border-emerald-200/80",
            "icon": "sentiment_very_satisfied",
        }
    if d_lower in ["khó", "hard"]:
        return {
            "text": "Khó",
            "classes": "bg-rose-50 text-rose-700 border-rose-200/80",
            "icon": "sentiment_dissatisfied",
        }
    return {
        "text": "Trung bình",
        "classes": "bg-amber-50 text-amber-700 border-amber-200/80",
        "icon": "sentiment_neutral",
    }


def render_flashcard(
    card_data: Dict[str, Any],
    is_flipped_default: bool = False,
    on_flip_callback: Optional[Callable[[bool], None]] = None,
) -> FlashcardController:
    """Component Flashcard 3D Flip & Badge Metadata theo phong cách EdTech Clean Minimalist.

    - Chế độ Flip 3D (CSS perspective: 1000px & transform-style: preserve-3d):
        * Nhấp vào thẻ hoặc gọi controller.toggle_flip() để xoay 180 độ.
        * Mặt trước (Question): Câu hỏi trung tâm text-xl font-bold text-slate-800, badge chủ đề/tag, hint mở rộng.
        * Mặt sau (Answer): Đáp án in đậm, hộp giải thích chi tiết bg-slate-50 border border-slate-100 text-slate-600.
    - Badge góc trên: Độ khó (Dễ / Trung bình / Khó) và số lượt ôn (review_count).
    """
    # Nhúng CSS 3D Flip
    ui.add_head_html(
        """
    <style>
    .perspective-1000 {
        perspective: 1000px;
    }
    .transform-style-preserve-3d {
        transform-style: preserve-3d;
        -webkit-transform-style: preserve-3d;
        transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .backface-hidden {
        backface-visibility: hidden;
        -webkit-backface-visibility: hidden;
    }
    .rotate-y-180 {
        transform: rotateY(180deg);
    }
    </style>
    """
    )

    # Dữ liệu thẻ
    question_text = card_data.get("question", "Chưa có nội dung câu hỏi")
    answer_text = card_data.get("answer", "Chưa có nội dung đáp án")
    explanation_text = card_data.get("explanation", "")
    hint_text = card_data.get("hint", "")
    tag_text = card_data.get("tag") or card_data.get("deck_name") or "Chung"
    review_count = card_data.get("review_count", 0)
    difficulty_meta = _get_difficulty_badge_style(card_data.get("difficulty", "Trung bình"))

    # Trạng thái lật mặt
    is_flipped_state = {"value": bool(is_flipped_default)}

    # Outer Container với CSS Perspective
    with ui.element("div").classes(
        "perspective-1000 w-full max-w-2xl mx-auto min-h-[380px] cursor-pointer select-none group"
    ) as card_outer:

        # Inner 3D Container
        initial_flip_class = "rotate-y-180" if is_flipped_default else ""
        with ui.element("div").classes(
            f"transform-style-preserve-3d relative w-full h-full min-h-[380px] rounded-3xl {initial_flip_class}"
        ) as card_inner:

            # ---------------------------------------------------------------
            # MẶT TRƯỚC (QUESTION)
            # ---------------------------------------------------------------
            with ui.element("div").classes(
                "absolute inset-0 w-full h-full backface-hidden bg-white border border-slate-200/90 "
                "rounded-3xl p-7 shadow-md flex flex-col justify-between hover:shadow-xl hover:border-indigo-200 "
                "transition-all duration-300"
            ):
                # Header Bar Mặt trước
                with ui.row().classes("w-full items-center justify-between pb-3 border-b border-slate-100"):
                    # Tag / Topic Badge
                    with ui.row().classes(
                        f"items-center gap-1.5 px-3 py-1 rounded-full bg-{TOKENS['primary_light']} "
                        f"text-{TOKENS['primary']} border border-indigo-200/60"
                    ):
                        ui.icon("label", size="14px")
                        ui.label(tag_text).classes("text-xs font-bold")

                    # Metadata Badges (Difficulty & Review count)
                    with ui.row().classes("items-center gap-2"):
                        with ui.row().classes(
                            f"items-center gap-1 px-2.5 py-1 rounded-full border text-xs font-bold {difficulty_meta['classes']}"
                        ):
                            ui.icon(difficulty_meta["icon"], size="14px")
                            ui.label(difficulty_meta["text"])

                        with ui.row().classes(
                            "items-center gap-1 px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 border border-slate-200 text-xs font-semibold"
                        ):
                            ui.icon("repeat", size="14px")
                            ui.label(f"Lượt ôn: {review_count}")

                # Question Body
                with ui.column().classes("w-full items-center justify-center my-auto px-4 py-6 text-center gap-3"):
                    ui.label("CÂU HỎI").classes(
                        f"text-[11px] font-extrabold uppercase tracking-widest text-{TOKENS['primary']}"
                    )
                    ui.label(question_text).classes(
                        "text-xl md:text-2xl font-bold text-slate-800 leading-relaxed max-w-xl"
                    )

                # Footer Bar Mặt trước (Hint & Instructions)
                with ui.column().classes("w-full gap-2 pt-3 border-t border-slate-100"):
                    if hint_text:
                        with ui.expansion("Gợi ý trợ giúp", icon="lightbulb").props("dense").classes(
                            "w-full bg-amber-50/70 text-amber-900 rounded-xl px-3 border border-amber-200/60 text-xs font-medium"
                        ) as hint_expansion:
                            # Ngăn chặn event click của expansion lan truyền làm lật thẻ
                            hint_expansion.on("click.stop", lambda: None)
                            ui.label(hint_text).classes("text-xs text-amber-800 leading-normal py-1")

                    with ui.row().classes("w-full items-center justify-center gap-1.5 text-slate-400 text-xs"):
                        ui.icon("touch_app", size="16px")
                        ui.label("Nhấp thẻ hoặc nhấn").classes("text-xs")
                        ui.element("kbd").classes(
                            "bg-slate-100 text-slate-600 border border-slate-300 px-1.5 py-0.5 rounded text-[11px] font-mono font-bold"
                        ).text = "Space"
                        ui.label("để xem đáp án").classes("text-xs")

            # ---------------------------------------------------------------
            # MẶT SAU (ANSWER)
            # ---------------------------------------------------------------
            with ui.element("div").classes(
                "absolute inset-0 w-full h-full backface-hidden rotate-y-180 bg-white border border-indigo-200 "
                "rounded-3xl p-7 shadow-md flex flex-col justify-between hover:shadow-xl transition-all duration-300"
            ):
                # Header Bar Mặt sau
                with ui.row().classes("w-full items-center justify-between pb-3 border-b border-slate-100"):
                    with ui.row().classes(
                        "items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold text-xs"
                    ):
                        ui.icon("check_circle", size="14px")
                        ui.label("ĐÁP ÁN CHUẨN").classes("text-xs font-bold")

                    with ui.row().classes("items-center gap-2"):
                        with ui.row().classes(
                            f"items-center gap-1 px-2.5 py-1 rounded-full border text-xs font-bold {difficulty_meta['classes']}"
                        ):
                            ui.icon(difficulty_meta["icon"], size="14px")
                            ui.label(difficulty_meta["text"])

                        with ui.row().classes(
                            "items-center gap-1 px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 border border-slate-200 text-xs font-semibold"
                        ):
                            ui.icon("repeat", size="14px")
                            ui.label(f"Lượt ôn: {review_count}")

                # Answer & Explanation Body
                with ui.column().classes("w-full my-auto px-2 py-4 gap-4"):
                    with ui.column().classes("w-full items-center text-center gap-1"):
                        ui.label("NỘI DUNG ĐÁP ÁN").classes(
                            "text-[11px] font-extrabold uppercase tracking-widest text-emerald-600"
                        )
                        ui.label(answer_text).classes(
                            "text-xl md:text-2xl font-extrabold text-slate-900 leading-snug"
                        )

                    # Hộp giải thích chi tiết
                    if explanation_text:
                        with ui.column().classes(
                            "w-full bg-slate-50 rounded-xl p-4 border border-slate-100 text-slate-600 gap-1"
                        ):
                            with ui.row().classes("items-center gap-1.5"):
                                ui.icon("info", size="16px").classes(f"text-{TOKENS['primary']}")
                                ui.label("Giải thích chi tiết:").classes(
                                    f"text-xs font-bold uppercase tracking-wider text-{TOKENS['text_secondary']}"
                                )
                            ui.label(explanation_text).classes(
                                "text-sm text-slate-600 leading-relaxed font-normal"
                            )

                # Footer Bar Mặt sau (SRS Guidance)
                with ui.row().classes(
                    "w-full items-center justify-center gap-1.5 pt-3 border-t border-slate-100 text-slate-400 text-xs"
                ):
                    ui.icon("school", size="16px").classes(f"text-{TOKENS['primary']}")
                    ui.label("Đánh giá độ nhớ bằng thanh SRS bên dưới hoặc phím tắt").classes("text-xs")
                    ui.element("kbd").classes(
                        "bg-slate-100 text-slate-600 border border-slate-300 px-1 py-0.5 rounded text-[10px] font-mono font-bold"
                    ).text = "1"
                    ui.element("kbd").classes(
                        "bg-slate-100 text-slate-600 border border-slate-300 px-1 py-0.5 rounded text-[10px] font-mono font-bold"
                    ).text = "2"
                    ui.element("kbd").classes(
                        "bg-slate-100 text-slate-600 border border-slate-300 px-1 py-0.5 rounded text-[10px] font-mono font-bold"
                    ).text = "3"
                    ui.element("kbd").classes(
                        "bg-slate-100 text-slate-600 border border-slate-300 px-1 py-0.5 rounded text-[10px] font-mono font-bold"
                    ).text = "4"

    def apply_flip(target_state: bool) -> None:
        """Thực thi lật thẻ và kích hoạt callback."""
        is_flipped_state["value"] = target_state
        if target_state:
            card_inner.classes(add="rotate-y-180")
        else:
            card_inner.classes(remove="rotate-y-180")

        if on_flip_callback:
            on_flip_callback(target_state)

    def toggle() -> None:
        """Đảo ngược trạng thái hiện tại."""
        apply_flip(not is_flipped_state["value"])

    # Click trực tiếp lên thẻ để lật
    card_outer.on("click", toggle)

    return FlashcardController(
        toggle_func=toggle,
        flip_to_func=apply_flip,
        is_flipped_func=lambda: is_flipped_state["value"],
        element=card_outer,
    )

