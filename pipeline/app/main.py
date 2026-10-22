"""
main.py — FastAPI entrypoint for Flashcard AI Pipeline Microservice (Port 8000).
Exclusively serves AI inference tasks (Flan-T5 generation, Whisper speech-to-text).
Completely decoupled from database operations and business logic CRUD.
"""

from __future__ import annotations

import io
import logging
import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Path setup & Virtualenv resolution
# ---------------------------------------------------------------------------
_APP_DIR = Path(__file__).resolve().parent  # pipeline/app
_PIPELINE_DIR = _APP_DIR.parent  # pipeline/
_VENV_SITE_PACKAGES = _PIPELINE_DIR / ".venv" / "Lib" / "site-packages"

for _p in [str(_PIPELINE_DIR), str(_APP_DIR), str(_VENV_SITE_PACKAGES)]:
    if os.path.exists(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Load .env file from pipeline directory
load_dotenv(_PIPELINE_DIR / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("ai_pipeline")

# Configuration variables
FLAN_T5_MODEL_PATH = os.getenv(
    "FLAN_T5_MODEL_PATH",
    str(_PIPELINE_DIR / "models_weights" / "flan-t5-base"),
)
# Resolve relative paths relative to pipeline dir
if not Path(FLAN_T5_MODEL_PATH).is_absolute():
    FLAN_T5_MODEL_PATH = str((_PIPELINE_DIR / FLAN_T5_MODEL_PATH).resolve())

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
DEVICE = os.getenv("DEVICE", "cpu")

# ---------------------------------------------------------------------------
# Lazy-loaded Model Singletons
# ---------------------------------------------------------------------------
_card_pipeline = None
_audio_transcriber = None


def get_card_pipeline():
    global _card_pipeline
    if _card_pipeline is None:
        from src.processors.card_generator import FlashcardPipeline

        logger.info("Initializing Flan-T5 model from %s...", FLAN_T5_MODEL_PATH)
        _card_pipeline = FlashcardPipeline(model_path=FLAN_T5_MODEL_PATH)
    return _card_pipeline


def get_audio_transcriber():
    global _audio_transcriber
    if _audio_transcriber is None:
        from src.processors.audio_transcriber import AudioTranscriber

        logger.info(
            "Initializing Whisper model (size=%s, device=%s)...",
            WHISPER_MODEL_SIZE,
            DEVICE,
        )
        _audio_transcriber = AudioTranscriber(
            model_size=WHISPER_MODEL_SIZE,
            device=DEVICE,
        )
    return _audio_transcriber


# ---------------------------------------------------------------------------
# Lifespan Context Manager
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting AI Pipeline Microservice on %s:%s",
        os.getenv("HOST", "0.0.0.0"),
        os.getenv("PORT", "8000"),
    )
    logger.info("Verifying model path: %s", FLAN_T5_MODEL_PATH)
    yield
    logger.info("Shutting down AI Pipeline Microservice.")


# ---------------------------------------------------------------------------
# FastAPI Application Initialization
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Flashcard AI Pipeline Microservice",
    description="Microservice chuyên biệt phục vụ các tác vụ AI: Flan-T5 Q&A Flashcard Generation & Whisper Speech-to-Text.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
DEFAULT_MAX_WORDS_PER_CHUNK = 150


class GenerateRequest(BaseModel):
    text: str = Field(
        ..., min_length=1, description="Văn bản bài học cần sinh câu hỏi và đáp án"
    )
    max_cards: Optional[int] = Field(
        default=5,
        ge=1,
        le=100,
        description="Số lượng thẻ tối đa cần sinh",
    )
    max_words_per_chunk: Optional[int] = Field(
        default=DEFAULT_MAX_WORDS_PER_CHUNK,
        ge=50,
        le=500,
        description="Số từ tối đa trong mỗi phân đoạn văn bản cho model",
    )


class QAPair(BaseModel):
    question: str
    answer: str


class GenerateResponse(BaseModel):
    count: int
    cards: List[QAPair]
    inference_time_seconds: float


class TranscribeResponse(BaseModel):
    text: str
    language: str
    duration_seconds: float


class ModelStatus(BaseModel):
    status: str
    details: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    models: Dict[str, ModelStatus]


# ---------------------------------------------------------------------------
# AI Endpoints (pi. prefix)
# ---------------------------------------------------------------------------
@app.post(
    "/api/pi/generate",
    response_model=GenerateResponse,
    summary="Sinh thẻ Flashcard Q&A từ bài học",
    status_code=status.HTTP_200_OK,
)
@app.post(
    "/api/generate",
    response_model=GenerateResponse,
    include_in_schema=False,
)
async def pi_generate_flashcards(payload: GenerateRequest) -> Dict[str, Any]:
    """
    Tiếp nhận văn bản bài học -> Tiền xử lý, chia chunk -> Chạy mô hình offline Flan-T5 ->
    Trả về: {"count": N, "cards": [{"question": "...", "answer": "..."}], "inference_time_seconds": 1.25}.
    """
    cleaned_input = payload.text.strip()
    if not cleaned_input:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nội dung văn bản không được để trống.",
        )

    start_time = time.perf_counter()
    try:
        from src.cleaners.text_cleaner import clean_text, chunk_text

        cleaned = clean_text(cleaned_input)
        chunks = chunk_text(
            cleaned,
            max_words=payload.max_words_per_chunk or DEFAULT_MAX_WORDS_PER_CHUNK,
        )
        if not chunks:
            chunks = [cleaned[:500]] if cleaned else []

        pipeline = get_card_pipeline()
        cards: List[Dict[str, str]] = pipeline.generate_from_chunks(chunks)

        if payload.max_cards and payload.max_cards > 0:
            cards = cards[: payload.max_cards]

        inference_time = round(time.perf_counter() - start_time, 2)
        return {
            "count": len(cards),
            "cards": cards,
            "inference_time_seconds": inference_time,
        }
    except Exception as exc:
        logger.exception("Error during flashcard generation: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi tiến trình AI Flan-T5: {str(exc)}",
        )


@app.post(
    "/api/pi/transcribe",
    response_model=TranscribeResponse,
    summary="Bóc băng âm thanh sang văn bản (Speech-to-Text)",
    status_code=status.HTTP_200_OK,
)
@app.post(
    "/api/transcribe",
    response_model=TranscribeResponse,
    include_in_schema=False,
)
async def pi_transcribe_audio(
    file: UploadFile = File(..., description="File âm thanh (.mp3, .wav, .m4a)"),
    language: Optional[str] = Query(
        default="vi", description="Mã ngôn ngữ (mặc định: 'vi')"
    ),
) -> Dict[str, Any]:
    """
    Tiếp nhận file âm thanh qua multipart/form-data.
    Đọc trực tiếp binary từ RAM qua io.BytesIO, gọi mô hình Whisper offline,
    và trả về: {"text": "...", "language": "vi", "duration_seconds": 12.5}.
    """
    allowed_extensions = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac"}
    filename = file.filename or "audio.wav"
    file_ext = Path(filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Định dạng '{file_ext}' không được hỗ trợ. Chấp nhận: {', '.join(sorted(allowed_extensions))}",
        )

    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File âm thanh rỗng (0 bytes).",
            )

        audio_stream = io.BytesIO(file_bytes)
        transcriber = get_audio_transcriber()
        result = transcriber.transcribe(
            audio_data=audio_stream,
            filename=filename,
            language=language,
        )
        return {
            "text": result.get("text", ""),
            "language": result.get("language", language or "vi"),
            "duration_seconds": result.get("duration_seconds", 0.0),
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error during audio transcription: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi tiến trình Whisper STT: {str(exc)}",
        )


@app.get(
    "/api/pi/health",
    response_model=HealthResponse,
    summary="Kiểm tra trạng thái sẵn sàng của AI Microservice & các model",
    status_code=status.HTTP_200_OK,
)
@app.get(
    "/api/health",
    response_model=HealthResponse,
    include_in_schema=False,
)
async def pi_check_health() -> Dict[str, Any]:
    """
    Kiểm tra tình trạng hoạt động của service và nạp trọng số 2 model (Flan-T5 & Whisper).
    """
    # Flan-T5 check
    flan_status = "ready" if _card_pipeline is not None else "available_on_disk"
    if not Path(FLAN_T5_MODEL_PATH).exists():
        flan_status = "model_weights_missing"

    # Whisper check
    whisper_status = (
        "ready"
        if (_audio_transcriber is not None and _audio_transcriber.is_loaded())
        else "available"
    )

    return {
        "status": "healthy",
        "models": {
            "flan_t5": {
                "status": flan_status,
                "details": {
                    "model_path": FLAN_T5_MODEL_PATH,
                    "loaded_in_memory": _card_pipeline is not None,
                },
            },
            "whisper": {
                "status": whisper_status,
                "details": {
                    "model_size": WHISPER_MODEL_SIZE,
                    "device": DEVICE,
                    "loaded_in_memory": (
                        _audio_transcriber is not None
                        and _audio_transcriber.is_loaded()
                    ),
                },
            },
        },
    }



if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Starting AI Pipeline on http://{host}:{port}")
    app_target = "pipeline.app.main:app" if Path("pipeline").exists() else "app.main:app"
    uvicorn.run(app_target, host=host, port=port, reload=False)
