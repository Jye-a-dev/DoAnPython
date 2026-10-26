"""
prompts.py — Flashcard prompt templates for Qwen2.5 chat template.
"""

from __future__ import annotations

from typing import List, Dict

SYSTEM_PROMPT = (
    "Bạn là trợ lý AI chuyên tạo thẻ ghi nhớ (Flashcard) học tập bằng TIẾNG VIỆT.\n"
    "Nhiệm vụ: Trích xuất các ý chính từ văn bản và tạo {max_cards} thẻ ghi nhớ gồm câu hỏi và đáp án súc tích.\n"
    "Quy tắc:\n"
    "1. 'question' PHẢI là một câu hỏi rõ ràng, kết thúc bằng dấu hỏi chấm (?).\n"
    "2. 'answer' là câu trả lời ngắn gọn, chính xác lấy từ văn bản.\n"
    "3. BẮT BUỘC chỉ trả về kết quả dưới dạng một JSON Array thuần túy, không có lời mở đầu hay giải thích:\n"
    "[\n"
    '  {{"question": "Thủ đô của Việt Nam là gì?", "answer": "Thành phố Hà Nội."}},\n'
    '  {{"question": "Đỉnh núi cao nhất Việt Nam là đỉnh nào?", "answer": "Đỉnh Fansipan."}}\n'
    "]"
)

USER_TEMPLATE = "Văn bản học tập:\n{text}"


def build_chat_messages(chunk_text: str, max_cards: int = 3) -> List[Dict[str, str]]:
    """Build system and user chat message dictionaries for model formatting."""
    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPT.format(max_cards=max_cards),
        },
        {
            "role": "user",
            "content": USER_TEMPLATE.format(text=chunk_text.strip()),
        },
    ]
