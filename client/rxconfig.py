import os
from pathlib import Path
from dotenv import load_dotenv
import reflex as rx

# Resolve client directory and load local .env configuration
CLIENT_DIR = Path(__file__).resolve().parent
load_dotenv(CLIENT_DIR / ".env")
load_dotenv()

CLIENT_PORT = int(os.getenv("CLIENT_PORT", 5000))
BACKEND_PORT = int(os.getenv("REFLEX_BACKEND_PORT", 8001))

config = rx.Config(
    app_name="app",
    frontend_port=CLIENT_PORT,
    backend_port=BACKEND_PORT,
)
