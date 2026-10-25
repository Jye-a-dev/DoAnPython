"""Quick test script for parse_flashcard_output — no model required."""

import sys

sys.path.insert(0, r"d:\Code\doAnpython\pipeline")

from src.processors.card_generator import parse_flashcard_output

# Flan-T5 điển hình: Q/A labeled tiếng Anh
RAW_T5_EN = """Q: What is photosynthesis?
A: The process by which plants use sunlight to produce food.
Q: Where does photosynthesis occur?
A: In the chloroplasts of plant cells.
Q: What is the main product of photosynthesis?
A: Glucose and oxygen."""

# Flan-T5 tiếng Việt: Câu hỏi/Đáp án
RAW_T5_VI = """Câu hỏi: Quang hợp là gì?
Đáp án: Là quá trình thực vật sử dụng ánh sáng mặt trời để tổng hợp chất hữu cơ.
Câu hỏi: Quang hợp xảy ra ở đâu?
Đáp án: Trong lục lạp của tế bào thực vật."""

# JSON array (Qwen output)
RAW_JSON = '[{"question": "What is photosynthesis?", "answer": "Plants convert sunlight to food."}]'

# Câu hỏi + đáp án trên dòng liền kề
RAW_LINES = """What is the role of chlorophyll in photosynthesis?
Chlorophyll absorbs light energy and converts it into chemical energy."""

# Output lộn xộn — chỉ có câu hỏi dấu ? và text sau
RAW_FALLBACK = "Photosynthesis occurs in which organelle? The chloroplast is the site of photosynthesis."

# Flan-T5 dạng "Question: ... Answer: ..." (chữ đầy đủ)
RAW_T5_FULL = """Question: What pigment is responsible for photosynthesis?
Answer: Chlorophyll absorbs red and blue light for photosynthesis.
Question: What gas is released during photosynthesis?
Answer: Oxygen is released as a byproduct."""

TESTS = [
    ("T5 EN Q/A labeled (Q:/A:)", RAW_T5_EN, 3),
    ("T5 VI Câu hỏi/Đáp án", RAW_T5_VI, 2),
    ("JSON array (Qwen)", RAW_JSON, 1),
    ("Question-Answer bare lines", RAW_LINES, 1),
    ("Fallback single ?", RAW_FALLBACK, 1),
    ("T5 Question:/Answer: full", RAW_T5_FULL, 2),
]

all_pass = True
for name, raw, expected_min in TESTS:
    cards = parse_flashcard_output(raw)
    ok = len(cards) >= expected_min
    if not ok:
        all_pass = False
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}: {len(cards)} cards (expected >= {expected_min})")
    for c in cards:
        print(f"       Q: {c['question'][:80]}")
        print(f"       A: {c['answer'][:80]}")

print()
print("=" * 50)
print("All tests PASSED!" if all_pass else "SOME TESTS FAILED!")
