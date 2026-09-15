import asyncio
import os
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ensure project root is in sys.path and load environment configuration
PIPELINE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PIPELINE_DIR.parent
load_dotenv(PIPELINE_DIR / ".env")
load_dotenv()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from pipeline.detector import get_detector
    from pipeline.schemas import DetectionResult
    from pipeline.tts_engine import generate_audio
except ImportError:
    from detector import get_detector
    from schemas import DetectionResult
    from tts_engine import generate_audio

PIPELINE_HOST = os.getenv("PIPELINE_HOST", "0.0.0.0")
PIPELINE_PORT = int(os.getenv("PIPELINE_PORT", 3100))

STATIC_DIR = PROJECT_ROOT / "server" / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"
AUDIO_DIR = STATIC_DIR / "audio"

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(AUDIO_DIR, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Pre-warms YOLO model in background executor on startup."""
    print(f"\n[+] Pipeline AI Service dang chay tai: http://localhost:{PIPELINE_PORT}")
    print(f"    📖 Swagger UI: http://localhost:{PIPELINE_PORT}/docs\n", flush=True)

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, get_detector)
    yield


app = FastAPI(
    title="Smart Object Detector - AI Pipeline Service",
    description="Dedicated AI Inference (YOLO11) and Audio Synthesis (Edge-TTS) Microservice",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/static/audio", StaticFiles(directory=str(AUDIO_DIR)), name="audio")


@app.get("/health", tags=["System"])
def health_check() -> dict:
    return {
        "status": "healthy",
        "service": "yolo_ai_pipeline",
        "port": PIPELINE_PORT
    }


@app.post("/api/v1/predict", response_model=DetectionResult, tags=["Inference"])
async def predict_endpoint(
    image: UploadFile = File(..., description="Target image file (JPEG, PNG, WEBP)")
) -> DetectionResult:
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
    if image.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {image.content_type}."
        )

    ext = Path(image.filename).suffix if image.filename else ".jpg"
    unique_id = uuid.uuid4().hex[:12]
    raw_image_path = UPLOADS_DIR / f"raw_{unique_id}{ext}"

    try:
        content = await image.read()
        with open(raw_image_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to buffer upload: {str(e)}"
        )

    loop = asyncio.get_running_loop()
    detector = get_detector()
    try:
        detection_result, _ = await loop.run_in_executor(
            None,
            detector.detect_objects,
            str(raw_image_path),
            str(UPLOADS_DIR),
            "/static/uploads"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline inference error: {str(e)}"
        )

    # Synthesize audio commentary
    audio_filename = f"speech_{unique_id}.mp3"
    audio_path = AUDIO_DIR / audio_filename
    try:
        await generate_audio(detection_result.summary, str(audio_path))
        detection_result.audio_url = f"/static/audio/{audio_filename}"
    except Exception:
        detection_result.audio_url = None

    return detection_result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host=PIPELINE_HOST, port=PIPELINE_PORT, reload=True)

