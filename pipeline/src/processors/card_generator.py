"""
card_generator.py — Flashcard generation pipeline sử dụng Qwen2.5-0.5B-Instruct (Causal LM, offline).

Public API:
    FlashcardPipeline                                       — model wrapper
    parse_flashcard_output(raw_output) -> list[dict]
    FlashcardPipeline.generate_from_chunk(text, max_cards) -> list[dict]
    FlashcardPipeline.generate_from_chunks(chunks, ...)    -> list[dict]
    FlashcardPipeline.generate_from_document(file_path)    -> list[dict]
"""

from __future__ import annotations

import csv
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Fix Windows console UTF-8 output encoding for Vietnamese characters
if sys.platform == "win32":
    stdout_reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(stdout_reconfigure):
        stdout_reconfigure(encoding="utf-8", errors="replace")
    stderr_reconfigure = getattr(sys.stderr, "reconfigure", None)
    if callable(stderr_reconfigure):
        stderr_reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Resolve project root
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent  # pipeline/src/processors/
_PIPELINE_DIR = _THIS_DIR.parent.parent  # pipeline/
if str(_PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(_PIPELINE_DIR))

# Chỉ hỗ trợ Qwen2.5 — không còn flan-t5-base
_DEFAULT_MODEL_DIR = str(_PIPELINE_DIR / "models_weights" / "qwen2.5-0.5b")


def _resolve_default_model_dir() -> str:
    """Đọc MODEL_PATH từ .env, fallback về qwen2.5-0.5b mặc định."""
    env_path = os.getenv("MODEL_PATH")
    if env_path:
        p = Path(env_path)
        if not p.is_absolute():
            p = _PIPELINE_DIR / p
        if p.exists():
            return str(p.resolve())
    return _DEFAULT_MODEL_DIR


# ---------------------------------------------------------------------------
# System Prompt cho Qwen Chat Template
# ---------------------------------------------------------------------------
_SYSTEM_PROMPT = (
    "Bạn là trợ lý AI chuyên tạo thẻ ghi nhớ (Flashcard) học tập bằng TIẾNG VIỆT.\n"
    "Nhiệm vụ: Trích xuất các ý chính từ văn bản và tạo tối đa {max_cards} thẻ ghi nhớ.\n"
    "BẮT BUỘC chỉ trả về kết quả dưới dạng một JSON Array thuần túy, "
    "không có văn bản giải thích nào khác:\n"
    "[\n"
    '  {{"question": "Câu hỏi bằng tiếng Việt?", "answer": "Đáp án ngắn gọn bằng tiếng Việt."}}\n'
    "]"
)

_USER_TEMPLATE = "Văn bản học tập:\n{text}"


def _build_chat_messages(chunk_text: str, max_cards: int) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": _SYSTEM_PROMPT.format(max_cards=max_cards),
        },
        {
            "role": "user",
            "content": _USER_TEMPLATE.format(text=chunk_text.strip()),
        },
    ]


# ---------------------------------------------------------------------------
# Multi-tier Flashcard Output Parser
# ---------------------------------------------------------------------------

# Tier 0b: JSON object fallback (regex scan từng object)
_PATTERN_JSON_OBJ = re.compile(
    r'\{\s*"question"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,\s*"answer"\s*:\s*"((?:[^"\\]|\\.)*)"\s*\}',
    re.DOTALL,
)

# Tier 1: "Q: ... A: ..." hoặc "Question: ... Answer: ..."
_PATTERN_EN_QA = re.compile(
    r"(?:Q(?:uestion)?)\s*[:\-]\s*(.+?)\s*(?:A(?:nswer)?)\s*[:\-]\s*(.+?)(?=\n\s*(?:Q(?:uestion)?)\s*[:\-]|$)",
    re.DOTALL | re.IGNORECASE,
)

# Tier 2: "Câu hỏi: ... Đáp án: ..." (tiếng Việt)
_PATTERN_VI_QA = re.compile(
    r"(?:Câu hỏi|CH)\s*[:\-]\s*(.+?)\s*(?:Đáp án|Trả lời|ĐA)\s*[:\-]\s*(.+?)(?=\n\s*(?:Câu hỏi|CH)\s*[:\-]|$)",
    re.DOTALL | re.IGNORECASE,
)

# Tier 3: Dòng kết thúc ? + dòng ngay sau
_PATTERN_QUESTION_LINES = re.compile(
    r"^(.+\?)\s*\n\s*([^\n?]+?)(?=\n|$)",
    re.MULTILINE,
)

# Tier 4: Cặp đánh số "1. Câu hỏi? Đáp án."
_PATTERN_NUMBERED = re.compile(
    r"\d+[\.]\s*(.+?\?)\s*\n\s*(.+?)(?=\n\s*\d+[\.]|$)",
    re.DOTALL,
)


def parse_flashcard_output(raw_output: str) -> list[dict[str, str]]:
    """
    Parser đa tầng: JSON array → JSON object scan → Q/A labeled → numbered → fallback.

    Bắt buộc log raw output để debug.
    """
    cards: list[dict[str, str]] = []
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
                        q = str(item.get("question", "")).strip()
                        a = str(item.get("answer", "")).strip()
                        if q and a:
                            if not q.endswith("?"):
                                q += "?"
                            cards.append({"question": q, "answer": a})
                if cards:
                    return _deduplicate(cards)
        except json.JSONDecodeError:
            pass

    # --- Tier 0b: JSON objects scan (fallback nếu array parse thất bại) ---
    for q_txt, a_txt in _PATTERN_JSON_OBJ.findall(text):
        q_clean = q_txt.strip()
        a_clean = a_txt.strip()
        if q_clean and a_clean:
            if not q_clean.endswith("?"):
                q_clean += "?"
            cards.append({"question": q_clean, "answer": a_clean})
    if cards:
        return _deduplicate(cards)

    # --- Tier 1: EN labeled Q/A ---
    for q_txt, a_txt in _PATTERN_EN_QA.findall(text):
        q_clean = q_txt.strip().rstrip("?").strip()
        a_clean = a_txt.strip()
        if q_clean and a_clean and len(a_clean) > 3:
            cards.append({"question": q_clean + "?", "answer": a_clean})
    if cards:
        return _deduplicate(cards)

    # --- Tier 2: VI labeled Q/A ---
    for q_txt, a_txt in _PATTERN_VI_QA.findall(text):
        q_clean = q_txt.strip().rstrip("?").strip()
        a_clean = a_txt.strip()
        if q_clean and a_clean and len(a_clean) > 3:
            cards.append({"question": q_clean + "?", "answer": a_clean})
    if cards:
        return _deduplicate(cards)

    # --- Tier 3: Numbered pairs ---
    for q_txt, a_txt in _PATTERN_NUMBERED.findall(text):
        q_clean = q_txt.strip()
        a_clean = a_txt.strip()
        if q_clean and a_clean and len(a_clean) > 3:
            if not q_clean.endswith("?"):
                q_clean += "?"
            cards.append({"question": q_clean, "answer": a_clean})
    if cards:
        return _deduplicate(cards)

    # --- Tier 4: Dòng câu hỏi kết thúc ? + dòng đáp án ---
    for q_txt, a_txt in _PATTERN_QUESTION_LINES.findall(text):
        q_clean = re.sub(
            r"^(?:\d+[\.]\s*|Q\s*:\s*|Question\s*:\s*|Câu hỏi\s*:\s*)",
            "",
            q_txt.strip(),
            flags=re.IGNORECASE,
        ).strip()
        a_clean = re.sub(
            r"^(?:A\s*:\s*|Answer\s*:\s*|Đáp án\s*:\s*|Trả lời\s*:\s*)",
            "",
            a_txt.strip(),
            flags=re.IGNORECASE,
        ).strip()
        if q_clean and a_clean and len(a_clean) > 3:
            if not q_clean.endswith("?"):
                q_clean += "?"
            cards.append({"question": q_clean, "answer": a_clean})
    if cards:
        return _deduplicate(cards)

    # --- Tier 5: Phân đoạn theo dòng trống ---
    segments = [s.strip() for s in re.split(r"\n\s*\n", text) if s.strip()]
    if len(segments) >= 2:
        it = iter(segments)
        for q_seg in it:
            a_seg = next(it, None)
            if a_seg:
                q_clean = (
                    re.sub(r"^(?:[Qq](?:uestion)?|Q|Câu hỏi)[:\.\s]+", "", q_seg)
                    .strip()
                    .rstrip("?")
                    .strip()
                )
                a_clean = re.sub(
                    r"^(?:[Aa](?:nswer)?|A|Câu trả lời|Đáp án)[:\.\s]+", "", a_seg
                ).strip()
                if q_clean and a_clean and len(a_clean) > 3:
                    cards.append({"question": q_clean + "?", "answer": a_clean})
        if cards:
            return _deduplicate(cards)

    # --- Tier 6 (Fallback cuối): tách theo dấu ? ---
    if "?" in text:
        parts = text.split("?", 1)
        q_clean = (
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
            a_clean = re.sub(
                r"^(?:A\s*:\s*|Answer\s*:\s*|Đáp án\s*:\s*)",
                "",
                a_lines[0],
                flags=re.IGNORECASE,
            ).strip()
            if q_clean and a_clean and len(a_clean) > 3:
                cards.append({"question": q_clean + "?", "answer": a_clean})

    return _deduplicate(cards)


def _deduplicate(cards: list[dict[str, str]]) -> list[dict[str, str]]:
    """Loại bỏ thẻ trùng lặp dựa trên câu hỏi đã chuẩn hóa."""
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for card in cards:
        key = card["question"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(card)
    return unique


# ---------------------------------------------------------------------------
# FlashcardPipeline — Qwen2.5 CausalLM (offline)
# ---------------------------------------------------------------------------
class FlashcardPipeline:
    """
    Pipeline offline chạy Qwen2.5-0.5B-Instruct (Causal LM / Decoder-only)
    để sinh flashcard tiếng Việt dạng JSON.
    """

    _tokenizer: Any
    _model: Any
    _device: Any
    _model_name: str

    def __init__(
        self,
        model_path: str | None = None,
        local_files_only: bool = True,
    ) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        selected_path = model_path or _resolve_default_model_dir()
        resolved_path = str(Path(selected_path).resolve())

        if local_files_only and not Path(resolved_path).exists():
            raise FileNotFoundError(
                f"Thư mục weights không tồn tại: {resolved_path}. "
                "Vui lòng chạy: cd pipeline && python src/download_model.py"
            )

        self._model_name = Path(resolved_path).name
        print(f"[*] Đang nạp Qwen2.5 model từ: {resolved_path}")
        logger.info(
            "Nạp model '%s' (local_files_only=%s)", self._model_name, local_files_only
        )

        self._tokenizer = AutoTokenizer.from_pretrained(
            resolved_path,
            local_files_only=local_files_only,
            trust_remote_code=True,
        )

        self._model = AutoModelForCausalLM.from_pretrained(
            resolved_path,
            local_files_only=local_files_only,
            torch_dtype=torch.float32,
            trust_remote_code=True,
        )

        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._model.to(self._device)
        self._model.eval()

        # Qwen pad token = eos token
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

        print(f"[OK] Model '{self._model_name}' sẵn sàng. Device: {self._device}")

    def _build_prompt(self, chunk_text: str, max_cards: int = 3) -> str:
        """Xây dựng prompt sử dụng Qwen Chat Template (system + user messages)."""
        messages = _build_chat_messages(chunk_text, max_cards)
        if (
            hasattr(self._tokenizer, "apply_chat_template")
            and self._tokenizer.chat_template
        ):
            try:
                return self._tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
            except Exception as e:
                logger.warning("apply_chat_template thất bại: %s — dùng raw prompt.", e)

        # Fallback: ghép thủ công nếu không có chat_template
        sys_content = messages[0]["content"]
        user_content = messages[1]["content"]
        return (
            f"<|im_start|>system\n{sys_content}<|im_end|>\n"
            f"<|im_start|>user\n{user_content}<|im_end|>\n"
            "<|im_start|>assistant\n"
        )

    def _infer(self, chunk_text: str, max_cards: int = 3) -> str:
        """
        Thực thi suy luận single-chunk với Qwen2.5 CausalLM.

        Cắt bỏ phần prompt từ output, chỉ giữ phần model sinh ra.
        """
        import torch

        prompt = self._build_prompt(chunk_text, max_cards=max_cards)
        inputs = self._tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=1024,  # Qwen2.5 context window lớn hơn T5
        ).to(self._device)

        input_len = inputs.input_ids.shape[1]

        gen_kwargs: dict[str, Any] = {
            "max_new_tokens": 300,
            "do_sample": False,  # greedy — ổn định nhất cho JSON
            "temperature": 0.1,
            "repetition_penalty": 1.1,
            "pad_token_id": self._tokenizer.pad_token_id
            or self._tokenizer.eos_token_id,
            "eos_token_id": self._tokenizer.eos_token_id,
        }

        with torch.no_grad():
            output_ids = self._model.generate(**inputs, **gen_kwargs)

        # Cắt bỏ phần prompt input, chỉ decode phần model sinh ra
        generated_tokens = output_ids[0][input_len:]
        raw_text = self._tokenizer.decode(generated_tokens, skip_special_tokens=True)

        # BẮT BUỘC: log raw output để debug
        print(f"[DEBUG RAW MODEL OUTPUT]:\n{raw_text}")
        logger.info(
            "[DEBUG RAW MODEL OUTPUT for chunk '%s...']:\n%s",
            chunk_text[:60],
            raw_text,
        )

        return raw_text

    @staticmethod
    def parse_flashcard_output(raw_output: str) -> list[dict[str, str]]:
        return parse_flashcard_output(raw_output)

    def generate_from_chunk(
        self, chunk_text: str, max_cards: int = 3
    ) -> list[dict[str, str]]:
        """Sinh flashcards từ một đoạn văn bản đơn lẻ."""
        if not chunk_text or not chunk_text.strip():
            return []
        raw = self._infer(chunk_text, max_cards=max_cards)
        if not raw:
            logger.warning("[WARN] Model trả về chuỗi rỗng: '%s...'", chunk_text[:60])
            return []
        cards = parse_flashcard_output(raw)
        logger.info(
            "[generate_from_chunk] '%s...' → %d cards", chunk_text[:60], len(cards)
        )
        return cards

    def generate_from_chunks(
        self,
        chunks: list[str],
        batch_size: int = 1,  # Qwen CPU: 1 chunk/lần để tránh OOM
        max_cards_per_chunk: int = 3,
    ) -> list[dict[str, str]]:
        """Sinh flashcards tuần tự từ danh sách chunks."""
        if not chunks:
            return []

        all_cards: list[dict[str, str]] = []
        seen_questions: set[str] = set()

        for idx, chunk in enumerate(chunks):
            logger.info("[Chunk %d/%d] Đang xử lý...", idx + 1, len(chunks))
            raw = self._infer(chunk, max_cards=max_cards_per_chunk)
            cards = parse_flashcard_output(raw)
            logger.info(
                "[Chunk %d/%d] → %d cards | raw_len=%d chars",
                idx + 1,
                len(chunks),
                len(cards),
                len(raw),
            )
            for card in cards:
                key = card["question"].lower().strip()
                if key not in seen_questions:
                    seen_questions.add(key)
                    all_cards.append(card)

        logger.info("Tổng thẻ từ %d chunks: %d", len(chunks), len(all_cards))
        return all_cards

    def generate_from_document(
        self,
        file_path: str,
        max_words_per_chunk: int = 150,
        batch_size: int = 1,
        max_cards: int | None = None,
    ) -> list[dict[str, str]]:
        """Pipeline trọn gói: Đọc file → Tiền xử lý → Chunk → Sinh thẻ."""
        try:
            from ..cleaners.text_cleaner import load_document, clean_text, chunk_text
        except (ImportError, ValueError):
            try:
                from src.cleaners.text_cleaner import (
                    load_document,
                    clean_text,
                    chunk_text,
                )
            except ImportError:
                from pipeline.src.cleaners.text_cleaner import (
                    load_document,
                    clean_text,
                    chunk_text,
                )

        raw_text = load_document(file_path)
        cleaned = clean_text(raw_text)
        if not cleaned or not cleaned.strip():
            return []

        chunks = chunk_text(cleaned, max_words=max_words_per_chunk)
        if not chunks:
            return []

        cards = self.generate_from_chunks(chunks, batch_size=batch_size)
        if max_cards and max_cards > 0:
            cards = cards[:max_cards]
        return cards

    @staticmethod
    def export_to_file(
        cards: list[dict[str, Any]],
        output_path: str,
        format: str = "json",
    ) -> str:
        """Xuất danh sách thẻ ra file JSON hoặc CSV chuẩn UTF-8."""
        fmt = format.lower().strip()
        if fmt not in ("json", "csv"):
            raise ValueError(
                f"Định dạng không hỗ trợ: '{format}'. Chỉ chấp nhận 'json' hoặc 'csv'."
            )

        resolved_path = os.path.abspath(output_path)
        parent_dir = os.path.dirname(resolved_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        if fmt == "json":
            with open(resolved_path, "w", encoding="utf-8") as f:
                json.dump(cards, f, ensure_ascii=False, indent=2)
        elif fmt == "csv":
            with open(resolved_path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(
                    f, fieldnames=["id", "question", "answer"], extrasaction="ignore"
                )
                writer.writeheader()
                for idx, card in enumerate(cards, start=1):
                    writer.writerow(
                        {
                            "id": card.get("id", idx),
                            "question": card.get("question", ""),
                            "answer": card.get("answer", ""),
                        }
                    )

        logger.info("Đã xuất %d thẻ ra %s (format=%s)", len(cards), resolved_path, fmt)
        return resolved_path
