"""
deck_exporter.py — Dịch vụ kết xuất bộ thẻ (Export Deck) sang CSV, Anki TXT, JSON và PDF Printable A4.
Hỗ trợ định dạng PDF in ấn 2 mặt (Mặt trước Câu hỏi, Mặt sau Đáp án) dạng lưới A4 cắt rời.
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, List


def export_deck_csv(deck_title: str, cards: List[Dict[str, Any]]) -> str:
    """Kết xuất danh sách thẻ thành định dạng chuẩn CSV."""
    output = io.StringIO()
    writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(
        ["Question", "Answer", "Explanation", "Personal Notes", "Difficulty", "Tags"]
    )
    for c in cards:
        tags_str = (
            ",".join(c.get("tags", []))
            if isinstance(c.get("tags"), list)
            else str(c.get("tags") or "")
        )
        writer.writerow(
            [
                c.get("question", ""),
                c.get("answer", ""),
                c.get("explanation") or "",
                c.get("personal_notes") or "",
                c.get("difficulty") or "medium",
                tags_str,
            ]
        )
    return output.getvalue()


def export_deck_anki(deck_title: str, cards: List[Dict[str, Any]]) -> str:
    """Kết xuất định dạng tương thích Anki/AnkiDroid (Tab-delimited text)."""
    lines = [
        "#separator:tab",
        "#html:true",
        f"#deck:{deck_title}",
        "#columns:Front\tBack\tPersonalNotes\tExplanation\tTags\tEaseFactor\tIntervalDays",
    ]
    for c in cards:
        q = str(c.get("question", "")).replace("\t", " ").replace("\n", "<br>")
        a = str(c.get("answer", "")).replace("\t", " ").replace("\n", "<br>")
        n = str(c.get("personal_notes") or "").replace("\t", " ").replace("\n", "<br>")
        e = str(c.get("explanation") or "").replace("\t", " ").replace("\n", "<br>")
        tags = " ".join(c.get("tags", [])) if isinstance(c.get("tags"), list) else ""
        ef = str(c.get("ease_factor", 2.5))
        iv = str(c.get("interval_days", 1))
        lines.append(f"{q}\t{a}\t{n}\t{e}\t{tags}\t{ef}\t{iv}")
    return "\n".join(lines)


def export_deck_json(
    deck_data: Dict[str, Any], cards: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Kết xuất toàn bộ siêu dữ liệu bộ thẻ và SM-2 progress ra JSON."""
    return {
        "version": "2.0.0",
        "exported_at": "2026-10-29T20:00:00Z",
        "deck": deck_data,
        "cards_count": len(cards),
        "cards": cards,
    }


def _escape_pdf_text(text: str) -> str:
    """Thoát ký tự chuỗi theo chuẩn định dạng PDF."""
    clean = "".join(ch if 32 <= ord(ch) <= 126 else " " for ch in text)
    return clean.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _wrap_text_lines(text: str, max_chars: int = 34) -> List[str]:
    """Bẻ dòng văn bản để hiển thị vừa vặn trong ô thẻ A4."""
    words = text.split()
    if not words:
        return []
    lines: List[str] = []
    current_line: List[str] = []
    current_len = 0
    for w in words:
        if current_len + len(w) + 1 > max_chars:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [w]
            current_len = len(w)
        else:
            current_line.append(w)
            current_len += len(w) + 1
    if current_line:
        lines.append(" ".join(current_line))
    return lines[:6]


def export_deck_pdf_printable(deck_title: str, cards: List[Dict[str, Any]]) -> bytes:
    """
    Sinh tài liệu PDF chuẩn A4 (595x842pt) bố trí 8 thẻ/trang (2 cột x 4 hàng).
    Mặt trước (Trang lẻ) là Câu hỏi, Mặt sau (Trang chẵn) là Đáp án (đảo cột để in 2 mặt khớp nhau).
    Có đường nét đứt định vị cắt rời thẻ thủ công.
    """
    pw, ph = 595.0, 842.0
    cols, rows = 2, 4
    cards_per_page = cols * rows
    margin_x, margin_y = 35.0, 40.0
    card_w = (pw - 2 * margin_x) / cols
    card_h = (ph - 2 * margin_y) / rows

    page_streams: List[str] = []
    chunk_size = cards_per_page
    card_chunks = [
        cards[i : i + chunk_size] for i in range(0, len(cards), chunk_size)
    ] or [[]]

    for chunk in card_chunks:
        # --- TRANG LẺ: MẶT TRƯỚC (QUESTIONS) ---
        f_ops = ["q", "0.6 0.6 0.6 RG", "[3 3] 0 d", "0.75 w"]
        # Vẽ lưới nét đứt
        for r in range(rows + 1):
            y = ph - margin_y - r * card_h
            f_ops.append(f"{margin_x:.2f} {y:.2f} m {pw - margin_x:.2f} {y:.2f} l S")
        for c in range(cols + 1):
            x = margin_x + c * card_w
            f_ops.append(f"{x:.2f} {margin_y:.2f} m {x:.2f} {ph - margin_y:.2f} l S")
        f_ops.append("Q")

        # Nội dung Mặt trước
        for idx, card in enumerate(chunk):
            r = idx // cols
            c = idx % cols
            cx = margin_x + c * card_w
            cy = ph - margin_y - (r + 1) * card_h
            q_text = str(card.get("question", "")).strip()

            f_ops.extend(
                [
                    "BT",
                    "/F1 8 Tf",
                    "0.4 0.4 0.5 rg",
                    f"{cx + 10:.2f} {cy + card_h - 16:.2f} Td",
                    f"({_escape_pdf_text(deck_title[:30])} | Q#{idx + 1}) Tj",
                    "ET",
                ]
            )
            lines = _wrap_text_lines(q_text, max_chars=32)
            start_y = cy + card_h - 40
            for l_idx, line in enumerate(lines):
                f_ops.extend(
                    [
                        "BT",
                        "/F1 11 Tf",
                        "0.1 0.1 0.15 rg",
                        f"{cx + 12:.2f} {start_y - l_idx * 14:.2f} Td",
                        f"({_escape_pdf_text(line)}) Tj",
                        "ET",
                    ]
                )

        page_streams.append("\n".join(f_ops))

        # --- TRANG CHẴN: MẶT SAU (ANSWERS - ĐẢO CỘT 0 <-> 1 ĐỂ KHỚP 2 MẶT KHI IN DUPLEX) ---
        b_ops = ["q", "0.6 0.6 0.6 RG", "[3 3] 0 d", "0.75 w"]
        for r in range(rows + 1):
            y = ph - margin_y - r * card_h
            b_ops.append(f"{margin_x:.2f} {y:.2f} m {pw - margin_x:.2f} {y:.2f} l S")
        for c in range(cols + 1):
            x = margin_x + c * card_w
            b_ops.append(f"{x:.2f} {margin_y:.2f} m {x:.2f} {ph - margin_y:.2f} l S")
        b_ops.append("Q")

        for idx, card in enumerate(chunk):
            r = idx // cols
            c = 1 - (idx % cols)  # Đảo cột để in ấn 2 mặt khớp vị trí cắt
            cx = margin_x + c * card_w
            cy = ph - margin_y - (r + 1) * card_h
            a_text = str(card.get("answer", "")).strip()
            notes = str(card.get("personal_notes") or "").strip()

            b_ops.extend(
                [
                    "BT",
                    "/F1 8 Tf",
                    "0.3 0.3 0.7 rg",
                    f"{cx + 10:.2f} {cy + card_h - 16:.2f} Td",
                    f"(DAP AN - ANSWER | #{idx + 1}) Tj",
                    "ET",
                ]
            )
            lines = _wrap_text_lines(a_text, max_chars=32)
            start_y = cy + card_h - 40
            for l_idx, line in enumerate(lines):
                b_ops.extend(
                    [
                        "BT",
                        "/F1 11 Tf",
                        "0.15 0.15 0.2 rg",
                        f"{cx + 12:.2f} {start_y - l_idx * 14:.2f} Td",
                        f"({_escape_pdf_text(line)}) Tj",
                        "ET",
                    ]
                )
            if notes:
                note_line = _wrap_text_lines(f"Ghi chu: {notes}", max_chars=36)
                if note_line:
                    b_ops.extend(
                        [
                            "BT",
                            "/F1 8 Tf",
                            "0.5 0.4 0.1 rg",
                            f"{cx + 12:.2f} {cy + 14:.2f} Td",
                            f"({_escape_pdf_text(note_line[0])}) Tj",
                            "ET",
                        ]
                    )

        page_streams.append("\n".join(b_ops))

    # Đóng gói cấu trúc PDF File 1.4 nhị phân
    objects: List[bytes] = []
    objects.append(b"")  # placeholder cho 0

    # 1: Catalog
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    # 2: Pages (sẽ điền references các trang)
    total_pages = len(page_streams)
    page_obj_ids = [3 + i * 2 for i in range(total_pages)]
    kids_str = " ".join(f"{pid} 0 R" for pid in page_obj_ids)
    objects.append(
        f"<< /Type /Pages /Kids [{kids_str}] /Count {total_pages} >>".encode("ascii")
    )

    # Các Page và Content stream
    font_id = 3 + total_pages * 2
    for i, stm in enumerate(page_streams):
        pid = 3 + i * 2
        cid = pid + 1
        page_dict = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {pw} {ph}] "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> /Contents {cid} 0 R >>"
        ).encode("ascii")
        objects.append(page_dict)
        stm_bytes = stm.encode("latin-1", errors="replace")
        content_dict = (
            f"<< /Length {len(stm_bytes)} >>\nstream\n".encode("ascii")
            + stm_bytes
            + b"\nendstream"
        )
        objects.append(content_dict)

    # Font F1 (Helvetica)
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    # XRef & Trailer
    pdf_out = io.BytesIO()
    pdf_out.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for idx in range(1, len(objects)):
        offsets.append(pdf_out.tell())
        pdf_out.write(f"{idx} 0 obj\n".encode("ascii"))
        pdf_out.write(objects[idx])
        pdf_out.write(b"\nendobj\n")

    xref_pos = pdf_out.tell()
    pdf_out.write(f"xref\n0 {len(objects)}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets[1:]:
        pdf_out.write(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf_out.write(
        f"trailer\n<< /Size {len(objects)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode(
            "ascii"
        )
    )
    return pdf_out.getvalue()
