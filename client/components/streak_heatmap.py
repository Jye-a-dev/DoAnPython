"""
streak_heatmap.py — Component Biểu đồ đóng băng chuỗi ôn tập (Streak Heatmap).
Lưới 7 hàng (thứ trong tuần) x 52 cột (tuần trong năm) hiển thị theo cấp độ Level 0..4.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from nicegui import ui
from components.layout import TOKENS
from services import api

COLOR_MAP = {
    0: "bg-slate-100 border-slate-200/70",
    1: "bg-emerald-200 border-emerald-300",
    2: "bg-emerald-400 border-emerald-500",
    3: "bg-emerald-600 border-emerald-700",
    4: "bg-emerald-800 border-emerald-900",
}


def render_streak_heatmap(user_id: int, year: Optional[int] = None) -> None:
    """Render Heatmap chuỗi ôn tập Spaced Repetition (SM-2) trên trang Profile."""
    target_year = year or datetime.utcnow().year

    container = ui.card().classes(
        "w-full p-6 md:p-8 rounded-3xl bg-white border border-slate-200/80 shadow-sm gap-4"
    )

    with container:
        with ui.row().classes("w-full items-center justify-between pb-2 border-b border-slate-100 flex-wrap gap-2"):
            with ui.row().classes("items-center gap-3"):
                with ui.element("div").classes(
                    "w-10 h-10 rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100 shadow-2xs"
                ):
                    ui.icon("calendar_month", size="22px")
                with ui.column().classes("gap-0"):
                    ui.label(f"Chuỗi Hoạt Động Ôn Tập Năm {target_year}").classes(
                        f"text-lg font-black text-{TOKENS['text_primary']}"
                    )
                    ui.label(
                        "Theo dõi tần suất và mức độ đóng băng chuỗi ôn tập thẻ SM-2 hàng ngày"
                    ).classes(f"text-xs text-{TOKENS['text_secondary']}")

            summary_badge = ui.label("Đang tải dữ liệu...").classes(
                "text-xs font-bold text-slate-500 bg-slate-100 px-3 py-1 rounded-full border border-slate-200"
            )

        grid_wrapper = ui.column().classes("w-full overflow-x-auto pb-2 pt-1")

    async def load_data():
        resp = await api.get_streak_heatmap(user_id=user_id, year=target_year)
        heatmap_data: Dict[str, Any] = resp if isinstance(resp, dict) and not resp.get("error") else {}

        total_reviews = sum(int(v.get("review_count", 0)) for v in heatmap_data.values())
        total_days = sum(1 for v in heatmap_data.values() if int(v.get("review_count", 0)) > 0)
        summary_badge.text = f"{total_reviews} lượt ôn tập / {total_days} ngày hoạt động"
        summary_badge.classes(replace="bg-emerald-50 text-emerald-700 border-emerald-200")

        grid_wrapper.clear()
        with grid_wrapper:
            # Xác định ngày bắt đầu (Thứ 2 đầu tiên hoặc ngày cách đây 52 tuần)
            today = date.today()
            if target_year == today.year:
                end_date = today
                start_date = end_date - timedelta(days=52 * 7 - 1)
            else:
                start_date = date(target_year, 1, 1)
                end_date = date(target_year, 12, 31)

            # Đẩy lùi start_date về Thứ 2 (weekday = 0)
            start_date -= timedelta(days=start_date.weekday())

            # Chuẩn bị ma trận 7 hàng x N cột
            days_grid: List[List[date]] = [[] for _ in range(7)]
            curr = start_date
            while curr <= end_date or curr.weekday() != 0:
                days_grid[curr.weekday()].append(curr)
                curr += timedelta(days=1)

            day_labels = ["T2", "", "T4", "", "T6", "", "CN"]

            with ui.row().classes("items-start gap-2"):
                # Cột hiển thị Thứ
                with ui.column().classes("gap-1 pt-1 select-none pr-1"):
                    for label in day_labels:
                        ui.label(label).classes("text-[10px] font-bold text-slate-400 h-3 leading-3")

                # Lưới Heatmap 7 hàng
                with ui.column().classes("gap-1"):
                    for weekday_idx in range(7):
                        with ui.row().classes("gap-1"):
                            for d in days_grid[weekday_idx]:
                                d_str = d.strftime("%Y-%m-%d")
                                d_meta = heatmap_data.get(d_str, {"review_count": 0, "level": 0, "sessions": 0})
                                lvl = int(d_meta.get("level", 0))
                                rev_cnt = int(d_meta.get("review_count", 0))
                                sess_cnt = int(d_meta.get("sessions", 0))

                                color_class = COLOR_MAP.get(lvl, COLOR_MAP[0])
                                cell = ui.element("div").classes(
                                    f"w-3 h-3 rounded-[3px] border cursor-pointer transition-transform hover:scale-125 {color_class}"
                                )
                                d_vn = d.strftime("%d/%m/%Y")
                                cell.tooltip(f"{d_vn}: {rev_cnt} thẻ ôn SM-2, {sess_cnt} phiên học")

            # Legend ghi chú các mức Level
            with ui.row().classes("w-full items-center justify-end gap-2 pt-3 text-xs text-slate-400"):
                ui.label("Ít")
                for lvl in range(5):
                    ui.element("div").classes(f"w-3 h-3 rounded-[3px] border {COLOR_MAP[lvl]}")
                ui.label("Nhiều")

    ui.timer(0.1, load_data, once=True)

