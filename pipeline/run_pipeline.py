"""
run_pipeline.py — CLI entrypoint for Flashcard AI pipeline.

Usage:
    python run_pipeline.py --input data/raw/sample.txt --output data/processed/cards.json --format json
    python run_pipeline.py --text "Quang hợp là quá trình..." --max-cards 3
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

# Fix Windows console UTF-8 output encoding for Vietnamese characters
if sys.platform == "win32":
    stdout_reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(stdout_reconfigure):
        stdout_reconfigure(encoding="utf-8", errors="replace")
    stderr_reconfigure = getattr(sys.stderr, "reconfigure", None)
    if callable(stderr_reconfigure):
        stderr_reconfigure(encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Path resolution: allow execution from project root or pipeline directory
# ---------------------------------------------------------------------------
_THIS_DIR = Path(__file__).resolve().parent  # pipeline/
_PROJECT_ROOT = _THIS_DIR.parent  # project root

for _p in [str(_THIS_DIR), str(_PROJECT_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from src import FlashcardPipeline, clean_text, chunk_text, load_document
except ImportError:
    from pipeline.src import FlashcardPipeline, clean_text, chunk_text, load_document

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("run_pipeline")


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------
def _resolve_input_path(path_str: str) -> Path:
    """Resolve input file path relative to current dir or pipeline dir."""
    p = Path(path_str)
    if p.exists():
        return p.resolve()
    candidate = _THIS_DIR / path_str
    if candidate.exists():
        return candidate.resolve()
    return p.resolve()


def _resolve_output_path(path_str: str, fmt: str) -> Path:
    """Resolve output file path and auto-align extension if using defaults."""
    p = Path(path_str)
    if fmt == "csv" and p.name == "cards.json":
        p = p.with_name("cards.csv")

    if p.is_absolute():
        return p

    if not p.parent.exists() and (_THIS_DIR / p).parent.exists():
        return (_THIS_DIR / p).resolve()

    return p.resolve()


# ---------------------------------------------------------------------------
# Summary Table Printer
# ---------------------------------------------------------------------------
def _print_summary(
    input_file: Path | str,
    output_file: Path | None,
    output_format: str,
    chunk_count: int,
    card_count: int,
    t_read: float,
    t_clean: float,
    t_load: float,
    t_infer: float,
    t_total: float,
    sample_cards: list[dict[str, str]],
) -> None:
    """Print performance metrics and preview table."""
    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()

        t_perf = Table(
            title="Pipeline Performance Summary",
            show_header=True,
            header_style="bold cyan",
        )
        t_perf.add_column("Metric", style="dim", width=28)
        t_perf.add_column("Value", style="green")

        t_perf.add_row("Input Source", str(input_file))
        if output_file:
            t_perf.add_row("Output File", str(output_file))
        t_perf.add_row("Output Format", output_format.upper())
        t_perf.add_row("Chunks Processed", str(chunk_count))
        t_perf.add_row("Flashcards Generated", str(card_count))
        t_perf.add_row("Document Load Time", f"{t_read:.3f}s")
        t_perf.add_row("Clean & Chunk Time", f"{t_clean:.3f}s")
        t_perf.add_row("Model Load Time", f"{t_load:.3f}s")
        t_perf.add_row("Inference Time", f"{t_infer:.3f}s")
        t_perf.add_row("Total Time", f"{t_total:.3f}s")
        console.print(t_perf)

        if sample_cards:
            t_cards = Table(
                title=f"Sample Flashcards ({len(sample_cards)} previewed)",
                show_header=True,
                header_style="bold magenta",
            )
            t_cards.add_column("#", style="dim", width=4)
            t_cards.add_column("Question", style="yellow", width=40)
            t_cards.add_column("Answer", style="white", width=40)
            for idx, c in enumerate(sample_cards, 1):
                t_cards.add_row(str(idx), c.get("question", ""), c.get("answer", ""))
            console.print(t_cards)

    except ImportError:
        border = "-" * 60
        print(f"\n{border}")
        print("  PIPELINE PERFORMANCE SUMMARY")
        print(border)
        print(f"| Input Source                | {str(input_file)[:40]:<40} |")
        if output_file:
            print(f"| Output File                 | {str(output_file)[:40]:<40} |")
        print(f"| Output Format               | {output_format.upper():<40} |")
        print(f"| Text Chunks                 | {str(chunk_count):<40} |")
        print(f"| Cards Generated             | {str(card_count):<40} |")
        print(f"| Model Load Time             | {f'{t_load:.2f}s':<40} |")
        print(f"| Inference Time              | {f'{t_infer:.2f}s':<40} |")
        print(f"| Total Elapsed Time          | {f'{t_total:.2f}s':<40} |")
        print(f"{border}\n")


# ---------------------------------------------------------------------------
# CLI Argument Parser
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Flashcard AI Pipeline CLI Runner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--text",
        "-t",
        type=str,
        default=None,
        help="Chuỗi văn bản bài học trực tiếp (bỏ qua đọc file)",
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="data/raw/sample.txt",
        help="Đường dẫn file tài liệu đầu vào (.txt hoặc .pdf)",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="data/processed/cards.json",
        help="Đường dẫn file lưu kết quả",
    )
    parser.add_argument(
        "--model-path",
        "-m",
        type=str,
        default=None,
        help="Đường dẫn thư mục model weights offline",
    )
    parser.add_argument(
        "--format",
        "-f",
        type=str,
        choices=["json", "csv"],
        default="json",
        help="Định dạng xuất (json hoặc csv)",
    )
    parser.add_argument(
        "--chunk-size",
        "-c",
        type=int,
        default=120,
        help="Số từ tối đa mỗi chunk",
    )
    parser.add_argument(
        "--max-cards",
        type=int,
        default=5,
        help="Số lượng thẻ tối đa cần sinh",
    )
    parser.add_argument(
        "--batch-size",
        "-b",
        type=int,
        default=4,
        help="Kích thước batch khi chạy suy luận",
    )
    parser.add_argument(
        "--preview",
        "-p",
        type=int,
        default=3,
        help="Số thẻ mẫu hiển thị trong bảng tóm tắt",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main Runner
# ---------------------------------------------------------------------------
def main() -> None:
    args = parse_args()

    t_start_total = time.perf_counter()
    output_path = None
    input_source_desc = ""

    if args.text:
        input_source_desc = "<CLI inline text>"
        raw_text = args.text
        t_read = 0.0
    else:
        input_path = _resolve_input_path(args.input)
        if not input_path.exists():
            print(f"[ERROR] Không tìm thấy file đầu vào: {input_path}")
            sys.exit(1)
        input_source_desc = str(input_path)
        t_read_start = time.perf_counter()
        raw_text = load_document(str(input_path))
        t_read = time.perf_counter() - t_read_start

    print("=" * 65)
    print("  OFFLINE FLASHCARD GENERATION PIPELINE")
    print("=" * 65)
    print(f"[*] Nguồn dữ liệu: {input_source_desc}")
    print(f"[*] Chunk size   : {args.chunk_size} words")
    print(f"[*] Max cards    : {args.max_cards}")

    # 1. Làm sạch & chia chunk
    t_clean_start = time.perf_counter()
    cleaned = clean_text(raw_text)
    if not cleaned:
        print("[ERROR] Văn bản sau khi làm sạch bị rỗng. Dừng pipeline.")
        sys.exit(1)

    chunks = chunk_text(cleaned, max_words=args.chunk_size)
    if not chunks:
        chunks = [cleaned[:500]]
    t_clean = time.perf_counter() - t_clean_start
    print(f"[1/4] Làm sạch xong ({len(chunks)} chunks, {t_clean:.3f}s)")

    # 2. Khởi tạo mô hình
    print("[2/4] Nạp mô hình AI...")
    t_load_start = time.perf_counter()
    pipeline = FlashcardPipeline(model_path=args.model_path, local_files_only=True)
    t_load = time.perf_counter() - t_load_start

    # 3. Suy luận
    print(f"[3/4] Chạy suy luận (batch_size={args.batch_size})...")
    t_infer_start = time.perf_counter()
    cards = pipeline.generate_from_chunks(
        chunks,
        batch_size=args.batch_size,
        max_cards_per_chunk=args.max_cards,
    )
    if args.max_cards and args.max_cards > 0:
        cards = cards[: args.max_cards]
    t_infer = time.perf_counter() - t_infer_start

    # 4. Xuất kết quả
    if not args.text or args.output:
        output_path = _resolve_output_path(args.output, args.format)
        pipeline.export_to_file(
            cards=cards,
            output_path=str(output_path),
            format=args.format,
        )
        print(f"[4/4] Đã lưu kết quả tại: {output_path}")

    t_total = time.perf_counter() - t_start_total

    # Xuất định dạng JSON chuẩn theo schema
    response_payload = {
        "count": len(cards),
        "cards": cards,
        "inference_time_seconds": round(t_infer, 2),
    }

    print("\n--- JSON OUTPUT ---")
    print(json.dumps(response_payload, ensure_ascii=False, indent=2))

    sample_preview = cards[: min(args.preview, len(cards))]
    _print_summary(
        input_file=input_source_desc,
        output_file=output_path,
        output_format=args.format,
        chunk_count=len(chunks),
        card_count=len(cards),
        t_read=t_read,
        t_clean=t_clean,
        t_load=t_load,
        t_infer=t_infer,
        t_total=t_total,
        sample_cards=sample_preview,
    )


if __name__ == "__main__":
    main()
