"""
migrate_notes_column.py — Thêm cột personal_notes vào bảng cards (SQLite ALTER TABLE).
Chạy 1 lần cho DB hiện có: python scripts/migrate_notes_column.py
"""

from __future__ import annotations

import glob
import os
import sqlite3


def migrate(db_path: str) -> None:
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    try:
        tables = [
            row[0]
            for row in cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]
        if "cards" not in tables:
            con.close()
            return
        cols = [row[1] for row in cur.execute("PRAGMA table_info(cards)").fetchall()]
        if "personal_notes" not in cols:
            cur.execute("ALTER TABLE cards ADD COLUMN personal_notes TEXT NULL")
            con.commit()
            print(f"  [OK] Added personal_notes column to {db_path}")
        else:
            print(f"  [SKIP] personal_notes already exists in {db_path}")
    finally:
        con.close()


if __name__ == "__main__":
    search_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    patterns = [
        os.path.join(search_root, "*.db"),
        os.path.join(search_root, "*.sqlite"),
        os.path.join(search_root, "*.sqlite3"),
        os.path.join(search_root, "instance", "*.db"),
        os.path.join(search_root, "app", "instance", "*.db"),
    ]
    db_files: list[str] = []
    for pattern in patterns:
        db_files.extend(glob.glob(pattern))
    for f in sorted(set(db_files)):
        migrate(f)
