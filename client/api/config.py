import os
from pathlib import Path
from dotenv import load_dotenv

# Load môi trường từ .env client hoặc thư mục gốc
CLIENT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(CLIENT_DIR / ".env")
load_dotenv()

# Địa chỉ cơ sở cho API Gateway
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:3000/api/v1").rstrip("/")

# Địa chỉ Server gốc để resolve các file media tĩnh (ảnh, audio)
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:3000").rstrip("/")

# Thời gian chờ mặc định cho httpx request (giây)
DEFAULT_TIMEOUT = float(os.getenv("API_TIMEOUT", "30.0"))
