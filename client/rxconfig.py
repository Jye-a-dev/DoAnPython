import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import reflex as rx

CLIENT_DIR = Path(__file__).resolve().parent
if str(CLIENT_DIR) not in sys.path:
    sys.path.insert(0, str(CLIENT_DIR))

load_dotenv(CLIENT_DIR / ".env")
load_dotenv()

CLIENT_PORT = int(os.getenv("CLIENT_PORT", 5000))
BACKEND_PORT = int(os.getenv("REFLEX_BACKEND_PORT", 8001))

config = rx.Config(
    app_name="app",
    app_module_import="app",
    frontend_port=CLIENT_PORT,
    backend_port=BACKEND_PORT,
    plugins=[
        rx.plugins.RadixThemesPlugin(
            theme=rx.theme(
                appearance="inherit",
                has_background=True,
                accent_color="indigo",
                radius="large",
            )
        ),
        rx.plugins.SitemapPlugin(),
    ],
)

