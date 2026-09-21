import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel
from server.models.common import DateTimeCoerceModel


class OCRReviewBase(SQLModel):
    """Base schema defining common human-in-the-loop review attributes."""
    record_id: str = Field(unique=True, foreign_key="ocr_records.id", nullable=False, index=True)
    admin_id: str = Field(foreign_key="users.id", nullable=False)
    corrected_text: str = Field(nullable=False)
    accuracy_score: float = Field(ge=0.0, le=1.0, nullable=False)
    review_notes: Optional[str] = Field(default=None)


class OCRReview(OCRReviewBase, table=True):
    """Database table mapping for 'ocr_reviews' table defined in schema.sql with binary audio BLOB."""
    __tablename__ = "ocr_reviews"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    corrected_audio_data: bytes = Field(nullable=False)
    corrected_audio_mime: str = Field(default="audio/mpeg", max_length=30, nullable=False)
    reviewed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class OCRReviewCreate(OCRReviewBase):
    """Payload schema for submitting an admin review."""
    pass


class OCRReviewUpdate(SQLModel):
    """Payload schema for amending an existing review."""
    admin_id: Optional[str] = None
    corrected_text: Optional[str] = None
    accuracy_score: Optional[float] = None
    review_notes: Optional[str] = None


class OCRReviewRead(OCRReviewBase, DateTimeCoerceModel):
    """Response schema representing a persisted review record."""
    id: str
    record_id: str
    admin_id: str
    reviewed_at: datetime
    corrected_audio_url: Optional[str] = None
