"""
download_model.py — Tải weights Qwen2.5-0.5B-Instruct từ Hugging Face về máy để chạy offline.

Usage:
    cd pipeline
    python src/download_model.py
    python src/download_model.py --model Qwen/Qwen2.5-0.5B-Instruct --output-dir models_weights/qwen2.5-0.5b
"""

import argparse
import os
import sys
from pathlib import Path

from transformers import AutoModelForCausalLM, AutoTokenizer

# Fix Windows console UTF-8 output encoding for Vietnamese characters
if sys.platform == "win32":
    stdout_reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(stdout_reconfigure):
        stdout_reconfigure(encoding="utf-8", errors="replace")
    stderr_reconfigure = getattr(sys.stderr, "reconfigure", None)
    if callable(stderr_reconfigure):
        stderr_reconfigure(encoding="utf-8", errors="replace")

DEFAULT_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
_PIPELINE_DIR = Path(__file__).resolve().parent.parent  # pipeline/
DEFAULT_SAVE_DIR = _PIPELINE_DIR / "models_weights" / "qwen2.5-0.5b"


def download(
    model_id: str = DEFAULT_MODEL, target_dir: str | Path | None = None
) -> Path:
    """Tải và lưu tokenizer + model Qwen2.5 CausalLM về máy để chạy hoàn toàn offline."""
    if target_dir is None:
        target_path = DEFAULT_SAVE_DIR
    else:
        target_path = Path(target_dir).resolve()

    target_path.mkdir(parents=True, exist_ok=True)
    print(f"[*] Bắt đầu tải model '{model_id}' về: {target_path}")
    print("[*] Kiến trúc: Causal LM (Decoder-only) — Qwen2.5-0.5B-Instruct")
    print("[*] Dung lượng ước tính: ~950 MB — vui lòng đợi...")

    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    print("[+] Tokenizer tải xong.")

    model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True)
    print("[+] Model weights tải xong.")

    tokenizer.save_pretrained(str(target_path))
    model.save_pretrained(str(target_path))
    print(f"[+] Tải thành công! Weights lưu tại: {target_path}")
    print("[*] Lệnh khởi động service: python -m app.main")
    return target_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Tải model Qwen2.5-0.5B-Instruct offline từ Hugging Face Hub"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help="Model ID trên Hugging Face Hub (mặc định: Qwen/Qwen2.5-0.5B-Instruct)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Thư mục lưu weights (mặc định: pipeline/models_weights/qwen2.5-0.5b/)",
    )
    args = parser.parse_args()
    download(model_id=args.model, target_dir=args.output_dir)
