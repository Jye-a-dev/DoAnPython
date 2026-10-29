"""
study_stage.py — Khung chứa thẻ Flashcard 3D và cụm điều khiển SM-2 Action Bar.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Dict, Optional
from nicegui import ui
from components.flashcard_view import FlashcardController, render_flashcard
from components.srs_action_bar import render_srs_action_bar


class StudyStage:
    """Điều phối khu vực hiển thị thẻ học và tương tác SM-2."""

    def __init__(
        self,
        on_rating: Callable[[int], Any],
        on_flip_change: Optional[Callable[[bool], None]] = None,
        reverse_mode: bool = False,
        on_edit_note: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.on_rating_cb = on_rating
        self.on_flip_change_cb = on_flip_change
        self.reverse_mode: bool = reverse_mode
        self.on_edit_note_cb = on_edit_note
        self.card_controller: Optional[FlashcardController] = None
        self.current_card_data: Optional[Dict[str, Any]] = None
        self.is_animating: bool = False

        self.container = ui.column().classes("w-full items-center justify-center")
        with self.container:
            self.slot = ui.column().classes(
                "card-transition-wrapper w-full items-center justify-center min-h-[340px] opacity-100 translate-x-0"
            )
            self.action_bar_ref = render_srs_action_bar(
                on_rating_callback=self._handle_rating,
                is_active=True,
                on_space_pressed=self.toggle_flip,
            )

    def set_reverse_mode(self, reverse: bool) -> None:
        """Bật/tắt chế độ đảo ngược và render lại thẻ tức thì."""
        self.reverse_mode = reverse
        if self.current_card_data:
            self.render_card(self.current_card_data)

    def render_card(self, card_data: Dict[str, Any]) -> None:
        """Render thẻ flashcard hiện tại lên giữa màn hình."""
        self.current_card_data = card_data
        self.slot.clear()
        with self.slot:
            self.card_controller = render_flashcard(
                card_data=card_data,
                is_flipped_default=False,
                on_flip_callback=self.on_flip_change_cb,
                reverse_mode=self.reverse_mode,
                on_edit_note=self.on_edit_note_cb,
            )

    def toggle_flip(self) -> None:
        """Lật mặt thẻ qua controller."""
        if self.card_controller:
            self.card_controller.toggle_flip()

    async def _handle_rating(self, rating: int) -> None:
        """Kích hoạt animation chuyển thẻ và gọi callback chấm điểm."""
        if self.is_animating:
            return
        self.is_animating = True
        self.action_bar_ref["set_active"](False)

        # Hiệu ứng trượt thẻ ra ngoài
        self.slot.classes(
            add="opacity-0 -translate-x-8", remove="opacity-100 translate-x-0"
        )
        await asyncio.sleep(0.18)

        # Chuyển xử lý sang callback bên ngoài
        await self.on_rating_cb(rating)

        # Trượt thẻ tiếp theo vào
        self.slot.classes(
            add="opacity-100 translate-x-0", remove="opacity-0 -translate-x-8"
        )
        await asyncio.sleep(0.1)

        self.is_animating = False
        self.action_bar_ref["set_active"](True)

    def hide(self) -> None:
        """Ẩn toàn bộ stage khi kết thúc phiên."""
        self.container.set_visibility(False)


def create_study_stage(
    on_rating: Callable[[int], Any],
    on_flip_change: Optional[Callable[[bool], None]] = None,
    reverse_mode: bool = False,
    on_edit_note: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> StudyStage:
    """Factory khởi tạo StudyStage component."""
    return StudyStage(
        on_rating=on_rating,
        on_flip_change=on_flip_change,
        reverse_mode=reverse_mode,
        on_edit_note=on_edit_note,
    )
