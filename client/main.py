import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure client directory is prioritized in sys.path for component imports
_CLIENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CLIENT_DIR.parent

for _p in [str(_CLIENT_DIR), str(_PROJECT_ROOT)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

load_dotenv(_CLIENT_DIR / ".env")

from nicegui import ui
from components.navbar import render_navbar
from pages.home import render_home_page

port = int(os.getenv("PORT", 5000))
host = os.getenv("HOST", "0.0.0.0")

@ui.page("/")
def index():
    ui.query("body").classes("bg-slate-50 min-h-screen text-slate-800")
    render_navbar()
    render_home_page()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        title="EduFlash AI Client",
        host=host,
        port=port,
        reload=True,
        show=False,
        uvicorn_logging_level="info",
        uvicorn_reload_dirs=str(_CLIENT_DIR),
    )
