from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List
from nicegui import ui

from components import TOKENS, app_shell
from components.profile_favorites import render_profile_favorites_tab
from components.profile_stats import render_profile_stats_tab
from components.profile_telemetry import render_profile_telemetry_tab
from services import api
from services.auth_guard import get_current_user, require_auth


async def render_profile_page() -> None:
    """Dashboard Hồ sơ học tập cá nhân, Mục Yêu thích và Lịch sử Sinh thẻ AI (AI Telemetry)."""
    if not require_auth():
        return

    user = get_current_user() or {}
    user_id = int(user.get("id") or user.get("user_id") or 1)

    with app_shell(active_tab="profile", title="Hồ sơ học tập - EduFlash AI"):
        # 1. Truy vấn thông tin thực tế từ backend
        profile_data: Dict[str, Any] = {}
        try:
            p_res = await api.get_user_profile(user_id)
            if isinstance(p_res, dict) and not p_res.get("error"):
                profile_data = p_res
        except Exception:
            profile_data = {}

        decks_list: List[Dict[str, Any]] = []
        try:
            d_res = await api.get_decks(user_id=user_id)
            if isinstance(d_res, list):
                decks_list = d_res
        except Exception:
            decks_list = []

        cards_list: List[Dict[str, Any]] = []
        try:
            c_res = await api.get_cards(user_id=user_id)
            if isinstance(c_res, list):
                cards_list = c_res
        except Exception:
            cards_list = []

        sessions_list: List[Dict[str, Any]] = []
        try:
            s_res = await api.get_study_sessions(user_id=user_id)
            if isinstance(s_res, list):
                sessions_list = s_res
        except Exception:
            sessions_list = []

        favorites_list: List[Dict[str, Any]] = []
        try:
            fav_res = await api.get_favorites(user_id=user_id)
            if isinstance(fav_res, list):
                favorites_list = fav_res
        except Exception:
            favorites_list = []

        ai_logs_list: List[Dict[str, Any]] = []
        try:
            logs_res = await api.get_ai_logs(user_id=user_id)
            if isinstance(logs_res, list):
                ai_logs_list = logs_res
        except Exception:
            ai_logs_list = []

        docs_list: List[Dict[str, Any]] = []
        try:
            docs_res = await api.get_documents(user_id=user_id)
            if isinstance(docs_res, list):
                docs_list = docs_res
        except Exception:
            docs_list = []

        docs_map: Dict[Any, Any] = {
            d["id"]: d.get("filename", f"Tài liệu #{d['id']}")
            for d in docs_list
            if isinstance(d, dict) and "id" in d
        }
        decks_map: Dict[Any, Any] = {
            d["id"]: d for d in decks_list if isinstance(d, dict) and "id" in d
        }
        cards_map: Dict[Any, Any] = {
            c["id"]: c for c in cards_list if isinstance(c, dict) and "id" in c
        }

        total_decks = len(decks_list)
        total_cards = len(cards_list)
        mastered_cards = sum(
            1
            for c in cards_list
            if c.get("repetitions", 0) >= 2
            or str(c.get("difficulty", "")).lower() in {"dễ", "easy"}
        )
        total_sessions = len(sessions_list)

        streak_days = 0
        if sessions_list:
            session_dates = set()
            for s in sessions_list:
                ts_str = s.get("created_at") or s.get("started_at")
                if ts_str:
                    try:
                        d = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).date()
                        session_dates.add(d)
                    except Exception:
                        pass
            if session_dates:
                sorted_dates = sorted(list(session_dates), reverse=True)
                today = date.today()
                curr_date = today
                if sorted_dates[0] < today:
                    if sorted_dates[0] == today - timedelta(days=1):
                        curr_date = sorted_dates[0]
                    else:
                        streak_days = 0
                if streak_days == 0 and curr_date in session_dates:
                    for d in sorted_dates:
                        if d == curr_date:
                            streak_days += 1
                            curr_date -= timedelta(days=1)
                        elif d < curr_date:
                            break
            if streak_days == 0 and total_sessions > 0:
                streak_days = 1

        display_name = (
            profile_data.get("display_name")
            or profile_data.get("full_name")
            or user.get("display_name")
            or user.get("full_name")
            or user.get("username")
            or "Học viên EduFlash"
        )
        email = user.get("email") or "student@eduflash.ai"
        role_raw = user.get("role", "user")
        role_label = "Quản trị viên" if role_raw == "admin" else "Học viên"

        created_raw = user.get("created_at") or profile_data.get("created_at")
        joined_date = "Thành viên mới"
        if created_raw:
            try:
                dt = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
                joined_date = dt.strftime("%d/%m/%Y")
            except Exception:
                joined_date = str(created_raw)[:10]

        daily_goal_val = profile_data.get("daily_card_goal", 20)

        # 2. Layout Dashboard với Hệ Thống 3 Tabs
        with ui.column().classes("w-full gap-6 max-w-5xl mx-auto"):
            with ui.row().classes(
                "w-full items-center justify-between flex-wrap gap-4"
            ):
                with ui.column().classes("gap-1"):
                    ui.label("Hồ sơ & Giám sát học tập").classes(
                        f"text-3xl font-black text-{TOKENS['text_primary']} tracking-tight"
                    )
                    ui.label(
                        "Theo dõi tiến độ SM-2, quản lý mục yêu thích và giám sát hệ thống AI Telemetry"
                    ).classes(f"text-sm text-{TOKENS['text_secondary']}")

            with ui.tabs().classes(
                "w-full border-b border-slate-200 text-slate-600 bg-white rounded-2xl p-1 shadow-2xs"
            ) as profile_tabs:
                tab_stats = ui.tab(
                    "stats", label="1. Thống kê & Mục tiêu", icon="insights"
                ).classes(f"font-bold text-sm hover:text-{TOKENS['primary']}")
                tab_favorites = ui.tab(
                    "favorites",
                    label=f"2. Mục Yêu Thích ({len(favorites_list)} ⭐)",
                    icon="star",
                ).classes("font-bold text-sm hover:text-amber-500")
                tab_ai_telemetry = ui.tab(
                    "telemetry",
                    label=f"3. Lịch sử Sinh thẻ AI ({len(ai_logs_list)} logs)",
                    icon="precision_manufacturing",
                ).classes("font-bold text-sm hover:text-indigo-600")

            with ui.tab_panels(profile_tabs, value=tab_stats).classes(
                "w-full bg-transparent p-0 mt-2"
            ):
                with ui.tab_panel(tab_stats).classes("w-full p-0 flex flex-col gap-6"):
                    render_profile_stats_tab(
                        user_id=user_id,
                        display_name=display_name,
                        role_label=role_label,
                        email=email,
                        joined_date=joined_date,
                        total_decks=total_decks,
                        mastered_cards=mastered_cards,
                        total_cards=total_cards,
                        total_sessions=total_sessions,
                        streak_days=streak_days,
                        daily_goal_val=daily_goal_val,
                        profile_data=profile_data,
                    )

                with ui.tab_panel(tab_favorites).classes(
                    "w-full p-0 flex flex-col gap-6"
                ):
                    render_profile_favorites_tab(
                        favorites_list=favorites_list,
                        decks_map=decks_map,
                        cards_map=cards_map,
                        on_reload=render_profile_page,
                    )

                with ui.tab_panel(tab_ai_telemetry).classes(
                    "w-full p-0 flex flex-col gap-6"
                ):
                    render_profile_telemetry_tab(
                        ai_logs_list=ai_logs_list,
                        docs_map=docs_map,
                    )
