import os
import sqlite3
from pathlib import Path
from typing import Generator
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlmodel import SQLModel, Session

# Đường dẫn thư mục dữ liệu và tệp SQLite
SERVER_DIR = Path(__file__).resolve().parent
DATA_DIR = SERVER_DIR / "data"
DB_PATH = DATA_DIR / "detections.db"
SCHEMA_PATH = DATA_DIR / "schema.sql"

DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)


# Kích hoạt bắt buộc page_size, foreign keys, WAL mode, busy_timeout và synchronous = NORMAL trên từng connection
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA page_size = 16384;")
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA busy_timeout = 5000;")
        cursor.execute("PRAGMA synchronous = NORMAL;")
        cursor.close()


def init_db():
    """Khởi tạo cơ sở dữ liệu SQLite từ schema.sql và đồng bộ metadata."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Khởi tạo bảng và nạp seed data từ schema.sql
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA page_size = 16384;")
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA busy_timeout = 5000;")
        cursor.execute("PRAGMA synchronous = NORMAL;")

        # Kiểm tra tính tương thích schema UUID v4 và BLOB của bảng
        cursor.execute("PRAGMA table_info(users);")
        user_cols = {row[1]: str(row[2]).upper() for row in cursor.fetchall()}
        cursor.execute("PRAGMA table_info(categories);")
        category_cols = {row[1]: str(row[2]).upper() for row in cursor.fetchall()}
        cursor.execute("PRAGMA table_info(ocr_records);")
        ocr_cols = {row[1]: str(row[2]).upper() for row in cursor.fetchall()}

        needs_rebuild = False
        if user_cols and "INT" in user_cols.get("id", ""):
            needs_rebuild = True
        if category_cols and "INT" in category_cols.get("id", ""):
            needs_rebuild = True
        if ocr_cols and "RAW_IMAGE_DATA" not in ocr_cols:
            needs_rebuild = True

        if needs_rebuild:
            cursor.execute("DROP TABLE IF EXISTS order_items;")
            cursor.execute("DROP TABLE IF EXISTS orders;")
            cursor.execute("DROP TABLE IF EXISTS cart_items;")
            cursor.execute("DROP TABLE IF EXISTS products;")
            cursor.execute("DROP TABLE IF EXISTS categories;")
            cursor.execute("DROP TABLE IF EXISTS ocr_reviews;")
            cursor.execute("DROP TABLE IF EXISTS ocr_records;")
            cursor.execute("DROP TABLE IF EXISTS users;")
            cursor.execute("DROP TABLE IF EXISTS roles;")
            conn.commit()

        if SCHEMA_PATH.exists():
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                conn.executescript(f.read())

        # Đảm bảo các composite indexes được khởi tạo đồng bộ
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ocr_records_user_status_id ON ocr_records (user_id, status, id DESC);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ocr_records_status_id ON ocr_records (status, id DESC);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ocr_records_user_status_created ON ocr_records (user_id, status, created_at DESC);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_ocr_reviews_admin_id ON ocr_reviews (admin_id, id DESC);")
        conn.commit()
        try:
            conn.execute("VACUUM;")
            conn.commit()
        except Exception:
            pass

    # Tạo các bảng SQLModel bổ sung (nếu có)
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager an toàn cho Database Session, tự động commit hoặc rollback."""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
