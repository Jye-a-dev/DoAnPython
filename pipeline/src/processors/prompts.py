"""
prompts.py — Flashcard prompt templates for Qwen2.5 chat template.
"""

from __future__ import annotations

from typing import List, Dict

SYSTEM_PROMPT = (
    "Bạn là một trợ lý giáo dục chuyên nghiệp. Nhiệm vụ của bạn là đọc kỹ đoạn văn bản được cung cấp "
    "và trích xuất chính xác các ý chính để tạo ra các thẻ ghi nhớ (Flashcard) bằng TIẾNG VIỆT.\n"
    "YÊU CẦU BẮT BUỘC:\n"
    "1. Chỉ sử dụng thông tin có trong đoạn văn bản đầu vào. Tuyệt đối KHÔNG tự bịa đặt hay đưa thông tin ngoài lề.\n"
    "2. Tạo đúng số lượng thẻ được yêu cầu.\n"
    "3. Câu hỏi phải rõ ràng và kết thúc bằng dấu chấm hỏi (?). Câu trả lời phải ngắn gọn, súc tích.\n"
    "4. Chỉ xuất duy nhất một JSON Array hợp lệ theo cấu trúc sau, không thêm lời dẫn giải:\n"
    "[\n"
    '  {"question": "...", "answer": "..."}\n'
    "]"
)

USER_TEMPLATE = (
    "Số lượng thẻ cần tạo: {max_cards}\n\n"
    'Nội dung văn bản:\n"""\n{text}\n"""\n\n'
    "JSON Flashcards:"
)


def build_chat_messages(chunk_text: str, max_cards: int = 3) -> List[Dict[str, str]]:
    """Build system and user chat message dictionaries for model formatting."""
    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": USER_TEMPLATE.format(
                max_cards=max_cards, text=chunk_text.strip()
            ),
        },
    ]
