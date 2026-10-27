from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from nicegui import ui


def _format_date_time(iso_str: Optional[str]) -> str:
    """Format thời gian ISO 8601 sang ngày giờ chi tiết."""
    if not iso_str:
        return "--"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return str(iso_str)[:19]


def render_profile_telemetry_tab(
    ai_logs_list: List[Dict[str, Any]],
    docs_map: Dict[Any, Any],
) -> None:
    """Render Tab 3: AI Telemetry & Generation Logs Table."""
    with ui.card().classes(
        "w-full p-6 rounded-3xl bg-white border border-slate-200/80 shadow-sm gap-5"
    ):
        with ui.row().classes(
            "items-center justify-between w-full pb-3 border-b border-slate-100"
        ):
            with ui.row().classes("items-center gap-3"):
                with ui.element("div").classes(
                    "w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600"
                ):
                    ui.icon("terminal", size="22px")
                with ui.column().classes("gap-0"):
                    ui.label("Nhật ký AI Pipeline & Telemetry Logs").classes(
                        "text-lg font-black text-slate-900 tracking-tight"
                    )
                    ui.label(
                        "Chi tiết các lần chạy sinh câu hỏi từ mô hình Flan-T5, đo độ trễ và token"
                    ).classes("text-xs text-slate-500")

            ui.label(f"Tổng cộng: {len(ai_logs_list)} phiên").classes(
                "text-xs font-bold text-indigo-700 bg-indigo-50 border border-indigo-200 px-3 py-1 rounded-full"
            )

        if not ai_logs_list:
            with ui.column().classes(
                "w-full py-12 items-center justify-center text-center gap-2 text-slate-400"
            ):
                ui.icon("smart_toy", size="40px")
                ui.label("Chưa ghi nhận phiên sinh thẻ AI nào").classes(
                    "text-sm font-medium"
                )
                ui.label(
                    "Nạp tài liệu hoặc văn bản tại Studio để AI tự động trích xuất thẻ và ghi nhận nhật ký."
                ).classes("text-xs text-slate-400 max-w-sm")
        else:
            columns = [
                {
                    "name": "time",
                    "label": "Thời gian",
                    "field": "time",
                    "align": "left",
                    "sortable": True,
                },
                {
                    "name": "doc",
                    "label": "Tài liệu nguồn",
                    "field": "doc",
                    "align": "left",
                },
                {
                    "name": "model",
                    "label": "Model AI",
                    "field": "model",
                    "align": "left",
                },
                {
                    "name": "cards",
                    "label": "Số thẻ tạo",
                    "field": "cards",
                    "align": "center",
                    "sortable": True,
                },
                {
                    "name": "latency",
                    "label": "Độ trễ (giây)",
                    "field": "latency",
                    "align": "center",
                    "sortable": True,
                },
                {
                    "name": "tokens",
                    "label": "Tokens tiêu thụ",
                    "field": "tokens",
                    "align": "center",
                },
                {
                    "name": "status",
                    "label": "Trạng thái",
                    "field": "status",
                    "align": "center",
                },
            ]

            rows = []
            for log in ai_logs_list:
                doc_id_val = log.get("document_id")
                doc_name = (
                    docs_map.get(doc_id_val, f"Tài liệu #{doc_id_val}")
                    if doc_id_val
                    else "Văn bản trực tiếp"
                )
                p_tok = log.get("prompt_tokens", 0)
                c_tok = log.get("completion_tokens", 0)
                status_str = str(log.get("status", "SUCCESS")).upper()

                rows.append(
                    {
                        "id": log.get("id"),
                        "time": _format_date_time(log.get("created_at")),
                        "doc": doc_name,
                        "model": log.get("model_name", "flan-t5-base"),
                        "cards": f"{log.get('cards_generated', 0)} thẻ",
                        "latency": f"{float(log.get('inference_time_seconds', 0.0)):.2f}s",
                        "tokens": f"{p_tok + c_tok} ({p_tok} in / {c_tok} out)",
                        "status": status_str,
                    }
                )

            table = ui.table(
                columns=columns,
                rows=rows,
                row_key="id",
                pagination={"rowsPerPage": 10},
            ).classes("w-full shadow-none border border-slate-200 rounded-xl")

            table.add_slot(
                "body-cell-status",
                """
                <q-td :props="props">
                    <span v-if="props.value === 'SUCCESS'" class="px-2.5 py-1 rounded-full text-xs font-extrabold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        SUCCESS
                    </span>
                    <span v-else class="px-2.5 py-1 rounded-full text-xs font-extrabold bg-rose-50 text-rose-700 border border-rose-200">
                        {{ props.value }}
                    </span>
                </q-td>
                """,
            )

            table.add_slot(
                "body-cell-model",
                """
                <q-td :props="props">
                    <span class="px-2 py-0.5 rounded-md text-xs font-mono font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                        {{ props.value }}
                    </span>
                </q-td>
                """,
            )

