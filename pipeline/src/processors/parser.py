"""
parser.py — Multi-tier Flashcard Output Parser & Deduplication.
Supports JSON Array, JSON Object scan, Labeled Q/A (EN & VI), Numbered pairs, and Fallback splitting.
"""

from __future__ import annotations

import json
import logging
import re
from typing import List, Dict, Set

logger = logging.getLogger(__name__)

# Tier 0b: JSON object fallback (regex scan từng object)
PATTERN_JSON_OBJ = re.compile(
    r'\{\s*"question"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*"answer"\s*:\s*"((?:[^"\\]|\\.)*)"\s*\}',
    re.DOTALL,
)

# Tier 1: "Q: ... A: ..." hoặc "Question: ... Answer: ..."
PATTERN_EN_QA = re.compile(
    r"(?:Q(?:uestion)?)\s*(?:\d+)?\s*[:\-]\s*(.+?)\s*(?:A(?:nswer)?)\s*(?:\d+)?\s*[:\-]\s*(.+?)(?=\n\s*(?:Q(?:uestion)?)\s*(?:\d+)?\s*[:\-]|$)",
    re.DOTALL | re.IGNORECASE,
)

# Tier 2: "Câu hỏi: ... Đáp án: ..." (tiếng Việt)
PATTERN_VI_QA = re.compile(
    r"(?:Câu hỏi|CH)\s*(?:\d+)?\s*[:\-]\s*(.+?)\s*(?:Đáp án|Trả lời|ĐA)\s*(?:\d+)?\s*[:\-]\s*(.+?)(?=\n\s*(?:Câu hỏi|CH)\s*(?:\d+)?\s*[:\-]|$)",
    re.DOTALL | re.IGNORECASE,
)

# Tier 3: Dòng kết thúc ? + dòng ngay sau
PATTERN_QUESTION_LINES = re.compile(
    r"^(.+\?)\s*\n\s*([^\n?]+?)(?=\n|$)",
    re.MULTILINE,
)

# Tier 4: Cặp đánh số "1. Câu hỏi? Đáp án."
PATTERN_NUMBERED = re.compile(
    r"\d+[\.]\s*(.+?\?)\s*\n\s*(.+?)(?=\n\s*\d+[\.]|$)",
    re.DOTALL,
)

INVALID_PLACEHOLDERS = {
    "string",
    "...",
    "…",
    "câu hỏi bằng tiếng việt?",
    "câu hỏi bằng tiếng việt",
    "đáp án ngắn gọn bằng tiếng việt.",
    "đáp án bằng tiếng việt",
    "question",
    "answer",
    "nội dung câu hỏi",
    "nội dung câu trả lời",
    "thủ đô của việt nam là gì?",
    "thủ đô của việt nam là gì",
    "thành phố hà nội.",
    "thành phố hà nội",
    "đỉnh núi cao nhất việt nam là đỉnh nào?",
    "đỉnh núi cao nhất việt nam là đỉnh nào",
    "đỉnh fansipan.",
    "đỉnh fansipan",
}


def clean_qa_text(text: str) -> str:
    """Loại bỏ ký tự bao bọc thừa như [], ngoặc kép và khoảng trắng."""
    s = text.strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1].strip()
    return s.strip("\"' \t\r\n")


def is_valid_card(q: str, a: str) -> bool:
    """Kiểm tra thẻ không phải là placeholder rỗng hoặc chuỗi mặc định."""
    if not q or not a:
        return False
    q_norm = q.lower().strip().rstrip("?").strip()
    a_norm = a.lower().strip().rstrip(".").strip()
    if q_norm in INVALID_PLACEHOLDERS or a_norm in INVALID_PLACEHOLDERS:
        return False
    if len(q) < 5 or len(a) < 2:
        return False
    if q_norm == a_norm:
        return False
    return True


def deduplicate_cards(cards: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Loại bỏ thẻ trùng lặp dựa trên câu hỏi đã chuẩn hóa."""
    seen: Set[str] = set()
    unique: List[Dict[str, str]] = []
    for card in cards:
        key = card["question"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(card)
    return unique


def parse_flashcard_output(raw_output: str) -> List[Dict[str, str]]:
    """
    Parser đa tầng: JSON array → JSON object scan → Q/A labeled → numbered → fallback.
    """
    cards: List[Dict[str, str]] = []
    if not raw_output or not raw_output.strip():
        return cards

    text = raw_output.strip()

    # --- Tier 0a: JSON array ---
    json_array_match = re.search(r"\[.*?\]", text, re.DOTALL)
    if json_array_match:
        try:
            parsed = json.loads(json_array_match.group(0))
            if isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        q = clean_qa_text(str(item.get("question", "")))
                        a = clean_qa_text(str(item.get("answer", "")))
                        if is_valid_card(q, a):
                            if not q.endswith("?"):
                                q += "?"
                            cards.append({"question": q, "answer": a})
                if cards:
                    return deduplicate_cards(cards)
        except json.JSONDecodeError:
            pass

    # --- Tier 0b: JSON objects scan (fallback nếu array parse thất bại) ---
    for q_txt, a_txt in PATTERN_JSON_OBJ.findall(text):
        q_clean = clean_qa_text(q_txt)
        a_clean = clean_qa_text(a_txt)
        if is_valid_card(q_clean, a_clean):
            if not q_clean.endswith("?"):
                q_clean += "?"
            cards.append({"question": q_clean, "answer": a_clean})
    if cards:
        return deduplicate_cards(cards)

    # --- Tier 1: EN labeled Q/A ---
    for q_txt, a_txt in PATTERN_EN_QA.findall(text):
        q_clean = clean_qa_text(q_txt).rstrip("?").strip()
        a_clean = clean_qa_text(a_txt)
        if is_valid_card(q_clean, a_clean) and len(a_clean) > 3:
            cards.append({"question": q_clean + "?", "answer": a_clean})
    if cards:
        return deduplicate_cards(cards)

    # --- Tier 2: VI labeled Q/A ---
    for q_txt, a_txt in PATTERN_VI_QA.findall(text):
        q_clean = clean_qa_text(q_txt).rstrip("?").strip()
        a_clean = clean_qa_text(a_txt)
        if is_valid_card(q_clean, a_clean) and len(a_clean) > 3:
            cards.append({"question": q_clean + "?", "answer": a_clean})
    if cards:
        return deduplicate_cards(cards)

    # --- Tier 3: Numbered pairs ---
    for q_txt, a_txt in PATTERN_NUMBERED.findall(text):
        q_clean = clean_qa_text(q_txt)
        a_clean = clean_qa_text(a_txt)
        if is_valid_card(q_clean, a_clean) and len(a_clean) > 3:
            if not q_clean.endswith("?"):
                q_clean += "?"
            cards.append({"question": q_clean, "answer": a_clean})
    if cards:
        return deduplicate_cards(cards)

    # --- Tier 4: Dòng câu hỏi kết thúc ? + dòng đáp án ---
    for q_txt, a_txt in PATTERN_QUESTION_LINES.findall(text):
        q_clean = clean_qa_text(
            re.sub(
                r"^(?:\d+[\.]\s*|Q\s*:\s*|Question\s*:\s*|Câu hỏi\s*:\s*)",
                "",
                q_txt.strip(),
                flags=re.IGNORECASE,
            )
        )
        a_clean = clean_qa_text(
            re.sub(
                r"^(?:A\s*:\s*|Answer\s*:\s*|Đáp án\s*:\s*|Trả lời\s*:\s*)",
                "",
                a_txt.strip(),
                flags=re.IGNORECASE,
            )
        )
        if is_valid_card(q_clean, a_clean) and len(a_clean) > 3:
            if not q_clean.endswith("?"):
                q_clean += "?"
            cards.append({"question": q_clean, "answer": a_clean})
    if cards:
        return deduplicate_cards(cards)

    # --- Tier 5: Phân đoạn theo dòng trống ---
    segments = [s.strip() for s in re.split(r"\n\s*\n", text) if s.strip()]
    if len(segments) >= 2:
        it = iter(segments)
        for q_seg in it:
            a_seg = next(it, None)
            if a_seg:
                q_clean = clean_qa_text(
                    re.sub(r"^(?:[Qq](?:uestion)?|Q|Câu hỏi)[:\.\s]+", "", q_seg)
                    .strip()
                    .rstrip("?")
                    .strip()
                )
                a_clean = clean_qa_text(
                    re.sub(
                        r"^(?:[Aa](?:nswer)?|A|Câu trả lời|Đáp án)[:\.\s]+", "", a_seg
                    ).strip()
                )
                if is_valid_card(q_clean, a_clean) and len(a_clean) > 3:
                    cards.append({"question": q_clean + "?", "answer": a_clean})
        if cards:
            return deduplicate_cards(cards)

    # --- Tier 6 (Fallback cuối): tách theo dấu ? ---
    if "?" in text:
        parts = text.split("?", 1)
        q_clean = clean_qa_text(
            re.sub(
                r"^.*?(?:Q|Question|Câu hỏi)\s*[:\-]\s*",
                "",
                parts[0].strip(),
                flags=re.IGNORECASE | re.DOTALL,
            ).strip()
            or parts[0].strip()
        )
        a_lines = [ln.strip() for ln in parts[1].strip().split("\n") if ln.strip()]
        if a_lines:
            a_clean = clean_qa_text(
                re.sub(
                    r"^(?:A\s*:\s*|Answer\s*:\s*|Đáp án\s*:\s*)",
                    "",
                    a_lines[0],
                    flags=re.IGNORECASE,
                ).strip()
            )
            if is_valid_card(q_clean, a_clean) and len(a_clean) > 3:
                cards.append({"question": q_clean + "?", "answer": a_clean})

    return deduplicate_cards(cards)
