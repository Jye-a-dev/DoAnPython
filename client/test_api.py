import sys
if sys.platform == "win32":
    if callable(getattr(sys.stdout, "reconfigure", None)):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if callable(getattr(sys.stderr, "reconfigure", None)):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import asyncio
from services.api import (
    # 1. Users
    get_users,
    get_user_by_id,
    create_user,
    login_user,
    update_user,
    delete_user,
    # 2. Profiles
    get_profiles,
    get_profile_by_id,
    get_user_profile,
    create_profile,
    update_profile,
    delete_profile,
    # 3. Categories
    get_categories,
    get_category_by_id,
    create_category,
    update_category,
    delete_category,
    # 4. Folders
    get_folders,
    get_folder_by_id,
    create_folder,
    update_folder,
    delete_folder,
    # 5. Documents
    upload_doc,
    get_documents,
    get_document_by_id,
    update_document,
    delete_document,
    # 6. Decks
    get_decks,
    get_deck_by_id,
    create_deck,
    update_deck,
    delete_deck,
    # 7. Cards
    get_cards,
    get_card_by_id,
    create_card,
    update_card,
    delete_card,
    delete_all_cards,
    # 8. Tags
    get_tags,
    get_tag_by_id,
    create_tag,
    update_tag,
    delete_tag,
    # 9. Card Tags
    get_card_tags,
    get_tags_for_card,
    add_card_tag,
    remove_card_tag,
    # 10. AI Logs
    get_ai_logs,
    get_ai_log_by_id,
    create_ai_log,
    update_ai_log,
    delete_ai_log,
    # 11. Study Sessions
    get_study_sessions,
    get_study_session_by_id,
    create_study_session,
    end_study_session,
    delete_study_session,
    # 12. Study Reviews
    get_study_reviews,
    get_study_review_by_id,
    submit_srs_review,
    delete_study_review,
    # 13. User Favorites
    get_favorites,
    get_favorite_by_id,
    add_favorite,
    delete_favorite,
    # Pipeline & Gateway
    generate_cards,
    transcribe_audio,
    generate_flashcards,
    check_system_health,
    close_client,
)


async def test_client_api_service():
    print("=== 1. KIỂM TRA SIGNATURE & CẤU HÌNH API CLIENT ===", flush=True)
    from services import api

    assert hasattr(api, "BACKEND_API_URL"), "Thiếu biến cấu hình BACKEND_API_URL"
    assert getattr(api, "DEFAULT_TIMEOUT", 0.0) == 120.0, "Timeout httpx.AsyncClient phải là 120.0s"
    print("[PASS] Biến môi trường và URL cơ sở đã được nạp thành công!", flush=True)

    print("\n=== 2. KIỂM TRA SIGNATURE TOÀN BỘ 13 TABLES TRÊN CLIENT ===", flush=True)
    all_funcs = [
        get_users, get_user_by_id, create_user, login_user, update_user, delete_user,
        get_profiles, get_profile_by_id, get_user_profile, create_profile, update_profile, delete_profile,
        get_categories, get_category_by_id, create_category, update_category, delete_category,
        get_folders, get_folder_by_id, create_folder, update_folder, delete_folder,
        upload_doc, get_documents, get_document_by_id, update_document, delete_document,
        get_decks, get_deck_by_id, create_deck, update_deck, delete_deck,
        get_cards, get_card_by_id, create_card, update_card, delete_card, delete_all_cards,
        get_tags, get_tag_by_id, create_tag, update_tag, delete_tag,
        get_card_tags, get_tags_for_card, add_card_tag, remove_card_tag,
        get_ai_logs, get_ai_log_by_id, create_ai_log, update_ai_log, delete_ai_log,
        get_study_sessions, get_study_session_by_id, create_study_session, end_study_session, delete_study_session,
        get_study_reviews, get_study_review_by_id, submit_srs_review, delete_study_review,
        get_favorites, get_favorite_by_id, add_favorite, delete_favorite,
        generate_cards, transcribe_audio, generate_flashcards, check_system_health,
    ]
    for fn in all_funcs:
        assert callable(fn), f"Hàm {fn.__name__} phải là callable"
    print(f"[PASS] Đã kiểm tra thành công {len(all_funcs)} API functions cho đầy đủ 13 tables!", flush=True)

    print("\n=== 3. KIỂM TRA BẮT LỖI KHI SERVER OFFLINE ===", flush=True)
    res_cards = await get_cards()
    assert res_cards == [] or (isinstance(res_cards, dict) and "error" in res_cards)

    res_users = await get_users()
    assert res_users == [] or (isinstance(res_users, dict) and "error" in res_users)

    await close_client()
    print("[PASS] Bắt lỗi an toàn khi ngắt kết nối!", flush=True)


if __name__ == "__main__":
    asyncio.run(test_client_api_service())
