import os
from pathlib import Path
from dotenv import load_dotenv

_SERVER_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(_SERVER_DIR / ".env")

_INSTANCE_DIR = _SERVER_DIR / "instance"
_INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
_DEFAULT_DB = f"sqlite:///{(_INSTANCE_DIR / 'database.db').as_posix()}"

_raw_db_url = os.getenv("DATABASE_URL")
if not _raw_db_url or _raw_db_url == "sqlite:///instance/database.db":
    _resolved_db_url = _DEFAULT_DB
elif _raw_db_url.startswith("sqlite:///") and not os.path.isabs(
    _raw_db_url.replace("sqlite:///", "")
):
    _rel_p = _raw_db_url.replace("sqlite:///", "")
    _resolved_db_url = f"sqlite:///{(_SERVER_DIR / _rel_p).as_posix()}"
else:
    _resolved_db_url = _raw_db_url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-3000")
    SQLALCHEMY_DATABASE_URI = _resolved_db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AI_PIPELINE_URL = os.getenv("AI_PIPELINE_URL", "http://127.0.0.1:8000/api")
    CLIENT_ORIGIN = os.getenv("CLIENT_ORIGIN", "http://127.0.0.1:5000")
