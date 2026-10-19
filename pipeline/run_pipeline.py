"""
run_pipeline.py — CLI entrypoint for the Flan-T5 flashcard pipeline.

Usage:
    python run_pipeline.py [FILE] [--max-words N] [--preview N]

Defaults to pipeline/data/raw/sample.txt when FILE is omitted.
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s | %(name)s | %(message)s",
)

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------
_PIPELINE_DIR = Path(__file__).resolve().parent
_DEFAULT_SAMPLE = _PIPELINE_DIR / "data" / "raw" / "sample.txt"

if str(_PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(_PIPELINE_DIR))

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)
console = Console()


@app.command()
def main(
    file: Path = typer.Argument(
        default=None,
        help="Path to a .txt or .pdf file. Defaults to data/raw/sample.txt.",
        show_default=True,
    ),
    max_words: int = typer.Option(
        150,
        "--max-words",
        "-w",
        help="Maximum words per text chunk fed to the model.",
        min=50,
        max=400,
    ),
    preview: int = typer.Option(
        3,
        "--preview",
        "-p",
        help="Number of sample flashcards to display in the summary table.",
        min=1,
        max=20,
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Print the full result as a JSON array.",
    ),
) -> None:
    """Generate flashcards from a document using an offline Flan-T5 model."""

    # Resolve input file
    input_file: Path = file if file is not None else _DEFAULT_SAMPLE
    if not input_file.exists():
        console.print(f"[bold red][ERROR][/] File not found: {input_file}")
        raise typer.Exit(code=1)

    console.rule("[bold cyan]Flashcard Pipeline[/]")
    console.print(f"[dim]Input file :[/] {input_file}")
    console.print(f"[dim]Max words/chunk:[/] {max_words}")

    # ------------------------------------------------------------------
    # Load model
    # ------------------------------------------------------------------
    console.print("\n[bold yellow][1/3] Loading model…[/]")
    try:
        from src.processors.card_generator import FlashcardPipeline
    except ImportError as exc:
        console.print(f"[bold red][ERROR][/] Cannot import FlashcardPipeline: {exc}")
        raise typer.Exit(code=1)

    t_load_start = time.perf_counter()
    try:
        pipeline = FlashcardPipeline()
    except Exception as exc:
        console.print(f"[bold red][ERROR][/] Model load failed: {exc}")
        console.print(
            "    Ensure weights exist at [bold]pipeline/models_weights/flan-t5-base/[/]"
        )
        raise typer.Exit(code=1)
    t_load_end = time.perf_counter()
    console.print(f"    Model loaded in [bold]{t_load_end - t_load_start:.2f}s[/]")

    # ------------------------------------------------------------------
    # Generate flashcards
    # ------------------------------------------------------------------
    console.print("\n[bold yellow][2/3] Generating flashcards…[/]")
    t_infer_start = time.perf_counter()
    try:
        cards = pipeline.generate_from_document(
            str(input_file), max_words_per_chunk=max_words
        )
    except Exception as exc:
        console.print(f"[bold red][ERROR][/] Generation failed: {exc}")
        raise typer.Exit(code=1)
    t_infer_end = time.perf_counter()

    inference_time = t_infer_end - t_infer_start

    # ------------------------------------------------------------------
    # Report metrics
    # ------------------------------------------------------------------
    console.print("\n[bold yellow][3/3] Results[/]")
    console.print(
        Panel(
            f"[bold green]Flashcards generated:[/] {len(cards)}\n"
            f"[bold green]Inference time:      [/] {inference_time:.2f}s",
            title="[bold]Pipeline Metrics[/]",
            expand=False,
        )
    )

    if not cards:
        console.print(
            "[yellow]⚠  No flashcards were parsed from the model output.[/]\n"
            "   Try a different chunk size (--max-words) or inspect the raw output."
        )
        raise typer.Exit(code=0)

    # ------------------------------------------------------------------
    # Preview table
    # ------------------------------------------------------------------
    sample_count = min(preview, len(cards))
    table = Table(
        title=f"Sample Flashcards (first {sample_count} of {len(cards)})",
        show_lines=True,
        highlight=True,
    )
    table.add_column("#", style="dim", width=4, no_wrap=True)
    table.add_column("Question", style="cyan", min_width=30)
    table.add_column("Answer", style="green", min_width=30)

    for i, card in enumerate(cards[:sample_count], start=1):
        table.add_row(str(i), card["question"], card["answer"])

    console.print(table)

    # ------------------------------------------------------------------
    # JSON output
    # ------------------------------------------------------------------
    if json_output:
        console.rule("[bold]Full JSON Output[/]")
        print(json.dumps(cards, ensure_ascii=False, indent=2))

    # Always print the first card as a JSON sample for quick verification
    console.rule("[dim]JSON sample (card #1)[/]")
    print(json.dumps(cards[0], ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app()
