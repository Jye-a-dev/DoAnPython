from datetime import datetime
from typing import Any, Callable, Dict, Optional
from nicegui import ui

from components.layout import TOKENS, show_toast
from components.flashcard_view import render_flashcard, FlashcardController
from components.srs_action_bar import render_srs_action_bar


class InteractiveDemoController:
    """Bộ điều khiển Live Preview thẻ 3D và thanh trạng thái SM-2."""

    def __init__(
        self,
        update_card_func: Callable[[Dict[str, Any]], None],
        update_log_func: Callable[[str], None],
    ):
        self._update_card = update_card_func
        self._update_log = update_log_func

    def update_card(self, card_data: Dict[str, Any]) -> None:
        """Cập nhật nội dung thẻ hiển thị trên Live Preview."""
        self._update_card(card_data)

    def log(self, message: str) -> None:
        """Cập nhật dòng thông báo nhật ký trạng thái SM-2."""
        self._update_log(message)


def render_interactive_demo(
    initial_card: Optional[Dict[str, Any]] = None,
) -> InteractiveDemoController:
    """Khối Interactive Demo & Spaced Repetition (SM-2 Preview).

    - Thẻ Flashcard 3D lật mặt mượt mà qua click chuột hoặc phím [Space]
    - Thanh 4 nút đánh giá SM-2 (1: Học lại, 2: Khó, 3: Tốt, 4: Dễ) kèm hotkeys [1]-[4]
    - Khung nhật ký ghi nhận chu kỳ nhớ thời gian thực
    """
    default_card = {
        "id": "card-demo-01",
        "question": "Thuật toán SM-2 (SuperMemo 2) là gì và đóng vai trò gì trong ứng dụng EdTech?",
        "answer": "SM-2 là thuật toán tính toán khoảng cách lặp lại ngắt quãng (Spaced Repetition) tối ưu dựa trên đường cong lãng quên của Ebbinghaus.",
        "explanation": "Thuật toán tính toán hệ số Ease Factor (EF) và khoảng cách Interval (ngày) sau mỗi lần đánh giá (1: Again, 2: Hard, 3: Good, 4: Easy), giúp tối đa hóa khả năng lưu giữ kiến thức lâu dài với số lần ôn tập tối thiểu.",
        "hint": "Gợi ý: Thuật toán điều chỉnh hệ số dễ (Ease Factor) và khoảng cách ngắt quãng theo 4 mức độ nhớ.",
        "deck_name": "Kiến Trúc Spaced Repetition",
        "difficulty": "Trung bình",
        "review_count": 3,
    }
    active_card_data = initial_card or default_card
    card_controller_ref: Dict[str, Optional[FlashcardController]] = {"ctrl": None}

    with ui.element("div").props('id="demo-section"').classes("w-full mt-20 scroll-mt-24"):
        with ui.column().classes("w-full max-w-4xl mx-auto items-center gap-6"):
            # Tiêu đề phân khu Live Preview
            with ui.column().classes("text-center items-center gap-2"):
                with ui.row().classes(
                    f"items-center gap-2 px-3.5 py-1 rounded-full bg-{TOKENS['primary_light']} border border-indigo-200/80"
                ):
                    ui.icon("play_circle", size="16px").classes(f"text-{TOKENS['primary']}")
                    ui.label("Live Interactive Preview").classes(
                        f"text-xs font-bold uppercase tracking-wider text-{TOKENS['primary']}"
                    )
                ui.label("Trải nghiệm Flashcard 3D & Khoa học ghi nhớ SM-2").classes(
                    f"text-2xl md:text-3xl font-extrabold text-{TOKENS['text_primary']} tracking-tight"
                )
                ui.label(
                    "Thẻ lật mặt (Flip 3D) khi nhấp chuột hoặc bấm phím [Space]. Đánh giá khả năng nhớ bằng 4 phím tắt [1], [2], [3], [4]."
                ).classes(f"text-sm text-{TOKENS['text_secondary']} max-w-xl")

            # Container Live Preview
            with ui.card().classes(
                f"w-full bg-{TOKENS['bg_card']} border border-{TOKENS['border']} rounded-3xl p-6 md:p-8 shadow-sm items-center gap-6"
            ):
                # Khung hiển thị nhật ký tương tác SM-2
                srs_log_container = ui.column().classes("w-full max-w-2xl mx-auto")

                def update_srs_log(message: str) -> None:
                    srs_log_container.clear()
                    with srs_log_container:
                        with ui.row().classes(
                            "w-full items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-200/80 text-xs"
                        ):
                            with ui.row().classes("items-center gap-2"):
                                ui.icon("history", size="16px").classes(f"text-{TOKENS['primary']}")
                                ui.label("Trạng thái:").classes("font-bold text-slate-700")
                                ui.label(message).classes("font-medium text-slate-600")
                            now_str = datetime.now().strftime("%H:%M:%S")
                            ui.label(now_str).classes("text-slate-400 font-mono")

                def on_card_flipped(is_flipped: bool) -> None:
                    state_str = "Mặt sau (Đáp án)" if is_flipped else "Mặt trước (Câu hỏi)"
                    update_srs_log(f"Đã lật thẻ sang: {state_str}")

                def on_srs_rating(rating: int) -> None:
                    rating_labels = {
                        1: ("Học lại", "negative", "< 1 phút"),
                        2: ("Khó", "warning", "10 phút"),
                        3: ("Tốt", "info", "1 ngày"),
                        4: ("Dễ", "positive", "4 ngày"),
                    }
                    label, cat, interval = rating_labels.get(rating, ("Không rõ", "info", ""))
                    show_toast(f"Đánh giá SM-2: Phím [{rating}] {label} — Chu kỳ mới: {interval}", cat)
                    update_srs_log(f"Đánh giá phím [{rating}] {label} — Chu kỳ ôn tập kế tiếp: {interval}")

                # Vùng hiển thị thẻ Flashcard động
                flashcard_host = ui.column().classes("w-full items-center")

                def render_card_slot(card_dict: Dict[str, Any]) -> None:
                    flashcard_host.clear()
                    with flashcard_host:
                        ctrl = render_flashcard(
                            card_data=card_dict,
                            is_flipped_default=False,
                            on_flip_callback=on_card_flipped,
                        )
                        card_controller_ref["ctrl"] = ctrl

                render_card_slot(active_card_data)

                # Bộ nút đánh giá SM-2 kèm phím tắt
                render_srs_action_bar(
                    on_rating_callback=on_srs_rating,
                    is_active=True,
                    on_flip_callback=lambda: card_controller_ref["ctrl"].toggle_flip() if card_controller_ref["ctrl"] else None,
                )

                update_srs_log("Sẵn sàng. Nhấn [Space] để lật thẻ hoặc bấm phím [1]-[4] để đánh giá chu kỳ nhớ.")

    return InteractiveDemoController(
        update_card_func=render_card_slot,
        update_log_func=update_srs_log,
    )

