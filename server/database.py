import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, Optional
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlmodel import Field, SQLModel, Session, create_engine

# Absolute path resolution ensuring database files reside in <server>/data/detections.db
SERVER_DIR = Path(__file__).resolve().parent
DATA_DIR = SERVER_DIR / "data"
DB_FILE = DATA_DIR / "detections.db"
SCHEMA_FILE = DATA_DIR / "schema.sql"

# Guarantee data directory exists before engine attachment
os.makedirs(DATA_DIR, exist_ok=True)

SQLITE_URL = f"sqlite:///{DB_FILE.as_posix()}"

engine = create_engine(
    SQLITE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)


# SQLite PRAGMA hook: enforces foreign keys and enables Write-Ahead Logging for concurrent connections
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


class DetectionRecord(SQLModel, table=True):
    """Legacy detection record table model for backward compatibility with existing pipeline."""
    __tablename__ = "detection_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    image_url: str = Field(nullable=False)
    summary: str = Field(nullable=False)
    json_data: str = Field(nullable=False)
    audio_url: str = Field(nullable=False)


def init_db() -> None:
    """
    Initializes SQLite database:
    1. Executes data/schema.sql to create core tables, indexes, and seed default roles.
    2. Synchronizes sqlite_sequence for tables with pre-seeded primary keys.
    3. Creates SQLModel metadata for supplemental tables (e.g. detection_records).
    """
    os.makedirs(DATA_DIR, exist_ok=True)

    # Execute raw schema DDL and seeds if schema file exists
    if SCHEMA_FILE.exists():
        schema_sql = SCHEMA_FILE.read_text(encoding="utf-8")
        raw_conn = engine.raw_connection()
        try:
            cursor = raw_conn.cursor()
            cursor.executescript(schema_sql)
            # Sync sqlite_sequence to avoid UNIQUE constraint conflicts on auto-increment IDs after explicit seeds
            cursor.execute(
                "INSERT OR REPLACE INTO sqlite_sequence (name, seq) "
                "SELECT 'roles', COALESCE(MAX(id), 0) FROM roles;"
            )
            raw_conn.commit()
            cursor.close()
        finally:
            raw_conn.close()

    # Create remaining SQLModel tables if not already defined in DDL
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a thread-safe database session."""
    with Session(engine) as session:
        yield session
