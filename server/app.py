import asyncio
import os
from pathlib import Path
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from dotenv import load_dotenv

# Ensure project root is in sys.path and load environment configuration
SERVER_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SERVER_DIR.parent
load_dotenv(SERVER_DIR / ".env")
load_dotenv()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pipeline.detector import get_detector
from server.database import init_db
from server.routers import (
    detection_router,
    ocr_records_router,
    ocr_reviews_router,
    roles_router,
    users_router,
)

SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(os.getenv("SERVER_PORT", 3000))
PIPELINE_URL = os.getenv("PIPELINE_URL", "http://localhost:3100")

STATIC_DIR = SERVER_DIR / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"
AUDIO_DIR = STATIC_DIR / "audio"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager: sets up storage directories, initializes schema & seeds, pre-warms YOLO."""
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    os.makedirs(AUDIO_DIR, exist_ok=True)

    # Initialize SQLite schema, indexes, and sync sqlite_sequence
    init_db()

    print(f"\n[+] Server API Gateway dang chay tai: http://localhost:{SERVER_PORT}")
    print(f"    📖 Swagger UI: http://localhost:{SERVER_PORT}/docs")
    print(f"    🎯 Ket noi Pipeline: {PIPELINE_URL}\n", flush=True)

    # Pre-warm local fallback detector in background thread
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, get_detector)
    yield


tags_metadata = [
    {
        "name": "Roles",
        "description": "Quản lý vai trò người dùng (Admin, User), hỗ trợ đếm số lượng và CRUD đầy đủ.",
    },
    {
        "name": "Users",
        "description": "Quản lý tài khoản người dùng, phân quyền theo vai trò, hỗ trợ lọc và đếm số lượng.",
    },
    {
        "name": "OCR Records",
        "description": "Lưu trữ và quản lý bản ghi nhận diện OCR, hình ảnh, văn bản gốc, JSON bounding box và âm thanh.",
    },
    {
        "name": "OCR Reviews",
        "description": "Quản lý thẩm định và hiệu đính OCR của Admin, chấm điểm độ chính xác và audio chuẩn hóa.",
    },
    {
        "name": "Pipeline & Gateway",
        "description": "API Gateway điều phối suy luận YOLO qua microservice (Port 3100) và tổng hợp giọng nói.",
    },
    {
        "name": "System",
        "description": "Kiểm tra trạng thái vận hành và liveness của hệ thống backend.",
    },
]

app = FastAPI(
    title="Smart Object Detector & OCR Review API Gateway",
    description=(
        "Backend Gateway API cung cấp đầy đủ các module CRUD + Count cho Roles, Users, OCR Records, "
        "và OCR Reviews dựa trên database schema, đồng thời kết nối AI Pipeline microservice."
    ),
    version="2.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

# Cross-Origin Resource Sharing (CORS) for Reflex client communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static asset endpoints
app.mount("/static/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/static/audio", StaticFiles(directory=str(AUDIO_DIR)), name="audio")

# Mount modular CRUD & Count API Routers
app.include_router(roles_router)
app.include_router(users_router)
app.include_router(ocr_records_router)
app.include_router(ocr_reviews_router)
app.include_router(detection_router)


@app.get("/health", tags=["System"], summary="Health check endpoint")
def health_check() -> dict:
    """Service liveness and health check endpoint."""
    return {
        "status": "healthy",
        "service": "smart_object_detector_gateway",
        "port": SERVER_PORT,
        "pipeline_target": PIPELINE_URL,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.app:app", host=SERVER_HOST, port=SERVER_PORT, reload=True)
