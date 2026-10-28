"""
migrate_tts_columns.py — Thêm cột tts_text và tts_lang vào bảng cards (SQLite ALTER TABLE).
Chạy 1 lần cho DB hiện có: python scripts/migrate_tts_columns.py
"""

import glob
import os
import sqlite3
import sys


def migrate(db_path: str) -> None:
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cols = [row[1] for row in cur.execute("PRAGMA table_info(cards)").fetchall()]
    changed = False
    if "tts_text" not in cols:
        cur.execute("ALTER TABLE cards ADD COLUMN tts_text TEXT")
        print(f"  [OK] Đã thêm cột tts_text vào {db_path}")
        changed = True
    else:
        print(f"  [SKIP] tts_text đã tồn tại trong {db_path}")
    if "tts_lang" not in cols:
        cur.execute("ALTER TABLE cards ADD COLUMN tts_lang VARCHAR(10) DEFAULT 'en-US'")
        print(f"  [OK] Đã thêm cột tts_lang vào {db_path}")
        changed = True
    else:
        print(f"  [SKIP] tts_lang đã tồn tại trong {db_path}")
    if changed:
        con.commit()
    con.close()


if __name__ == "__main__":
    search_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    patterns = [
        os.path.join(search_root, "*.db"),
        os.path.join(search_root, "*.sqlite"),
        os.path.join(search_root, "*.sqlite3"),
        os.path.join(search_root, "instance", "*.db"),
        os.path.join(search_root, "instance", "*.sqlite"),
        os.path.join(search_root, "instance", "*.sqlite3"),
    ]
    db_files = []
    for pattern in patterns:
        db_files.extend(glob.glob(pattern))
    db_files = list(set(db_files))

    if not db_files:
        print("Không tìm thấy file database SQLite nào.")
        sys.exit(0)

    print(f"Tìm thấy {len(db_files)} database(s):")
    for db_path in db_files:
        print(f"\n>>> {db_path}")
        try:
            migrate(db_path)
        except Exception as exc:
            print(f"  [ERROR] {exc}")

    print("\nMigration hoàn tất.")
