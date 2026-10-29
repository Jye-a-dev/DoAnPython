"""
pomodoro_timer.py — Widget Đồng hồ Pomodoro 25/5 tích hợp cho Focus Mode.
Đếm ngược 25m Focus -> 5m Break, chuông báo Web Audio, Freeze Backdrop Blur nghỉ ngơi chống mỏi mắt.
"""

from __future__ import annotations

from typing import Any, Callable, Optional
from nicegui import ui
from components.layout import show_toast

FOCUS_SECONDS = 25 * 60
BREAK_SECONDS = 5 * 60


class PomodoroTimer:
    """Quản lý trạng thái đếm ngược và thông báo chu kỳ Pomodoro."""

    def __init__(self, on_freeze_change: Optional[Callable[[bool], Any]] = None):
        self.time_left: int = FOCUS_SECONDS
        self.is_running: bool = False
        self.is_break: bool = False
        self.completed_count: int = 0
        self.on_freeze_change_cb = on_freeze_change
        self.timer_label: Optional[ui.label] = None
        self.state_chip: Optional[ui.label] = None
        self.play_btn: Optional[ui.button] = None
        self.blur_overlay: Optional[ui.element] = None
        self._ticker = ui.timer(1.0, callback=self._tick, active=False)

    def _format_time(self) -> str:
        return f"{self.time_left // 60:02d}:{self.time_left % 60:02d}"

    def _tick(self) -> None:
        if self.time_left > 0:
            self.time_left -= 1
            if self.timer_label:
                self.timer_label.text = self._format_time()
        else:
            self._handle_cycle_complete()

    def _play_alarm_sound(self) -> None:
        """Phát âm chuông thông báo nhẹ nhàng thông qua Web Audio API."""
        ui.run_javascript("""
        (function() {
            try {
                const ctx = new (window.AudioContext || window.webkitAudioContext)();
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.type = 'sine';
                osc.frequency.setValueAtTime(587.33, ctx.currentTime);
                osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.3);
                gain.gain.setValueAtTime(0.15, ctx.currentTime);
                gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.8);
                osc.connect(gain); gain.connect(ctx.destination);
                osc.start(); osc.stop(ctx.currentTime + 0.85);
            } catch (err) {}
        })();
        """)

    def _handle_cycle_complete(self) -> None:
        self.is_running = False
        self._ticker.deactivate()
        if self.play_btn:
            self.play_btn.props("icon=play_arrow")

        self._play_alarm_sound()

        if not self.is_break:
            self.completed_count += 1
            self.is_break = True
            self.time_left = BREAK_SECONDS
            self._set_freeze(True)
            show_toast(
                "🍅 Hoàn thành 25 phút tập trung! Hãy nghỉ ngơi 5 phút chống mỏi mắt.",
                "positive",
            )
        else:
            self.is_break = False
            self.time_left = FOCUS_SECONDS
            self._set_freeze(False)
            show_toast(
                "Hết 5 phút nghỉ ngơi. Sẵn sàng cho chu kỳ tập trung tiếp theo!", "info"
            )

        self._update_ui_state()

    def _set_freeze(self, frozen: bool) -> None:
        if self.blur_overlay:
            self.blur_overlay.set_visibility(frozen)
        if self.on_freeze_change_cb:
            self.on_freeze_change_cb(frozen)

    def toggle_play(self) -> None:
        self.is_running = not self.is_running
        if self.is_running:
            self._ticker.activate()
            if self.play_btn:
                self.play_btn.props("icon=pause")
        else:
            self._ticker.deactivate()
            if self.play_btn:
                self.play_btn.props("icon=play_arrow")

    def reset_timer(self) -> None:
        self.is_running = False
        self._ticker.deactivate()
        self.time_left = BREAK_SECONDS if self.is_break else FOCUS_SECONDS
        if self.play_btn:
            self.play_btn.props("icon=play_arrow")
        if self.timer_label:
            self.timer_label.text = self._format_time()

    def skip_phase(self) -> None:
        self.is_break = not self.is_break
        self.time_left = BREAK_SECONDS if self.is_break else FOCUS_SECONDS
        self._set_freeze(self.is_break)
        self._update_ui_state()

    def _update_ui_state(self) -> None:
        if self.timer_label:
            self.timer_label.text = self._format_time()
        if self.state_chip:
            if self.is_break:
                self.state_chip.text = f"Nghỉ ngơi ☕ (#{self.completed_count})"
                self.state_chip.classes(
                    replace="bg-emerald-50 text-emerald-700 border-emerald-200"
                )
            else:
                self.state_chip.text = f"Tập trung 🎯 (#{self.completed_count})"
                self.state_chip.classes(
                    replace="bg-rose-50 text-rose-700 border-rose-200"
                )


def render_pomodoro_widget(
    on_freeze_change: Optional[Callable[[bool], Any]] = None,
) -> PomodoroTimer:
    """Render widget Pomodoro nhỏ gọn trên thanh điều khiển Focus Mode."""
    pomo = PomodoroTimer(on_freeze_change=on_freeze_change)
    with ui.row().classes(
        "items-center gap-1 px-2.5 py-1 bg-white border border-slate-200 rounded-full shadow-2xs"
    ):
        pomo.state_chip = ui.label("Tập trung 🎯").classes(
            "text-[10px] font-extrabold px-1.5 py-0.5 rounded-full border bg-rose-50 text-rose-700 border-rose-200 uppercase"
        )
        pomo.timer_label = ui.label("25:00").classes(
            "text-xs font-mono font-black text-slate-800 tracking-wider min-w-[38px] text-center"
        )
        pomo.play_btn = (
            ui.button(icon="play_arrow", on_click=pomo.toggle_play)
            .props("flat round dense size=xs color=indigo")
            .tooltip("Bắt đầu / Tạm dừng")
        )
        ui.button(icon="replay", on_click=pomo.reset_timer).props(
            "flat round dense size=xs color=slate-6"
        ).tooltip("Đặt lại 25m")
        ui.button(icon="skip_next", on_click=pomo.skip_phase).props(
            "flat round dense size=xs color=slate-6"
        ).tooltip("Chuyển chu kỳ")

    # Màn hình Backdrop Blur khi Freeze nghỉ ngơi 5 phút
    overlay = ui.element("div").classes(
        "fixed inset-0 z-50 backdrop-blur-md bg-slate-900/60 flex flex-col items-center justify-center p-6 text-center select-none"
    )
    overlay.set_visibility(False)
    pomo.blur_overlay = overlay
    with overlay:
        with ui.card().classes(
            "max-w-md p-8 rounded-3xl bg-white shadow-2xl items-center gap-4 border border-slate-100"
        ):
            ui.icon("spa", size="48px").classes("text-emerald-500 animate-pulse")
            ui.label("Giờ Nghỉ Ngơi Pomodoro (5 Phút)").classes(
                "text-xl font-black text-slate-900"
            )
            ui.label(
                "Bạn đã hoàn thành 25 phút tập trung! Hãy phóng tầm mắt ra xa và thư giãn mắt."
            ).classes("text-xs text-slate-500 leading-relaxed")
            ui.button(
                "Tiếp tục học ngay",
                icon="play_arrow",
                on_click=lambda: (pomo._set_freeze(False), pomo.skip_phase()),
            ).classes(
                "bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs px-5 py-2.5 rounded-xl"
            )

    return pomo
