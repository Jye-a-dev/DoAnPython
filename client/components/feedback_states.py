from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Optional
from nicegui import ui

logger = logging.getLogger(__name__)


def network_error_banner(
    on_retry: Optional[Callable[[], Any]] = None,
    message: str = "Không thể kết nối đến máy chủ Backend (Port 3000). Vui lòng kiểm tra lại tiến trình.",
) -> ui.row:
    """Banner thông báo lỗi kết nối Backend API kèm nút Thử lại không crash NiceGUI."""
    with ui.row().classes(
        "w-full items-center justify-between bg-amber-50 border border-amber-200 text-amber-900 rounded-2xl p-4 shadow-sm transition-all duration-200 gap-4"
    ) as banner:
        with ui.row().classes("items-center gap-3 flex-1"):
            with ui.element("div").classes(
                "w-10 h-10 rounded-xl bg-amber-100 flex items-center justify-center text-amber-700 shrink-0"
            ):
                ui.icon("wifi_off", size="22px")
            with ui.column().classes("gap-0.5"):
                ui.label("Lỗi kết nối máy chủ").classes(
                    "text-xs font-bold uppercase tracking-wider text-amber-800"
                )
                ui.label(message).classes(
                    "text-sm font-medium text-amber-900 leading-snug"
                )

        async def _handle_retry() -> None:
            try:
                if on_retry is not None:
                    if asyncio.iscoroutinefunction(on_retry):
                        await on_retry()
                    else:
                        res = on_retry()
                        if asyncio.iscoroutine(res):
                            await res
                else:
                    ui.navigate.reload()
            except Exception as exc:
                logger.error("Lỗi khi thử lại fetch API: %s", exc)

        ui.button(
            "Thử lại",
            icon="refresh",
            on_click=_handle_retry,
        ).classes(
            "bg-amber-600 hover:bg-amber-700 text-white font-bold rounded-xl px-4 py-2 shadow-sm text-xs cursor-pointer transition-all duration-150 shrink-0"
        )

    return banner


def empty_deck_state(
    title: str = "Bạn chưa có bài học hoặc thẻ ghi nhớ nào!",
    description: Optional[str] = (
        "Hãy nạp tài liệu bài học hoặc dán nội dung vào Studio để AI tự động trích xuất bộ Flashcard đầu tiên."
    ),
    icon: str = "auto_stories",
    action_text: str = "Tạo bài học mới",
    action_url: str = "/",
    secondary_text: Optional[str] = None,
    secondary_url: Optional[str] = None,
    on_action_callback: Optional[Callable[[], Any]] = None,
) -> ui.column:
    """Khung Empty State chuẩn Clean Minimalist / EdTech khi Deck hoặc danh sách thẻ rỗng."""
    with ui.column().classes(
        "bg-white border border-dashed border-slate-300 rounded-3xl p-12 text-center max-w-lg mx-auto items-center gap-5 my-8 shadow-xs w-full"
    ) as container:
        with ui.element("div").classes(
            "w-20 h-20 rounded-3xl bg-slate-50 flex items-center justify-center border border-slate-100 shadow-2xs"
        ):
            ui.icon(icon, size="64px").classes("text-slate-300")

        with ui.column().classes("gap-1.5 items-center"):
            ui.label(title).classes(
                "text-2xl font-extrabold text-slate-900 tracking-tight"
            )
            if description:
                ui.label(description).classes(
                    "text-sm text-slate-500 leading-relaxed max-w-sm"
                )

        with ui.row().classes("gap-3 mt-2 items-center justify-center flex-wrap"):
            def _trigger_primary() -> None:
                if on_action_callback:
                    if asyncio.iscoroutinefunction(on_action_callback):
                        asyncio.create_task(on_action_callback())
                    else:
                        on_action_callback()
                else:
                    ui.navigate.to(action_url)

            ui.button(
                action_text,
                icon="bolt",
                on_click=_trigger_primary,
            ).classes(
                "bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl px-6 py-2.5 shadow-md transition duration-200 cursor-pointer text-sm"
            )

            if secondary_text and secondary_url:
                ui.button(
                    secondary_text,
                    icon="folder_special",
                    on_click=lambda: ui.navigate.to(secondary_url),
                ).classes(
                    "bg-white hover:bg-slate-50 text-slate-700 font-bold rounded-xl px-5 py-2.5 border border-slate-200 transition duration-200 cursor-pointer text-sm"
                )

    return container

