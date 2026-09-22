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

        if user_cols and "PASSWORD_HASH" not in user_cols and not needs_rebuild:
            cursor.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);")
            conn.commit()

        if SCHEMA_PATH.exists():
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                conn.executescript(f.read())

        # Đồng bộ mật khẩu mẫu cho các tài khoản seed
        admin_default_hash = "scrypt:32768:8:1$lQ17xvm4CDWZJ6Jw$056dc4a87c17561c0bfeb839f395fe22c5f807cadd9fcbdbb37b244f9f559b55525df4db9a65e631527698c3ad14b0f12ac34c18e2b86d5ccd2616515e34b103"
        customer_default_hash = "scrypt:32768:8:1$wAs2UGIyT9u1cMBM$f273f769b6057be5cd35bf3d38e8c6a73a5253a47bfc120fe64365303e26e9b2692fc989e08dff9ce1b5d5bb213f176ac01453668ef946851638666ccdb45f76"
        user_default_hash = "scrypt:32768:8:1$N9bCwNA6inWkM9f5$954ac9c2f5ecf8a799e8d57fb641c9a52d7e37a27252930ab27484e526b2fe2323de18100df89e3814dfc2b864ee09442c83617cd175e14cc00d50d425dc1fdb"

        cursor.execute("UPDATE users SET password_hash = ? WHERE email = 'admin@system.local' AND (password_hash IS NULL OR password_hash = '');", (admin_default_hash,))
        cursor.execute("UPDATE users SET password_hash = ? WHERE email = 'customer@shop.vn' AND (password_hash IS NULL OR password_hash = '');", (customer_default_hash,))
        cursor.execute("UPDATE users SET password_hash = ? WHERE email = 'user@system.local' AND (password_hash IS NULL OR password_hash = '');", (user_default_hash,))
        cursor.execute("""
            INSERT OR IGNORE INTO users (id, google_id, email, password_hash, full_name, role_id, is_active) VALUES
            ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', 'customer_default', 'customer@shop.vn', ?, 'Khách Hàng Mẫu', 2, 1),
            ('bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbc', 'user_default', 'user@system.local', ?, 'Người Dùng Test', 2, 1);
        """, (customer_default_hash, user_default_hash))
        conn.commit()

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
