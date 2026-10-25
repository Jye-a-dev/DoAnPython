from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from nicegui import ui

from components import TOKENS, app_shell, show_toast
from services import api
from services.auth_guard import get_current_user, require_auth, logout


async def render_profile_page() -> None:
    """Dashboard Hồ sơ học tập cá nhân & Thống kê Spaced Repetition (SM-2)."""
    if not require_auth():
        return

    user = get_current_user() or {}
    user_id = user.get("id") or user.get("user_id") or 1

    with app_shell(
        active_tab="profile", title="Hồ sơ học tập - EduFlash AI"
    ):
        # 1. Truy vấn thông tin thực tế từ backend (Profile, Decks, Cards, Sessions)
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

        # Tính toán chỉ số thống kê thực tế
        total_decks = len(decks_list)
        total_cards = len(cards_list)

        mastered_cards = sum(
            1
            for c in cards_list
            if c.get("repetitions", 0) >= 2
            or str(c.get("difficulty", "")).lower() in {"dễ", "easy"}
        )
        total_sessions = len(sessions_list)

        # Tính toán chuỗi ngày học Streak (🔥)
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

        # Trích xuất thông tin người dùng
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

        # ===================================================================
        # GIAO DIỆN PROFILE DASHBOARD
        # ===================================================================
        with ui.column().classes("w-full gap-8 max-w-5xl mx-auto"):
            # Header Tiêu đề
            with ui.row().classes("w-full items-center justify-between flex-wrap gap-4"):
                with ui.column().classes("gap-1"):
                    ui.label("Hồ sơ & Tiến độ học tập").classes(
                        f"text-3xl font-black text-{TOKENS['text_primary']} tracking-tight"
                    )
                    ui.label("Theo dõi hành trình ghi nhớ dài hạn và chỉ số thuật toán SM-2").classes(
                        f"text-sm text-{TOKENS['text_secondary']}"
                    )

            # ---------------------------------------------------------------
            # KHỐI 1: THÔNG TIN CÁ NHÂN (USER IDENTITY CARD)
            # ---------------------------------------------------------------
            with ui.card().classes(
                "w-full p-6 md:p-8 rounded-3xl bg-white border border-slate-200/80 shadow-sm"
            ):
                with ui.row().classes("w-full items-center justify-between flex-wrap gap-6"):
                    with ui.row().classes("items-center gap-5"):
                        initial_char = (str(display_name)[:1] if display_name else "U").upper()
                        with ui.avatar(size="72px").classes(
                            f"ring-4 ring-indigo-100 bg-gradient-to-tr from-{TOKENS['primary']} to-indigo-500 "
                            "text-white text-2xl font-black shadow-md select-none"
                        ):
                            ui.label(initial_char)

                        with ui.column().classes("gap-1"):
                            with ui.row().classes("items-center gap-3"):
                                ui.label(display_name).classes(
                                    f"text-xl md:text-2xl font-extrabold text-{TOKENS['text_primary']}"
                                )
                                with ui.element("div").classes(
                                    "px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700 border border-indigo-200"
                                ):
                                    ui.label(role_label)

                            ui.label(email).classes(f"text-sm font-medium text-{TOKENS['text_secondary']}")
                            with ui.row().classes("items-center gap-1.5 text-xs text-slate-400 mt-1"):
                                ui.icon("event", size="16px")
                                ui.label(f"Ngày tham gia: {joined_date}")

                    with ui.row().classes("items-center gap-3"):
                        with ui.link(target="/decks").classes("no-underline"):
                            ui.button("Đến kho thẻ", icon="style").props("outline").classes(
                                f"text-{TOKENS['primary']} border-{TOKENS['primary']} rounded-xl font-bold px-4 py-2"
                            )

            # ---------------------------------------------------------------
            # KHỐI 2: CHỈ SỐ ÔN TẬP (SM-2 METRICS KPI GRID)
            # ---------------------------------------------------------------
            with ui.column().classes("w-full gap-3"):
                ui.label("Chỉ số hiệu quả ôn tập").classes(
                    f"text-lg font-extrabold text-{TOKENS['text_primary']}"
                )

                with ui.grid().classes("w-full grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"):
                    # KPI 1: Tổng số Deck
                    with ui.card().classes(
                        "p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex flex-col justify-between"
                    ):
                        with ui.row().classes("w-full items-center justify-between"):
                            ui.label("Bộ thẻ sở hữu").classes("text-xs font-bold text-slate-500 uppercase tracking-wider")
                            with ui.element("div").classes(
                                "w-9 h-9 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600"
                            ):
                                ui.icon("style", size="20px")
                        with ui.row().classes("items-baseline gap-2 mt-3"):
                            ui.label(str(total_decks)).classes("text-3xl font-black text-slate-900")
                            ui.label("decks").classes("text-xs font-semibold text-slate-400")

                    # KPI 2: Thẻ đã thuộc
                    with ui.card().classes(
                        "p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex flex-col justify-between"
                    ):
                        with ui.row().classes("w-full items-center justify-between"):
                            ui.label("Thẻ đã thuộc").classes("text-xs font-bold text-slate-500 uppercase tracking-wider")
                            with ui.element("div").classes(
                                "w-9 h-9 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600"
                            ):
                                ui.icon("verified", size="20px")
                        with ui.row().classes("items-baseline gap-2 mt-3"):
                            ui.label(str(mastered_cards)).classes("text-3xl font-black text-emerald-600")
                            ui.label(f"/ {total_cards} thẻ").classes("text-xs font-semibold text-slate-400")

                    # KPI 3: Số phiên học hoàn tất
                    with ui.card().classes(
                        "p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex flex-col justify-between"
                    ):
                        with ui.row().classes("w-full items-center justify-between"):
                            ui.label("Phiên học hoàn tất").classes("text-xs font-bold text-slate-500 uppercase tracking-wider")
                            with ui.element("div").classes(
                                "w-9 h-9 rounded-xl bg-blue-50 flex items-center justify-center text-blue-600"
                            ):
                                ui.icon("school", size="20px")
                        with ui.row().classes("items-baseline gap-2 mt-3"):
                            ui.label(str(total_sessions)).classes("text-3xl font-black text-blue-600")
                            ui.label("phiên").classes("text-xs font-semibold text-slate-400")

                    # KPI 4: Chuỗi ngày học Streak
                    with ui.card().classes(
                        "p-5 rounded-2xl bg-white border border-slate-200/80 shadow-xs flex flex-col justify-between"
                    ):
                        with ui.row().classes("w-full items-center justify-between"):
                            ui.label("Chuỗi ngày Streak").classes("text-xs font-bold text-slate-500 uppercase tracking-wider")
                            with ui.element("div").classes(
                                "w-9 h-9 rounded-xl bg-amber-50 flex items-center justify-center text-amber-500"
                            ):
                                ui.icon("local_fire_department", size="20px")
                        with ui.row().classes("items-baseline gap-2 mt-3"):
                            ui.label(f"{streak_days} 🔥").classes("text-3xl font-black text-amber-600")
                            ui.label("ngày liên tục").classes("text-xs font-semibold text-slate-400")

            # ---------------------------------------------------------------
            # KHỐI 3: CÀI ĐẶT MỤC TIÊU (DAILY CARD GOAL)
            # ---------------------------------------------------------------
            with ui.card().classes(
                "w-full p-6 md:p-8 rounded-3xl bg-white border border-slate-200/80 shadow-sm gap-5"
            ):
                with ui.row().classes("items-center gap-3 pb-2 border-b border-slate-100"):
                    with ui.element("div").classes(
                        f"w-10 h-10 rounded-xl bg-{TOKENS['primary_light']} flex items-center justify-center text-{TOKENS['primary']}"
                    ):
                        ui.icon("flag", size="22px")
                    with ui.column().classes("gap-0"):
                        ui.label("Cài đặt mục tiêu học tập hàng ngày").classes(
                            f"text-lg font-bold text-{TOKENS['text_primary']}"
                        )
                        ui.label("Xác định số lượng thẻ mới cần ôn tập mỗi ngày để thuật toán SM-2 lập lịch").classes(
                            f"text-xs text-{TOKENS['text_secondary']}"
                        )

                with ui.row().classes("w-full items-center gap-4 flex-wrap"):
                    goal_input = (
                        ui.number(
                            label="Mục tiêu thẻ ôn mỗi ngày (daily_card_goal)",
                            value=daily_goal_val,
                            min=5,
                            max=200,
                            step=5,
                        )
                        .props("outlined dense")
                        .classes("w-full max-w-xs")
                    )

                    async def handle_save_goal() -> None:
                        val = int(goal_input.value or 20)
                        save_goal_btn.props("loading")
                        try:
                            # Cập nhật thông qua API user_profiles
                            p_id = profile_data.get("id")
                            if p_id:
                                res = await api.update_profile(p_id, daily_card_goal=val)
                            else:
                                res = await api.create_profile(user_id=user_id, daily_card_goal=val)

                            if isinstance(res, dict) and res.get("error"):
                                show_toast(res.get("message") or "Không thể lưu cài đặt", "negative")
                            else:
                                show_toast(f"Đã cập nhật mục tiêu: {val} thẻ/ngày", "positive")
                        finally:
                            save_goal_btn.props(remove="loading")

                    save_goal_btn = ui.button(
                        "LƯU MỤC TIÊU",
                        icon="save",
                        on_click=handle_save_goal,
                    ).classes(
                        f"bg-{TOKENS['primary']} hover:bg-{TOKENS['primary_hover']} text-white font-bold px-6 py-2.5 rounded-xl shadow-xs transition-all cursor-pointer"
                    )

            # ---------------------------------------------------------------
            # KHỐI 4: NÚT ĐĂNG XUẤT NỔI BẬT
            # ---------------------------------------------------------------
            with ui.column().classes("w-full items-center pt-4 pb-12"):
                ui.button(
                    "ĐĂNG XUẤT TÀI KHOẢN",
                    icon="logout",
                    on_click=logout,
                ).classes(
                    "w-full max-w-md py-3.5 bg-rose-500 hover:bg-rose-600 text-white font-extrabold rounded-2xl "
                    "shadow-lg hover:shadow-rose-500/25 transition-all duration-200 cursor-pointer"
                )

