"""
run_pipeline.py — CLI entrypoint for Flan-T5 flashcard pipeline.

Usage:
    python run_pipeline.py --input data/raw/sample.txt --output data/processed/cards.json --format json --chunk-size 150
"""

from __future__ import annotations

import argparse
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
    input_file: Path,
    output_file: Path,
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

        table = Table(
            title="[bold green]PIPELINE EXECUTION SUMMARY[/bold green]",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Metric", style="bold white", width=28)
        table.add_column("Value", style="yellow")

        table.add_row("Input File", str(input_file))
        table.add_row("Output File", str(output_file))
        table.add_row("Output Format", output_format.upper())
        table.add_row("Text Chunks", str(chunk_count))
        table.add_row("Cards Generated", f"[bold green]{card_count}[/bold green]")
        table.add_row("Read & Clean Time", f"{t_read + t_clean:.2f}s")
        table.add_row("Model Load Time", f"{t_load:.2f}s")
        table.add_row("Batch Inference Time", f"{t_infer:.2f}s")
        table.add_row("Total Elapsed Time", f"[bold cyan]{t_total:.2f}s[/bold cyan]")

        console.print()
        console.print(table)

        if sample_cards:
            preview_table = Table(
                title=f"Sample Flashcards (Preview {len(sample_cards)} of {card_count})",
                show_header=True,
                header_style="bold magenta",
                show_lines=True,
            )
            preview_table.add_column("#", style="dim", width=4)
            preview_table.add_column("Question", style="cyan")
            preview_table.add_column("Answer", style="green")

            for idx, c in enumerate(sample_cards, start=1):
                preview_table.add_row(str(idx), c["question"], c["answer"])

            console.print()
            console.print(preview_table)
            console.print()

    except ImportError:
        # Fallback to standard formatted ASCII output
        border = "+-----------------------------+----------------------------------------------------+"
        print(f"\n{border}")
        print(
            "| METRIC                      | VALUE                                              |"
        )
        print(border)
        print(f"| Input File                  | {str(input_file)[:50]:<50} |")
        print(f"| Output File                 | {str(output_file)[:50]:<50} |")
        print(f"| Output Format               | {output_format.upper():<50} |")
        print(f"| Text Chunks                 | {str(chunk_count):<50} |")
        print(f"| Cards Generated             | {str(card_count):<50} |")
        print(f"| Model Load Time             | {f'{t_load:.2f}s':<50} |")
        print(f"| Inference Time              | {f'{t_infer:.2f}s':<50} |")
        print(f"| Total Elapsed Time          | {f'{t_total:.2f}s':<50} |")
        print(f"{border}\n")


# ---------------------------------------------------------------------------
# CLI Argument Parser
# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Flan-T5 Flashcard Pipeline CLI Runner",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
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
        default=150,
        help="Số từ tối đa mỗi chunk",
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

    input_path = _resolve_input_path(args.input)
    if not input_path.exists():
        print(f"[ERROR] Không tìm thấy file đầu vào: {input_path}")
        sys.exit(1)

    output_path = _resolve_output_path(args.output, args.format)

    print("=" * 65)
    print("  FLAN-T5 FLASHCARD GENERATION PIPELINE")
    print("=" * 65)
    print(f"[*] Input file : {input_path}")
    print(f"[*] Output file: {output_path}")
    print(f"[*] Format     : {args.format.upper()}")
    print(f"[*] Chunk size : {args.chunk_size} words")
    print(f"[*] Batch size : {args.batch_size}")

    t_start_total = time.perf_counter()

    # 1. Đọc file
    print("\n[1/5] Đang đọc file tài liệu đầu vào...")
    t_read_start = time.perf_counter()
    raw_text = load_document(str(input_path))
    t_read = time.perf_counter() - t_read_start
    print(f"      [OK] Đã đọc {len(raw_text)} ký tự từ {input_path.name}")

    # 2. Clean & Chunk
    print("\n[2/5] Đang làm sạch và phân đoạn văn bản (chunking)...")
    t_clean_start = time.perf_counter()
    cleaned = clean_text(raw_text)
    if not cleaned:
        print("[ERROR] Văn bản sau khi làm sạch bị rỗng. Dừng pipeline.")
        sys.exit(1)

    chunks = chunk_text(cleaned, max_words=args.chunk_size)
    t_clean = time.perf_counter() - t_clean_start
    print(f"      [OK] Đã chia thành {len(chunks)} chunks tối ưu")

    # 3. Khởi tạo mô hình
    print("\n[3/5] Khởi tạo mô hình Flan-T5 (offline)...")
    t_load_start = time.perf_counter()
    pipeline = FlashcardPipeline()
    t_load = time.perf_counter() - t_load_start

    # 4. Batch Inference qua Flan-T5 & Parse Q&A
    print(f"\n[4/5] Chạy Batch Inference qua Flan-T5 (batch_size={args.batch_size})...")
    t_infer_start = time.perf_counter()
    cards = pipeline.generate_from_chunks(chunks, batch_size=args.batch_size)
    t_infer = time.perf_counter() - t_infer_start
    print(f"      [OK] Đã sinh và phân tích cú pháp {len(cards)} flashcards")

    # 5. Lưu file vào data/processed/
    print(f"\n[5/5] Xuất kết quả ra file chuẩn ({args.format.upper()})...")
    saved_path = pipeline.export_to_file(
        cards=cards,
        output_path=str(output_path),
        format=args.format,
    )
    print(f"      [OK] File đã được lưu tại: {saved_path}")

    t_total = time.perf_counter() - t_start_total

    # In bảng tóm tắt thời gian và số lượng thẻ sinh ra
    sample_preview = cards[: min(args.preview, len(cards))]
    _print_summary(
        input_file=input_path,
        output_file=Path(saved_path),
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
