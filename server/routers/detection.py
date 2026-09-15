import asyncio
import json
import os
from pathlib import Path
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
import httpx
from sqlmodel import Session, col, select

from pipeline.detector import get_detector
from pipeline.schemas import DetectionResult, HistoryItem, HistoryResponse
from pipeline.tts_engine import generate_audio
from server.database import DetectionRecord, get_session

router = APIRouter(tags=["Pipeline & Gateway"])

SERVER_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = SERVER_DIR / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"
AUDIO_DIR = STATIC_DIR / "audio"
PIPELINE_URL = os.getenv("PIPELINE_URL", "http://localhost:3100")


@router.post(
    "/api/v1/detect",
    response_model=DetectionResult,
    summary="Coordinate object detection & audio synthesis",
    description="Accepts multipart image upload, coordinates inference via microservice (Port 3100) with local fallback, generates audio, and records detection."
)
async def detect_object_endpoint(
    image: UploadFile = File(..., description="Target image file (JPEG, PNG, WEBP)"),
    session: Session = Depends(get_session)
) -> DetectionResult:
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
    if image.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {image.content_type}. Must be JPEG, PNG, or WEBP."
        )

    ext = Path(image.filename).suffix if image.filename else ".jpg"
    unique_id = uuid.uuid4().hex[:12]
    original_filename = f"raw_{unique_id}{ext}"
    raw_image_path = UPLOADS_DIR / original_filename

    try:
        file_bytes = await image.read()
        with open(raw_image_path, "wb") as buffer:
            buffer.write(file_bytes)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to buffer uploaded image: {str(e)}"
        )

    detection_result = None

    # Step 1: Attempt to delegate inference to dedicated Pipeline Microservice (Port 3100)
    if PIPELINE_URL:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{PIPELINE_URL}/api/v1/predict",
                    files={"image": (image.filename or "upload.jpg", file_bytes, image.content_type or "image/jpeg")}
                )
                if response.status_code == 200:
                    detection_result = DetectionResult(**response.json())
        except Exception:
            detection_result = None

    # Step 2: Resilient in-process fallback if Pipeline Service is unreachable
    if detection_result is None:
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
                detail=f"Inference execution error: {str(e)}"
            )

        if not detection_result.audio_url:
            audio_filename = f"speech_{unique_id}.mp3"
            audio_path = AUDIO_DIR / audio_filename
            try:
                await generate_audio(detection_result.summary, str(audio_path))
                detection_result.audio_url = f"/static/audio/{audio_filename}"
            except Exception:
                detection_result.audio_url = None

    # Step 3: Persist immutable legacy record into SQLite database
    try:
        record = DetectionRecord(
            image_url=detection_result.image_url,
            summary=detection_result.summary,
            json_data=detection_result.model_dump_json(),
            audio_url=detection_result.audio_url or ""
        )
        session.add(record)
        session.commit()
        session.refresh(record)
    except Exception as db_err:
        session.rollback()
        print(f"[DB Warning] Failed to persist detection record: {db_err}")

    return detection_result


@router.get(
    "/api/v1/history",
    response_model=HistoryResponse,
    summary="Get detection history",
    description="Retrieves recent object detection history records from SQLite."
)
def get_detection_history(
    limit: int = 10,
    session: Session = Depends(get_session)
) -> HistoryResponse:
    query = (
        select(DetectionRecord)
        .order_by(col(DetectionRecord.created_at).desc())
        .limit(limit)
    )
    records = session.exec(query).all()

    formatted_items = []
    for r in records:
        try:
            parsed_json = json.loads(r.json_data)
        except Exception:
            parsed_json = {"raw": r.json_data}

        formatted_items.append(
            HistoryItem(
                id=r.id or 0,
                created_at=r.created_at.isoformat(),
                image_url=r.image_url,
                summary=r.summary,
                json_data=parsed_json,
                audio_url=r.audio_url
            )
        )

    return HistoryResponse(total=len(formatted_items), records=formatted_items)

