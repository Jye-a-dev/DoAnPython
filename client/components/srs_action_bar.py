import asyncio
import inspect
from typing import Any, Callable, Dict, Optional
from nicegui import events, ui


def render_srs_action_bar(
    on_rating_callback: Callable[[int], Any],
    is_active: bool = True,
    on_space_pressed: Optional[Callable[[], Any]] = None,
    on_flip_callback: Optional[Callable[[], Any]] = None,
) -> Dict[str, Any]:
    """Bộ nút đánh giá SM-2 & Keyboard Hotkeys chuẩn Semantic SRS Tokens.

    - 4 Nút chấm điểm chuẩn:
        * Nút 1: Học lại (bg-red-500 hover:bg-red-600 text-white, icon replay)
        * Nút 2: Khó (bg-amber-500 hover:bg-amber-600 text-white, icon sentiment_dissatisfied)
        * Nút 3: Tốt (bg-blue-600 hover:bg-blue-700 text-white, icon sentiment_satisfied)
        * Nút 4: Dễ (bg-emerald-600 hover:bg-emerald-700 text-white, icon sentiment_very_satisfied)
        * Shortcut tag: <kbd class="bg-black/20 px-1.5 py-0.5 rounded text-xs">1</kbd>
    - Keyboard Hotkeys:
        * Lắng nghe bàn phím qua ui.keyboard(on_key=...)
        * Phím 1, 2, 3, 4: kích hoạt on_rating_callback(rating) khi is_active=True
        * Phím Space: kích hoạt on_space_pressed() để lật mặt thẻ
    """
    flip_handler = on_space_pressed or on_flip_callback

    srs_buttons = [
        {
            "rating": 1,
            "label": "Học lại",
            "key": "1",
            "icon": "replay",
            "classes": "bg-red-500 hover:bg-red-600 text-white",
            "interval": "< 1 phút",
        },
        {
            "rating": 2,
            "label": "Khó",
            "key": "2",
            "icon": "sentiment_dissatisfied",
            "classes": "bg-amber-500 hover:bg-amber-600 text-white",
            "interval": "10 phút",
        },
        {
            "rating": 3,
            "label": "Tốt",
            "key": "3",
            "icon": "sentiment_satisfied",
            "classes": "bg-blue-600 hover:bg-blue-700 text-white",
            "interval": "1 ngày",
        },
        {
            "rating": 4,
            "label": "Dễ",
            "key": "4",
            "icon": "sentiment_very_satisfied",
            "classes": "bg-emerald-600 hover:bg-emerald-700 text-white",
            "interval": "4 ngày",
        },
    ]

    action_state = {"is_active": is_active}

    def trigger_rating(rating: int):
        if not action_state["is_active"]:
            return
        if on_rating_callback:
            res = on_rating_callback(rating)
            if inspect.isawaitable(res):
                asyncio.ensure_future(res)

    def trigger_flip():
        if not action_state["is_active"]:
            return
        if flip_handler:
            res = flip_handler()
            if inspect.isawaitable(res):
                asyncio.ensure_future(res)

    def handle_key(e: events.KeyEventArguments):
        if not action_state["is_active"]:
            return
        if not e.action.keydown or e.action.repeat:
            return

        # Phím Space để lật mặt thẻ
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

        # Phím 1, 2, 3, 4 để chấm điểm SRS
        key_name = str(getattr(e.key, "name", e.key)).strip()
        if key_name in ["1", "2", "3", "4"]:
            trigger_rating(int(key_name))

    # Lắng nghe bàn phím
    keyboard_listener = ui.keyboard(
        on_key=handle_key,
        active=is_active,
        repeating=False,
    )

    with ui.column().classes(
        "w-full max-w-xl mx-auto items-center gap-3 select-none"
    ) as container:
        # Nhóm 4 nút đánh giá SRS
        with ui.row().classes("w-full justify-center items-center gap-2.5"):
            for item in srs_buttons:
                with ui.button(
                    on_click=lambda r=item["rating"]: trigger_rating(r)
                ).classes(
                    f"{item['classes']} flex-1 px-3 py-2.5 rounded-xl shadow-sm transition-all duration-150 "
                    "flex flex-col items-center justify-center gap-1 cursor-pointer"
                ):
                    with ui.row().classes("items-center gap-1.5"):
                        ui.icon(item["icon"], size="18px")
                        ui.label(item["label"]).classes("font-bold text-sm")

                    with ui.row().classes(
                        "items-center gap-1 text-[11px] opacity-90 leading-none"
                    ):
                        ui.html(
                            f'<kbd class="bg-black/20 px-1.5 py-0.5 rounded text-xs">{item["key"]}</kbd>'
                        )
                        ui.label(item["interval"]).classes("text-[10px] font-medium")

        # Gợi ý phím tắt tiện ích
        with ui.row().classes("items-center gap-2 text-[11px] text-slate-400 mt-1"):
            ui.icon("keyboard", size="14px")
            ui.label(
                "Phím tắt: [Space] Lật thẻ  •  [1] Học lại  •  [2] Khó  •  [3] Tốt  •  [4] Dễ"
            )

    return {
        "set_active": lambda active: action_state.update({"is_active": active}),
        "keyboard": keyboard_listener,
        "container": container,
    }
