import asyncio
import inspect
from typing import Any, Callable, Dict, Optional
from nicegui import events, ui
from components.layout import TOKENS, show_toast


def render_srs_action_bar(
    on_rating_callback: Callable[[int], Any],
    is_active: bool = True,
    on_flip_callback: Optional[Callable[[], Any]] = None,
) -> Dict[str, Any]:
    """Component Bộ nút đánh giá SM-2 & Hotkeys bàn phím chuẩn EdTech Tokens.

    - 4 Nút đánh giá SM-2:
        * Phím 1: Học lại (bg-red-500 hover:bg-red-600, icon: replay, khoảng cách < 1 phút)
        * Phím 2: Khó (bg-amber-500 hover:bg-amber-600, icon: sentiment_dissatisfied, khoảng cách 10 phút)
        * Phím 3: Tốt (bg-blue-600 hover:bg-blue-700, icon: sentiment_satisfied, khoảng cách 1 ngày)
        * Phím 4: Dễ (bg-emerald-600 hover:bg-emerald-700, icon: sentiment_very_satisfied, khoảng cách 4 ngày)
    - Keyboard Hotkeys:
        * Lắng nghe qua ui.keyboard(on_key=...)
        * Phím 1, 2, 3, 4: Kích hoạt on_rating_callback(rating)
        * Phím Space: Kích hoạt on_flip_callback()
    """
    srs_buttons_config = [
        {
            "rating": 1,
            "label": "Học lại",
            "key": "1",
            "icon": "replay",
            "bg": "bg-red-500 hover:bg-red-600 active:bg-red-700",
            "interval": "< 1 phút",
            "desc": "Quên hoàn toàn",
        },
        {
            "rating": 2,
            "label": "Khó",
            "key": "2",
            "icon": "sentiment_dissatisfied",
            "bg": "bg-amber-500 hover:bg-amber-600 active:bg-amber-700",
            "interval": "10 phút",
            "desc": "Nhớ khó khăn",
        },
        {
            "rating": 3,
            "label": "Tốt",
            "key": "3",
            "icon": "sentiment_satisfied",
            "bg": "bg-blue-600 hover:bg-blue-700 active:bg-blue-800",
            "interval": "1 ngày",
            "desc": "Nhớ sau do dự",
        },
        {
            "rating": 4,
            "label": "Dễ",
            "key": "4",
            "icon": "sentiment_very_satisfied",
            "bg": "bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800",
            "interval": "4 ngày",
            "desc": "Nhớ ngay lập tức",
        },
    ]

    action_state = {"is_active": is_active}

    def trigger_rating(rating: int):
        """Kích hoạt rating khi click chuột hoặc bấm phím 1-4."""
        if not action_state["is_active"]:
            return
        if on_rating_callback:
            res = on_rating_callback(rating)
            if inspect.isawaitable(res):
                asyncio.create_task(res)

    def trigger_flip():
        """Kích hoạt lật thẻ khi click nút lật hoặc bấm phím Space."""
        if not action_state["is_active"]:
            return
        if on_flip_callback:
            res = on_flip_callback()
            if inspect.isawaitable(res):
                asyncio.create_task(res)

    # Xử lý sự kiện bàn phím Hotkeys
    def handle_key(e: events.KeyEventArguments):
        if not action_state["is_active"]:
            return
        # Chỉ xử lý khi keydown và không phải key lặp giữ phím
        if not e.action.keydown or e.action.repeat:
            return

        # Phím Space để lật thẻ
        is_space = False
        if hasattr(e.key, "space") and e.key.space:
            is_space = True
        elif hasattr(e.key, "name") and e.key.name in [" ", "Space"]:
            is_space = True
        elif isinstance(e.key, str) and e.key in [" ", "Space"]:
            is_space = True

        if is_space:
            trigger_flip()
            return

        # Phím 1, 2, 3, 4 để đánh giá SM-2
        key_name = str(getattr(e.key, "name", e.key)).strip()
        if key_name in ["1", "2", "3", "4"]:
            trigger_rating(int(key_name))

    # Đăng ký listener bàn phím với NiceGUI
    keyboard_listener = ui.keyboard(
        on_key=handle_key,
        active=is_active,
        repeating=False,
    )

    # Giao diện Action Bar
    with ui.column().classes("w-full max-w-2xl mx-auto items-center gap-3 select-none") as bar_container:
        # Hàng nút phụ: Lật mặt thẻ [Space]
        if on_flip_callback:
            with ui.row().classes("w-full justify-center mb-1"):
                with ui.button(on_click=trigger_flip).classes(
                    "bg-white hover:bg-slate-50 text-slate-700 border border-slate-200/90 "
                    "px-4 py-1.5 rounded-xl text-xs font-semibold shadow-2xs transition-all duration-150 "
                    "flex items-center gap-2 group"
                ):
                    ui.icon("flip", size="16px").classes(
                        f"text-{TOKENS['primary']} group-hover:rotate-180 transition-transform duration-300"
                    )
                    ui.label("Lật mặt thẻ")
                    ui.element("kbd").classes(
                        "bg-slate-100 text-slate-600 border border-slate-300 px-1.5 py-0.5 rounded text-[10px] font-mono font-bold"
                    ).text = "Space"

        # Hàng 4 nút đánh giá SM-2
        with ui.row().classes("w-full justify-center items-center gap-2 md:gap-3 flex-wrap"):
            for btn in srs_buttons_config:
                with ui.button(
                    on_click=lambda r=btn["rating"]: trigger_rating(r)
                ).classes(
                    f"{btn['bg']} text-white px-3.5 md:px-5 py-3 rounded-2xl shadow-sm hover:shadow-md "
                    "transition-all duration-150 flex flex-col items-center justify-center gap-1 "
                    "min-w-[105px] md:min-w-[130px] flex-1 max-w-[155px]"
                ):
                    # Icon và Tên nút
                    with ui.row().classes("items-center gap-1.5"):
                        ui.icon(btn["icon"], size="18px")
                        ui.label(btn["label"]).classes("font-bold text-sm")

                    # Gợi ý phím tắt & Chu kỳ ôn tiếp theo
                    with ui.row().classes("items-center gap-1 text-[11px] opacity-90 leading-none"):
                        ui.element("kbd").classes(
                            "bg-black/25 px-1 py-0.5 rounded text-[10px] font-mono font-bold tracking-wider"
                        ).text = f"[{btn['key']}]"
                        ui.label(btn["interval"]).classes("text-[10px] font-medium")

        # Gợi ý phím tắt tổng thể
        with ui.row().classes("items-center gap-2 text-[11px] text-slate-400 mt-1"):
            ui.icon("keyboard", size="14px")
            ui.label("Phím tắt nhanh: [Space] Lật thẻ  •  [1] Học lại  •  [2] Khó  •  [3] Tốt  •  [4] Dễ")

    return {
        "set_active": lambda active: action_state.update({"is_active": active}),
        "keyboard": keyboard_listener,
        "container": bar_container,
    }

