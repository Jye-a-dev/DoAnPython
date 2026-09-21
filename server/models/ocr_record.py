import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel
from server.models.common import DateTimeCoerceModel


class OCRRecordBase(SQLModel):
    """Base schema defining common OCR detection record attributes."""
    user_id: str = Field(foreign_key="users.id", nullable=False, index=True, description="Identifier of the user who captured the image")
    raw_detected_text: str = Field(nullable=False, description="Raw text output extracted by OCR/detector")
    ocr_json_data: str = Field(default="[]", nullable=False, description="JSON string containing structured bounding boxes and metadata")
    status: str = Field(default="pending", max_length=20, nullable=False, description="Status of the record: pending, approved, or rejected")


class OCRRecord(OCRRecordBase, table=True):
    """Database table mapping for 'ocr_records' table defined in schema.sql with binary BLOB media storage."""
    __tablename__ = "ocr_records"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Dữ liệu nhị phân BLOB và Content-Type MIME
    raw_image_data: bytes = Field(nullable=False, description="Raw input photo bytes")
    raw_image_mime: str = Field(default="image/jpeg", max_length=30, nullable=False)

    annotated_image_data: Optional[bytes] = Field(default=None, description="YOLO annotated image bytes")
    annotated_image_mime: Optional[str] = Field(default="image/jpeg", max_length=30)

    raw_detected_text: str = Field(nullable=False)
    ocr_json_data: str = Field(default="[]", nullable=False)

    audio_data: bytes = Field(nullable=False, description="Synthesized MP3 audio bytes")
    audio_mime: str = Field(default="audio/mpeg", max_length=30, nullable=False)

    status: str = Field(default="pending", max_length=20, nullable=False, index=True)


class OCRRecordCreate(OCRRecordBase):
    """Payload schema for registering a new OCR record."""
    pass


class OCRRecordUpdate(SQLModel):
    """Payload schema for updating OCR record information."""
    raw_detected_text: Optional[str] = None
    ocr_json_data: Optional[str] = None
    status: Optional[str] = None


class OCRRecordRead(OCRRecordBase, DateTimeCoerceModel):
    """Response schema representing a persisted OCR detection record."""
    id: str
    user_id: str
    created_at: datetime
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
