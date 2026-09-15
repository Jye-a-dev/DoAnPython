from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel
from server.models.common import DateTimeCoerceModel


class OCRRecordBase(SQLModel):
    """Base schema defining common OCR detection record attributes."""
    user_id: int = Field(foreign_key="users.id", nullable=False, index=True, description="Identifier of the user who captured the image")
    image_url: str = Field(nullable=False, description="Static URI or URL pointing to the captured frame image")
    raw_detected_text: str = Field(nullable=False, description="Raw text output extracted by OCR/detector")
    ocr_json_data: str = Field(nullable=False, description="JSON string containing structured bounding boxes and metadata")
    audio_url: str = Field(nullable=False, description="Static URI pointing to the synthesized audio read-out")
    status: str = Field(default="pending", max_length=20, nullable=False, description="Status of the record: pending, approved, or rejected")


class OCRRecord(OCRRecordBase, table=True):
    """Database table mapping for 'ocr_records' table defined in schema.sql."""
    __tablename__ = "ocr_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class OCRRecordCreate(OCRRecordBase):
    """Payload schema for registering a new OCR record."""
    pass


class OCRRecordUpdate(SQLModel):
    """Payload schema for updating OCR record information."""
    user_id: Optional[int] = None
    image_url: Optional[str] = None
    raw_detected_text: Optional[str] = None
    ocr_json_data: Optional[str] = None
    audio_url: Optional[str] = None
    status: Optional[str] = Field(default=None, max_length=20)


class OCRRecordRead(OCRRecordBase, DateTimeCoerceModel):
    """Response schema representing a persisted OCR detection record."""
    id: int
    created_at: datetime

