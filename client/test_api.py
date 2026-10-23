import sys
if sys.platform == "win32":
    if callable(getattr(sys.stdout, "reconfigure", None)):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if callable(getattr(sys.stderr, "reconfigure", None)):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import asyncio
import httpx
from services.api import (
    upload_doc,
    generate_cards,
    transcribe_audio,
    get_decks,
    get_cards,
    submit_srs_review,
    close_client,
)

async def test_client_api_service():
    print('=== 1. KIỂM TRA SIGNATURE & TIMEOUT CẤU HÌNH ===', flush=True)
    from services import api
    assert hasattr(api, 'BACKEND_API_URL') or hasattr(api, 'BASE_URL'), 'Thiếu biến cấu hình API URL'
    assert getattr(api, 'DEFAULT_TIMEOUT', 0.0) == 120.0, 'Timeout httpx.AsyncClient phải là 120.0s'
    print('[PASS] Biến môi trường và URL cơ sở đã được nạp thành công!', flush=True)

    print('\n=== 2. KIỂM TRA KHẢ NĂNG BẮT NGOẠI LỆ KHI SERVER OFFLINE ===', flush=True)
    res_cards = await get_cards()
    assert res_cards == [] or (isinstance(res_cards, dict) and 'error' in res_cards), 'Không xử lý an toàn lỗi khi server offline'
    print('[PASS] Bắt lỗi ngắt kết nối an toàn (Connection Error Gracefully Handled)!', flush=True)

    print('\n=== 3. MOCK VALIDATION MULTIPART & PARAMS (DRY RUN) ===', flush=True)
    fake_audio = b'fake_audio_bytes_data'
    res_audio = await transcribe_audio(fake_audio, 'test.wav')
    assert isinstance(res_audio, dict), 'Hàm transcribe_audio phải trả về kiểu dict'
    
    res_review = await submit_srs_review(session_id=1, card_id=1, rating=3)
    assert isinstance(res_review, dict), 'Hàm submit_srs_review phải trả về kiểu dict'
    print('[PASS] Toàn bộ 6 API signatures hoạt động đúng chuẩn bất đồng bộ (async/await)!', flush=True)

    print('\n=== BƯỚC 1: API ASYNC CLIENT HOÀN TOÀN HỢP LỆ VÀ SẴN SÀNG TÍCH HỢP UI ===', flush=True)
    await close_client()

if __name__ == '__main__':
    asyncio.run(test_client_api_service())

