import importlib
import os
from pathlib import Path
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa
from sqlalchemy import event, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool


class DynamicSQLAlchemy(SQLAlchemy):
    """
    Mở rộng SQLAlchemy để tự động nhận diện và tái tạo Engine khi
    app.config['SQLALCHEMY_DATABASE_URI'] thay đổi (ví dụ trong môi trường kiểm thử in-memory).
    """

    @property
    def engines(self):
        app = current_app._get_current_object()  # type: ignore[attr-defined]
        engines_dict = self._app_engines.get(app, {})
        current_uri = app.config.get("SQLALCHEMY_DATABASE_URI")
        default_engine = engines_dict.get(None)

        if current_uri is not None and (
            default_engine is None or str(default_engine.url) != current_uri
        ):
            if default_engine is not None:
                default_engine.dispose()

            opts = {}
            if current_uri == "sqlite:///:memory:":
                # Dùng StaticPool và tắt check_same_thread để toàn bộ test client dùng chung RAM DB
                opts["poolclass"] = StaticPool
                opts["connect_args"] = {"check_same_thread": False}

            new_engine = sa.create_engine(current_uri, **opts)

            @event.listens_for(new_engine, "connect")
            def set_fk_pragma(dbapi_conn, _):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON;")
                cursor.close()

            engines_dict[None] = new_engine

        return engines_dict


db = DynamicSQLAlchemy()


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Đảm bảo mọi kết nối SQLite luôn kích hoạt PRAGMA foreign_keys=ON."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()


def init_db(app):
    """
    Nạp và thực thi trực tiếp toàn bộ câu lệnh từ file server/schema.sql
    khi ứng dụng khởi chạy nếu database chưa tồn tại.
    """
    # Đăng ký toàn bộ 13 models vào SQLAlchemy metadata
    importlib.import_module("app.models")

    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    db_needs_init = False

    # Xác định đường dẫn SQLite file và kiểm tra sự tồn tại của database
    if db_uri.startswith("sqlite:///"):
        rel_path = db_uri.replace("sqlite:///", "")
        if rel_path == ":memory:":
            db_needs_init = True
        else:
            db_path = (
                Path(rel_path)
                if os.path.isabs(rel_path)
                else Path(app.instance_path) / rel_path
            )
            if not db_path.exists() or db_path.stat().st_size == 0:
                db_needs_init = True
                db_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        db_needs_init = True

    with app.app_context():
        if not db_needs_init:
            inspector = inspect(db.engine)
            if not inspector.has_table("users"):
                db_needs_init = True

        if db_needs_init:
            schema_candidates = [
                Path(app.root_path).parent / "schema.sql",
                Path(app.root_path) / "schema.sql",
                Path.cwd() / "server" / "schema.sql",
                Path.cwd() / "schema.sql",
            ]
            schema_file = next((p for p in schema_candidates if p.is_file()), None)

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
