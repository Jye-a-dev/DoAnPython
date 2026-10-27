from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional
from nicegui import ui

from components.layout import TOKENS, show_toast
from services import api


def render_deck_detail_dialog(
    active_user_id: int,
    on_deck_updated: Callable[[], Any],
) -> Dict[str, Any]:
    """Render detail modal for browsing/adding/deleting cards and managing tag chips."""
    detail_state: Dict[str, Any] = {"deck": None, "cards": []}

    with ui.dialog() as dialog, ui.card().classes(
        "w-full max-w-3xl p-6 rounded-3xl bg-white shadow-2xl border border-slate-100 gap-4 max-h-[88vh] flex flex-col"
    ):
        with ui.row().classes(
            "items-center justify-between w-full pb-3 border-b border-slate-100"
        ):
            with ui.row().classes("items-center gap-2"):
                ui.icon("style", size="22px").classes(f"text-{TOKENS['primary']}")
                detail_title_label = ui.label("Chi tiết bộ thẻ").classes(
                    "text-lg font-bold text-slate-900"
                )
            ui.button(icon="close", on_click=dialog.close).props(
                "flat dense round"
            ).classes("text-slate-400 hover:text-slate-700")

        detail_cards_scroll = ui.column().classes(
            "w-full overflow-y-auto gap-3 pr-1 max-h-[52vh]"
        )

        with ui.card().classes(
            "w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 gap-2"
        ):
            ui.label("Thêm nhanh flashcard vào bộ thẻ:").classes(
                f"text-xs font-bold text-{TOKENS['text_secondary']} uppercase tracking-wider"
            )
            with ui.row().classes("w-full gap-2 items-center"):
                new_q_input = (
                    ui.input(placeholder="Câu hỏi...")
                    .props("outlined dense")
                    .classes("flex-1 bg-white")
                )
                new_a_input = (
                    ui.input(placeholder="Đáp án...")
                    .props("outlined dense")
                    .classes("flex-1 bg-white")
                )

                async def handle_quick_add_card() -> None:
                    q = new_q_input.value.strip() if new_q_input.value else ""
                    a = new_a_input.value.strip() if new_a_input.value else ""
                    if not q or not a:
                        show_toast("Vui lòng điền đủ câu hỏi và đáp án", "warning")
                        return
                    target_d = detail_state["deck"]
                    if not target_d:
                        return
                    res = await api.create_card(
                        question=q, answer=a, deck_id=target_d["id"]
                    )
                    if isinstance(res, dict) and "id" in res:
                        show_toast("Đã thêm flashcard mới!", "positive")
                        new_q_input.value = ""
                        new_a_input.value = ""
                        await open_deck_detail_modal(target_d)
                        await on_deck_updated()
                    else:
                        show_toast("Lỗi khi thêm thẻ", "negative")

                ui.button("+ Thêm", on_click=handle_quick_add_card).classes(
                    f"bg-{TOKENS['primary']} text-white font-bold px-4 py-2 rounded-xl cursor-pointer"
                )

    async def open_deck_detail_modal(deck_data: Dict[str, Any]) -> None:
        detail_state["deck"] = deck_data
        detail_title_label.text = f"Bộ Thẻ: {deck_data.get('title', 'Deck')}"
        dialog.open()

        detail_cards_scroll.clear()
        deck_cards_resp = await api.get_cards(deck_id=deck_data["id"])
        deck_cards = deck_cards_resp if isinstance(deck_cards_resp, list) else []
        detail_state["cards"] = deck_cards

        all_tags_resp = await api.get_tags(user_id=active_user_id)
        tag_name_to_id: Dict[str, int] = {}
        if isinstance(all_tags_resp, list):
            tag_name_to_id = {
                t["name"].lower(): t["id"]
                for t in all_tags_resp
                if "id" in t and "name" in t
            }

        with detail_cards_scroll:
            if not deck_cards:
                with ui.column().classes(
                    "w-full py-8 items-center text-center gap-2 text-slate-400"
                ):
                    ui.icon("inbox", size="36px")
                    ui.label("Chưa có thẻ nào trong bộ này").classes("text-sm")
                return

            for idx, c in enumerate(deck_cards):
                card_id = c.get("id", 0)
                card_tags_raw = c.get("tags", [])
                current_tags: List[str] = []
                if isinstance(card_tags_raw, list):
                    for t in card_tags_raw:
                        if isinstance(t, dict):
                            current_tags.append(t.get("name", ""))
                        elif isinstance(t, str):
                            current_tags.append(t)

                with ui.card().classes(
                    "w-full bg-white border border-slate-200 rounded-xl p-3.5 shadow-2xs gap-2"
                ):
                    with ui.row().classes("items-center justify-between w-full"):
                        ui.label(f"#{idx + 1} (ID: {card_id})").classes(
                            "text-xs font-bold text-slate-400"
                        )

                        def make_del_card_cb(target_card_id: int):
                            async def del_card():
                                await api.delete_card(target_card_id)
                                show_toast("Đã xóa thẻ", "info")
                                await open_deck_detail_modal(deck_data)
                                await on_deck_updated()

                            return del_card

                        ui.button(
                            icon="delete", on_click=make_del_card_cb(card_id)
                        ).props("flat dense round").classes(
                            "text-slate-400 hover:text-rose-600 text-xs"
                        )

                    ui.label(f"Hỏi: {c.get('question', '')}").classes(
                        "text-sm font-bold text-slate-800"
                    )
                    ui.label(f"Đáp: {c.get('answer', '')}").classes(
                        "text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-1 rounded-md"
                    )
                    if c.get("explanation"):
                        ui.label(f"Giải thích: {c['explanation']}").classes(
                            "text-xs text-slate-500 italic"
                        )

                    with ui.column().classes(
                        "w-full gap-1 pt-2 border-t border-slate-100"
                    ):
                        with ui.row().classes("items-center justify-between w-full"):
                            ui.label("Nhãn thẻ (Tags):").classes(
                                "text-[11px] font-bold text-slate-400 uppercase tracking-wider"
                            )

                        tags_chips_row = ui.row().classes(
                            "items-center gap-1.5 flex-wrap w-full"
                        )
                        with tags_chips_row:
                            if not current_tags:
                                ui.label("Chưa gắn nhãn").classes(
                                    "text-xs text-slate-400 italic"
                                )
                            else:
                                for t_name in current_tags:
                                    t_clean = t_name.strip()
                                    if not t_clean:
                                        continue
                                    t_id = tag_name_to_id.get(t_clean.lower())

                                    def make_remove_tag_cb(
                                        cid: int, tid: Optional[int], name_str: str
                                    ):
                                        async def remove_tag_action():
                                            target_tid = tid
                                            if not target_tid:
                                                t_res = await api.create_tag(
                                                    name=name_str,
                                                    user_id=active_user_id,
                                                )
                                                if isinstance(t_res, dict):
                                                    target_tid = t_res.get("id")
                                            if target_tid:
                                                await api.remove_card_tag(
                                                    cid, target_tid
                                                )
                                                show_toast(
                                                    f"Đã gỡ nhãn '{name_str}'",
                                                    "info",
                                                )
                                                await open_deck_detail_modal(deck_data)

                                        return remove_tag_action

                                    with ui.row().classes(
                                        "items-center gap-1 px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 border border-slate-200 text-xs font-medium cursor-pointer hover:bg-rose-50 hover:text-rose-600 hover:border-rose-200 transition-colors"
                                    ).tooltip("Nhấp để gỡ nhãn").on(
                                        "click",
                                        make_remove_tag_cb(card_id, t_id, t_clean),
                                    ):
                                        ui.icon("label", size="11px").classes(
                                            "text-slate-400"
                                        )
                                        ui.label(t_clean)
                                        ui.icon("close", size="11px")

                        with ui.row().classes("w-full items-center gap-2 mt-1"):
                            tag_add_input = (
                                ui.input(placeholder="Gõ nhãn mới và ấn Enter...")
                                .props("outlined dense")
                                .classes("flex-1 text-xs bg-slate-50")
                            )

                            def make_add_tag_cb(cid: int, input_el: ui.input):
                                async def add_tag_action():
                                    new_t = (
                                        input_el.value.strip()
                                        if input_el.value
                                        else ""
                                    )
                                    if not new_t:
                                        return
                                    tag_res = await api.create_tag(
                                        name=new_t, user_id=active_user_id
                                    )
                                    tag_id_created = (
                                        tag_res.get("id")
                                        if isinstance(tag_res, dict)
                                        and not tag_res.get("error")
                                        else None
                                    )
                                    if tag_id_created:
                                        await api.add_card_tag(
                                            card_id=cid, tag_id=tag_id_created
                                        )
                                        show_toast(
                                            f"Đã gắn nhãn '{new_t}'", "positive"
                                        )
                                        input_el.value = ""
                                        await open_deck_detail_modal(deck_data)
                                    else:
                                        show_toast("Không thể tạo nhãn", "negative")

                                return add_tag_action

                            tag_add_cb = make_add_tag_cb(card_id, tag_add_input)
                            tag_add_input.on("keydown.enter", tag_add_cb)
                            ui.button("+ Gán", on_click=tag_add_cb).props(
                                "flat dense"
                            ).classes(f"text-xs font-bold text-{TOKENS['primary']}")

    return {
        "dialog": dialog,
        "open_modal": open_deck_detail_modal,
    }

