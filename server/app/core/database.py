import importlib
import sqlite3
from pathlib import Path
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine

db = SQLAlchemy()


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Bật ràng buộc khóa ngoại trên SQLite cho mỗi kết nối DB."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.close()


def init_db(flask_app):
    """
    Khởi tạo cơ sở dữ liệu:
    1. Import đầy đủ 13 models vào metadata.
    2. Đọc và thực thi file DDL schema.sql.
    3. Đồng bộ db.create_all() trong application context.
    """
    # Import toàn bộ models để đăng ký vào SQLAlchemy metadata mà không shadow biến flask_app
    importlib.import_module("app.models")

    schema_candidates = [
        Path(flask_app.root_path).parent / "schema.sql",
        Path(flask_app.root_path) / "schema.sql",
        Path.cwd() / "server" / "schema.sql",
        Path.cwd() / "schema.sql",
    ]
    schema_file = next((p for p in schema_candidates if p.exists()), None)

    with flask_app.app_context():
        if schema_file and schema_file.exists():
            with open(schema_file, "r", encoding="utf-8") as f:
                ddl_sql = f.read()

            raw_conn = db.engine.raw_connection()
            try:
                cursor = raw_conn.cursor()
                cursor.executescript(ddl_sql)
                raw_conn.commit()
                cursor.close()
            finally:
                raw_conn.close()

        db.create_all()
