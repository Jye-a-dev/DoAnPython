"""
deck_importer.py — Service phân tích cú pháp và nhập bộ thẻ từ CSV, Excel (.xlsx), và Tab-delimited.
Hỗ trợ nhận diện tiêu đề linh hoạt: Front/Question, Back/Answer, Personal Notes/Hint.
"""

from __future__ import annotations

import csv
import io
import re
import xml.etree.ElementTree as ET
import zipfile
from typing import Any, Dict, List, Tuple


def _normalize_header(header: str) -> str:
    """Chuẩn hóa chuỗi tiêu đề để so khớp không phân biệt hoa thường và ký tự đặc biệt."""
    return re.sub(r"[_\s\-\./\\]+", "", header.replace("\ufeff", "").lower().strip())


FRONT_VARIANTS = {
    "question",
    "front",
    "cauhoi",
    "câu hỏi",
    "q",
    "term",
    "từ",
    "tu",
    "mặttrước",
    "mattruoc",
    "mat truoc",
    "prompt",
    "vocabulary",
}
BACK_VARIANTS = {
    "answer",
    "back",
    "dapan",
    "đáp án",
    "a",
    "definition",
    "nghĩa",
    "nghia",
    "mặtsau",
    "matsau",
    "mat sau",
    "response",
    "meaning",
}
NOTE_VARIANTS = {
    "personalnotes",
    "personalnote",
    "notes",
    "note",
    "ghichu",
    "ghi chú",
    "hint",
    "mẹonhớ",
    "meonho",
    "annotation",
    "mnemonic",
}
EXPLANATION_VARIANTS = {
    "explanation",
    "giaithich",
    "giải thích",
    "desc",
    "description",
    "details",
}


def _match_column_indices(headers: List[str]) -> Tuple[int, int, int, int]:
    """Tìm chỉ số cột cho (front, back, notes, explanation). Mặc định là (0, 1, 2, -1) nếu không rõ."""
    q_idx, a_idx, n_idx, e_idx = -1, -1, -1, -1
    for idx, h in enumerate(headers):
        norm = _normalize_header(h)
        if q_idx == -1 and norm in FRONT_VARIANTS:
            q_idx = idx
        elif a_idx == -1 and norm in BACK_VARIANTS:
            a_idx = idx
        elif n_idx == -1 and norm in NOTE_VARIANTS:
            n_idx = idx
        elif e_idx == -1 and norm in EXPLANATION_VARIANTS:
            e_idx = idx

    if q_idx == -1 and len(headers) >= 1:
        q_idx = 0
    if a_idx == -1 and len(headers) >= 2:
        a_idx = 1
    if n_idx == -1 and len(headers) >= 3:
        n_idx = 2

    return q_idx, a_idx, n_idx, e_idx


def _rows_to_cards(all_rows: List[List[str]]) -> List[Dict[str, Any]]:
    """Chuyển đổi ma trận hàng/cột thành danh sách flashcards chuẩn."""
    cards: List[Dict[str, Any]] = []
    if not all_rows:
        return cards

    first_row = all_rows[0]
    norm_first = [_normalize_header(c) for c in first_row]
    has_header = any(n in FRONT_VARIANTS or n in BACK_VARIANTS for n in norm_first)

    if has_header:
        q_idx, a_idx, n_idx, e_idx = _match_column_indices(first_row)
        data_rows = all_rows[1:]
    else:
        q_idx = 0
        a_idx = 1 if len(first_row) > 1 else -1
        n_idx = 2 if len(first_row) > 2 else -1
        e_idx = 3 if len(first_row) > 3 else -1
        data_rows = all_rows

    for row in data_rows:
        if 0 <= q_idx < len(row) and 0 <= a_idx < len(row):
            q_val = str(row[q_idx]).strip()
            a_val = str(row[a_idx]).strip()
            if not q_val or not a_val:
                continue
            n_val = (
                str(row[n_idx]).strip()
                if 0 <= n_idx < len(row) and str(row[n_idx]).strip()
                else None
            )
            e_val = (
                str(row[e_idx]).strip()
                if 0 <= e_idx < len(row) and str(row[e_idx]).strip()
                else None
            )
            cards.append(
                {
                    "question": q_val,
                    "answer": a_val,
                    "personal_notes": n_val,
                    "explanation": e_val,
                    "difficulty": "medium",
                }
            )
    return cards


def parse_delimited_text(text: str) -> List[Dict[str, Any]]:
    """Phân tích văn bản CSV hoặc Tab-delimited (Anki/Quizlet copy-paste). Bỏ qua header comment (#)."""
    raw_lines = [line.strip() for line in text.splitlines()]
    non_empty = [l for l in raw_lines if l]
    # Lọc bỏ các dòng comment (ví dụ Anki export: #separator:tab, #deck:, #html:true)
    data_lines = [l for l in non_empty if not l.startswith("#")]
    if not data_lines:
        return []

    # Tự động nhận diện delimiter từ dòng dữ liệu đầu tiên (Tab hoặc Chấm phẩy hoặc Phẩy)
    first_data_line = data_lines[0]
    delimiter = (
        "\t"
        if "\t" in first_data_line
        else (";" if ";" in first_data_line and "," not in first_data_line else ",")
    )

    clean_text = "\n".join(data_lines)
    reader = csv.reader(io.StringIO(clean_text), delimiter=delimiter)
    all_rows = [row for row in reader if row and any(cell.strip() for cell in row)]
    return _rows_to_cards(all_rows)


def parse_xlsx_bytes(content: bytes) -> List[Dict[str, Any]]:
    """Phân tích file Excel .xlsx bằng openpyxl (ưu tiên) hoặc fallback XML ElementTree."""
    # 1. Thử dùng openpyxl trước (hỗ trợ hoàn hảo kiểu dữ liệu, chuỗi inline, UTF-8 và công thức)
    try:
        import openpyxl  # type: ignore

        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
        sheet = wb.active
        all_rows: List[List[str]] = []
        if sheet is not None:
            for row in sheet.iter_rows(values_only=True):
                cells = [str(c).strip() if c is not None else "" for c in row]
                if any(cells):
                    all_rows.append(cells)
            if all_rows:
                return _rows_to_cards(all_rows)
    except Exception:
        pass

    # 2. Fallback nhẹ dùng zipfile + ElementTree nếu môi trường không có openpyxl
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            shared_strings: List[str] = []
            if "xl/sharedStrings.xml" in zf.namelist():
                sst_root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
                ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                for si in sst_root.findall(".//s:si", ns) or sst_root.findall(".//si"):
                    t_nodes = si.findall(".//s:t", ns) or si.findall(".//t")
                    texts = [t.text or "" for t in t_nodes]
                    shared_strings.append("".join(texts))

            sheet_path = "xl/worksheets/sheet1.xml"
            if sheet_path not in zf.namelist():
                sheets = [
                    n for n in zf.namelist() if n.startswith("xl/worksheets/sheet")
                ]
                if not sheets:
                    return []
                sheet_path = sheets[0]

            sheet_root = ET.fromstring(zf.read(sheet_path))
            ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
            rows = sheet_root.findall(".//s:row", ns) or sheet_root.findall(".//row")

            all_rows = []
            for row in rows:
                c_nodes = row.findall("s:c", ns) or row.findall("c")
                row_cells: List[str] = []
                for c in c_nodes:
                    cell_type = c.get("t", "")
                    val_str = ""
                    v_node = c.find("s:v", ns)
                    if v_node is None:
                        v_node = c.find("v")

                    if v_node is not None and v_node.text:
                        val_raw = v_node.text.strip()
                        if cell_type == "s" and val_raw.isdigit():
                            s_idx = int(val_raw)
                            val_str = (
                                shared_strings[s_idx]
                                if s_idx < len(shared_strings)
                                else ""
                            )
                        else:
                            val_str = val_raw
                    elif cell_type == "inlineStr":
                        t_node = c.find(".//s:t", ns)
                        if t_node is None:
                            t_node = c.find(".//t")
                        if t_node is not None and t_node.text:
                            val_str = t_node.text.strip()
                    row_cells.append(val_str)
                if any(cell.strip() for cell in row_cells):
                    all_rows.append(row_cells)

            return _rows_to_cards(all_rows)
    except Exception:
        pass
    return []


def import_cards_from_file_data(
    filename: str, raw_bytes: bytes
) -> List[Dict[str, Any]]:
    """Phân phối việc phân tích dựa trên đuôi file (.csv, .xlsx, .txt, .tsv)."""
    fname_lower = filename.lower()
    if fname_lower.endswith(".xlsx"):
        return parse_xlsx_bytes(raw_bytes)

    # Đọc giải mã text thử tuần tự UTF-8-SIG (Excel CSV), UTF-8, UTF-16, CP1258, Latin-1
    for encoding in ("utf-8-sig", "utf-8", "utf-16", "cp1258", "latin-1"):
        try:
            text = raw_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw_bytes.decode("utf-8", errors="replace")

    return parse_delimited_text(text)
