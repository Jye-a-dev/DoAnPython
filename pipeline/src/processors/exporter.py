"""
exporter.py — Export flashcard dataset to JSON or UTF-8 CSV formats.
"""

from __future__ import annotations

import csv
import json
import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def export_cards_to_file(
    cards: List[Dict[str, Any]],
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
