import logging
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SERVER_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

logger = logging.getLogger("gateway")

PIPELINE_SERVICE_URL = os.getenv("PIPELINE_SERVICE_URL", "http://127.0.0.1:3100")
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", 3000))
JWT_SECRET = os.getenv("JWT_SECRET", "smart-detector-secure-token-secret-2026")
JWT_ALGORITHM = "HS256"

STORAGE_DIR = Path(os.getenv("STORAGE_DIR", str(SERVER_DIR / "static"))).resolve()
STATIC_DIR = STORAGE_DIR
UPLOADS_DIR = STATIC_DIR / "uploads"
AUDIO_DIR = STATIC_DIR / "audio"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Shared thread pool for background tasks and non-blocking pipeline calls
executor = ThreadPoolExecutor(max_workers=8)


def cleanup_old_files_worker(retention_seconds: int = 86400):
    """Background worker to purge stale upload and audio assets."""
    while True:
        try:
            now = time.time()
            for folder in [UPLOADS_DIR, AUDIO_DIR]:
                for f in folder.glob("*"):
                    if f.is_file() and not f.name.startswith(".gitkeep"):
                        if now - f.stat().st_mtime > retention_seconds:
                            f.unlink(missing_ok=True)
        except Exception:
            pass
        time.sleep(3600)

