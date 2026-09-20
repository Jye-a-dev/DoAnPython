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


# Kích hoạt bắt buộc foreign keys và WAL mode trên từng connection
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.close()


def init_db():
    """Khởi tạo cơ sở dữ liệu SQLite từ schema.sql và đồng bộ metadata."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Khởi tạo bảng và nạp seed data từ schema.sql
    if SCHEMA_PATH.exists():
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
            conn.commit()

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
