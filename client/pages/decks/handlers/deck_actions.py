"""
deck_actions.py — CRUD handlers and Web Speech TTS execution for Decks & Cards.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from nicegui import ui
from services import api


async def load_decks_overview(active_user_id: int) -> Dict[str, Any]:
    """Tải toàn bộ dữ liệu decks, cards, categories, folders, favorites cho user."""
    decks_resp = await api.get_decks(user_id=active_user_id)
    all_cards_resp = await api.get_cards(user_id=active_user_id)
    categories_resp = await api.get_categories(user_id=active_user_id)
    folders_resp = await api.get_folders(user_id=active_user_id)
    favorites_resp = await api.get_favorites(user_id=active_user_id)

    is_err = any(
        api.is_connection_error(r)
        for r in (decks_resp, all_cards_resp, categories_resp, folders_resp)
    )
    if is_err:
        return {"error": True, "message": "Lỗi kết nối máy chủ backend"}

    return {
        "error": False,
        "decks": decks_resp if isinstance(decks_resp, list) else [],
        "cards": all_cards_resp if isinstance(all_cards_resp, list) else [],
        "categories": categories_resp if isinstance(categories_resp, list) else [],
        "folders": folders_resp if isinstance(folders_resp, list) else [],
        "favorites": favorites_resp if isinstance(favorites_resp, list) else [],
    }


async def save_card_action(
    deck_id: Optional[int],
    card_id: Optional[int],
    question: str,
    answer: str,
    explanation: Optional[str] = None,
    tts_text: Optional[str] = None,
    tts_lang: str = "en-US",
) -> Dict[str, Any]:
    """Tạo mới hoặc cập nhật Card đồng bộ trường TTS."""
    clean_tts = (tts_text or "").strip() or question.strip()
    clean_lang = (tts_lang or "en-US").strip()
    payload = {
        "question": question.strip(),
        "answer": answer.strip(),
        "explanation": (explanation or "").strip() or None,
        "tts_text": clean_tts,
        "tts_lang": clean_lang,
    }
    if card_id:
        return await api.update_card(card_id, **payload)
    return await api.create_card(deck_id=deck_id, **payload)


async def delete_card_action(card_id: int) -> Dict[str, Any]:
    """Xóa flashcard theo ID."""
    return await api.delete_card(card_id)


async def delete_deck_action(deck_id: int) -> Dict[str, Any]:
    """Xóa bộ thẻ theo ID."""
    return await api.delete_deck(deck_id)


async def update_deck_title(deck_id: int, title: str) -> Dict[str, Any]:
    """Đổi tên bộ thẻ."""
    return await api.update_deck(deck_id, title=title)


def play_tts_speech(text: str, lang: str = "en-US") -> None:
    """Gọi Web Speech API phát âm thanh trực tiếp trên client browser."""
    if not text:
        return
    clean_text = text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
    clean_lang = (lang or "en-US").replace("'", "").strip()
    js_code = f"""
    (() => {{
        const ev = window.event;
        if (ev && ev.stopPropagation) {{ ev.stopPropagation(); }}
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(`{clean_text}`);
        u.lang = '{clean_lang}';
        window.speechSynthesis.speak(u);
    }})();
    """
    ui.run_javascript(js_code)

