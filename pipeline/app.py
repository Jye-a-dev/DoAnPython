import asyncio
import os
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Optional
import psutil
import torch
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Ensure project root is in sys.path
PIPELINE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PIPELINE_DIR.parent
load_dotenv(PIPELINE_DIR / ".env")
load_dotenv()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))

try:
    from pipeline.detector import get_detector
    from pipeline.schemas import DetectionResult
    from pipeline.tts_engine import generate_audio
    from pipeline.vlm_engine import get_vlm_suggestion
except ImportError:
    from detector import get_detector
    from schemas import DetectionResult
    from tts_engine import generate_audio
    from vlm_engine import get_vlm_suggestion

PIPELINE_HOST = os.getenv("PIPELINE_HOST", "0.0.0.0")
PIPELINE_PORT = int(os.getenv("PIPELINE_PORT", 3100))

DEFAULT_STATIC_DIR = PROJECT_ROOT / "server" / "static"
STORAGE_DIR = Path(os.getenv("STORAGE_DIR", str(DEFAULT_STATIC_DIR))).resolve()
STATIC_DIR = STORAGE_DIR
UPLOADS_DIR = STATIC_DIR / "uploads"
AUDIO_DIR = STATIC_DIR / "audio"
ASSET_BASE_URL = os.getenv("ASSET_BASE_URL", "").rstrip("/")

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


class TTSSynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text string to synthesize to speech")


class TTSSynthesizeResponse(BaseModel):
    audio_url: str
    status: str = "success"


class VLMSuggestRequest(BaseModel):
    image_path: str = Field(..., description="Absolute path or relative path to image file")
    box: Optional[dict] = Field(default=None, description="Bounding box dict with xmin, ymin, xmax, ymax")
    raw_label: Optional[str] = Field(default="", description="COCO raw label in English")
    raw_label_vi: Optional[str] = Field(default="", description="COCO label in Vietnamese")


class VLMSuggestResponse(BaseModel):
    suggested_label: str
    confidence: float = 0.95
    explanation: str
    suggested_class_name: str


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
    description="Dedicated AI Inference (YOLO) and Audio Synthesis (3-tier Fallback TTS) Microservice",
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


@app.get("/internal/health", tags=["System"])
def internal_health() -> dict:
    """Returns VRAM, system RAM, and device (CUDA/CPU) usage telemetry."""
    vram_info = {"device": "cpu", "allocated_mb": 0.0, "reserved_mb": 0.0, "total_mb": 0.0}
    device = "cpu"

    if torch.cuda.is_available():
        device = "cuda"
        allocated = torch.cuda.memory_allocated() / (1024 ** 2)
        reserved = torch.cuda.memory_reserved() / (1024 ** 2)
        props = torch.cuda.get_device_properties(0)
        total = props.total_memory / (1024 ** 2)
        vram_info = {
            "device": "cuda",
            "name": props.name,
            "allocated_mb": round(allocated, 2),
            "reserved_mb": round(reserved, 2),
            "total_mb": round(total, 2)
        }

    vm = psutil.virtual_memory()
    ram_info = {
        "total_mb": round(vm.total / (1024 ** 2), 2),
        "available_mb": round(vm.available / (1024 ** 2), 2),
        "used_mb": round(vm.used / (1024 ** 2), 2),
        "percent": vm.percent
    }

    return {
        "status": "healthy",
        "service": "yolo_ai_pipeline",
        "port": PIPELINE_PORT,
        "device": device,
        "vram": vram_info,
        "ram": ram_info
    }


@app.post("/internal/v1/process", response_model=DetectionResult, tags=["Inference"])
@app.post("/api/v1/predict", response_model=DetectionResult, tags=["Inference"])
async def process_image_endpoint(
    image: Optional[UploadFile] = File(None, description="Target image file"),
    file: Optional[UploadFile] = File(None, description="Target image file (alias)")
) -> dict:
    """Sequential pipeline: YOLO Detection -> Vietnamese Summary -> 3-tier Audio Synthesis."""
    target_file = file or image
    if not target_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yêu cầu cung cấp file ảnh hợp lệ (key: 'file' hoặc 'image')."
        )

    ext = Path(target_file.filename).suffix if target_file.filename else ".jpg"
    if not ext:
        ext = ".jpg"
    unique_id = uuid.uuid4().hex[:12]
    raw_image_path = UPLOADS_DIR / f"raw_{unique_id}{ext}"

    try:
        content = await target_file.read()
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
    except (ValueError, TypeError, IOError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Pipeline failed to process image payload: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline inference error: {str(e)}"
        )

    # Synthesize audio commentary via 3-tier fallback engine
    audio_filename = f"speech_{unique_id}.mp3"
    audio_path = AUDIO_DIR / audio_filename
    rel_audio_url = f"/static/audio/{audio_filename}"
    try:
        await generate_audio(detection_result.summary, str(audio_path))
        detection_result.audio_url = f"{ASSET_BASE_URL}{rel_audio_url}" if ASSET_BASE_URL else rel_audio_url
    except Exception:
        detection_result.audio_url = None

    if ASSET_BASE_URL and detection_result.image_url.startswith("/"):
        detection_result.image_url = f"{ASSET_BASE_URL}{detection_result.image_url}"

    detection_result.annotated_image_url = detection_result.image_url
    return detection_result


@app.post("/internal/v1/tts/synthesize", response_model=TTSSynthesizeResponse, tags=["Audio"])
async def synthesize_tts_endpoint(payload: TTSSynthesizeRequest) -> dict:
    """Synthesizes isolated text into an MP3 file using the 3-tier TTS fallback chain."""
    unique_id = uuid.uuid4().hex[:12]
    audio_filename = f"review_speech_{unique_id}.mp3"
    audio_path = AUDIO_DIR / audio_filename
    rel_audio_url = f"/static/audio/{audio_filename}"
    audio_url = f"{ASSET_BASE_URL}{rel_audio_url}" if ASSET_BASE_URL else rel_audio_url

    try:
        await generate_audio(payload.text, str(audio_path))
        return {
            "audio_url": audio_url,
            "status": "success"
        }
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"TTS synthesis failed: {str(ex)}"
        )


@app.post("/internal/v1/vlm/suggest", response_model=VLMSuggestResponse, tags=["Inference"])
async def vlm_suggest_endpoint(payload: VLMSuggestRequest) -> dict:
    """Provides 2-tier context-aware label refinement (Gemini Vision -> Local Heuristic Fallback)."""
    # Resolve relative paths against static dirs if needed
    img_path = Path(payload.image_path)
    if not img_path.is_absolute() or not img_path.exists():
        candidates = [
            STATIC_DIR / payload.image_path.lstrip("/"),
            UPLOADS_DIR / payload.image_path.lstrip("/"),
            PROJECT_ROOT / payload.image_path.lstrip("/"),
            UPLOADS_DIR / Path(payload.image_path).name,
        ]
        for c in candidates:
            if c.exists() and c.is_file():
                img_path = c
                break

    suggestion = await get_vlm_suggestion(
        image_path=str(img_path),
        box=payload.box,
        raw_label=payload.raw_label or "",
        raw_label_vi=payload.raw_label_vi or ""
    )
    return suggestion


if __name__ == "__main__":
    import uvicorn
    # Target module dynamically to support execution from repository root or subfolder
    app_import = "pipeline.app:app" if Path.cwd() == PROJECT_ROOT else "app:app"
    uvicorn.run(app_import, host=PIPELINE_HOST, port=PIPELINE_PORT, reload=True, reload_dirs=[str(PIPELINE_DIR)])
