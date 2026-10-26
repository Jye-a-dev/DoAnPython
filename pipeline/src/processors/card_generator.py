"""
card_generator.py — Flashcard generation pipeline using Qwen2.5-0.5B-Instruct (Causal LM, offline).
Refactored to orchestrate parser, prompt templates, and exporter components.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Component imports
from .exporter import export_cards_to_file
from .parser import deduplicate_cards, parse_flashcard_output
from .prompts import SYSTEM_PROMPT, USER_TEMPLATE, build_chat_messages

# Backward compatibility aliases
_SYSTEM_PROMPT = SYSTEM_PROMPT
_USER_TEMPLATE = USER_TEMPLATE
_build_chat_messages = build_chat_messages

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

        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

        print(f"[OK] Model '{self._model_name}' sẵn sàng. Device: {self._device}")

    def _build_prompt(self, chunk_text: str, max_cards: int = 3) -> str:
        """Xây dựng prompt sử dụng Qwen Chat Template."""
        messages = build_chat_messages(chunk_text, max_cards)
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

        sys_content = messages[0]["content"]
        user_content = messages[1]["content"]
        return (
            f"<|im_start|>system\n{sys_content}<|im_end|>\n"
            f"<|im_start|>user\n{user_content}<|im_end|>\n"
            "<|im_start|>assistant\n"
        )

    def _infer(self, chunk_text: str, max_cards: int = 3) -> str:
        """Thực thi suy luận single-chunk với Qwen2.5 CausalLM."""
        import torch

        prompt = self._build_prompt(chunk_text, max_cards=max_cards)
        inputs = self._tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=1024,
        ).to(self._device)

        input_len = inputs.input_ids.shape[1]
        gen_kwargs: Dict[str, Any] = {
            "max_new_tokens": min(350, max(120, max_cards * 120)),
            "do_sample": False,
            "repetition_penalty": 1.1,
            "pad_token_id": self._tokenizer.pad_token_id
            or self._tokenizer.eos_token_id,
            "eos_token_id": self._tokenizer.eos_token_id,
        }

        with torch.no_grad():
            output_ids = self._model.generate(**inputs, **gen_kwargs)

        generated_tokens = output_ids[0][input_len:]
        raw_text = self._tokenizer.decode(generated_tokens, skip_special_tokens=True)

        print(f"[DEBUG RAW MODEL OUTPUT]:\n{raw_text}")
        logger.info(
            "[DEBUG RAW MODEL OUTPUT for chunk '%s...']:\n%s",
            chunk_text[:60],
            raw_text,
        )
        return raw_text

    @staticmethod
    def parse_flashcard_output(raw_output: str) -> List[Dict[str, str]]:
        return parse_flashcard_output(raw_output)

    def generate_from_chunk(
        self, chunk_text: str, max_cards: int = 3
    ) -> List[Dict[str, str]]:
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
        chunks: List[str],
        batch_size: int = 1,
        max_cards_per_chunk: int = 3,
        total_max_cards: Optional[int] = None,
    ) -> List[Dict[str, str]]:
        """Sinh flashcards tuần tự từ danh sách chunks."""
        if not chunks:
            return []

        all_cards: List[Dict[str, str]] = []
        seen_questions: set[str] = set()

        for idx, chunk in enumerate(chunks):
            if total_max_cards and len(all_cards) >= total_max_cards:
                break
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
                if total_max_cards and len(all_cards) >= total_max_cards:
                    break

        logger.info("Tổng thẻ từ %d chunks: %d", len(chunks), len(all_cards))
        return all_cards

    def generate_from_document(
        self,
        file_path: str,
        max_words_per_chunk: int = 150,
        batch_size: int = 1,
        max_cards: Optional[int] = None,
    ) -> List[Dict[str, str]]:
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

    def generate(
        self,
        text: str,
        max_cards: int = 3,
        max_words_per_chunk: int = 120,
    ) -> List[Dict[str, str]]:
        """Sinh danh sách thẻ Flashcard từ văn bản bài học."""
        clean_input = text.strip() if text else ""
        if not clean_input:
            logger.warning("[generate] Input text rỗng.")
            return []

        logger.info(f"[INPUT TEXT]: {text[:80]}...")

        try:
            from ..cleaners.text_cleaner import clean_text, chunk_text
        except (ImportError, ValueError):
            try:
                from src.cleaners.text_cleaner import clean_text, chunk_text
            except ImportError:
                from pipeline.src.cleaners.text_cleaner import clean_text, chunk_text

        cleaned = clean_text(clean_input)
        chunks = chunk_text(cleaned, max_words=max_words_per_chunk)
        if not chunks:
            chunks = [cleaned[:1024]] if cleaned else []

        cards_data: List[Dict[str, str]] = self.generate_from_chunks(
            chunks,
            max_cards_per_chunk=max_cards,
            total_max_cards=max_cards,
        )

        if max_cards and max_cards > 0:
            cards_data = cards_data[:max_cards]

        logger.info(f"[MODEL OUTPUT CARDS]: {cards_data}")
        return cards_data

    @staticmethod
    def export_to_file(
        cards: List[Dict[str, Any]],
        output_path: str,
        format: str = "json",
    ) -> str:
        return export_cards_to_file(cards, output_path, format=format)


# ---------------------------------------------------------------------------
# Module-level proxy for functional execution
# ---------------------------------------------------------------------------
_default_pipeline: FlashcardPipeline | None = None


def get_default_pipeline() -> FlashcardPipeline:
    global _default_pipeline
    if _default_pipeline is None:
        _default_pipeline = FlashcardPipeline(model_path=_resolve_default_model_dir())
    return _default_pipeline


def generate(
    text: str,
    max_cards: int = 3,
    max_words_per_chunk: int = 120,
) -> List[Dict[str, str]]:
    """Module-level generator proxy."""
    pipeline = get_default_pipeline()
    return pipeline.generate(
        text=text,
        max_cards=max_cards,
        max_words_per_chunk=max_words_per_chunk,
    )
