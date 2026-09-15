from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel
from server.models.common import DateTimeCoerceModel


class OCRReviewBase(SQLModel):
    """Base schema defining common human-in-the-loop review attributes."""
    record_id: int = Field(unique=True, foreign_key="ocr_records.id", nullable=False, description="Associated OCR record identifier")
    admin_id: int = Field(foreign_key="users.id", nullable=False, description="Admin/reviewer identifier")
    corrected_text: str = Field(nullable=False, description="Standard corrected text verified by admin")
    corrected_audio_url: str = Field(nullable=False, description="Static URI pointing to audio synthesized from corrected text")
    accuracy_score: float = Field(ge=0.0, le=1.0, nullable=False, description="Calculated or assigned accuracy score between 0.0 and 1.0")
    review_notes: Optional[str] = Field(default=None, description="Optional reviewer observations or feedback notes")


class OCRReview(OCRReviewBase, table=True):
    """Database table mapping for 'ocr_reviews' table defined in schema.sql."""
    __tablename__ = "ocr_reviews"

    id: Optional[int] = Field(default=None, primary_key=True)
    reviewed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class OCRReviewCreate(OCRReviewBase):
    """Payload schema for submitting an admin review."""
    pass


class OCRReviewUpdate(SQLModel):
    """Payload schema for amending an existing review."""
    admin_id: Optional[int] = None
    corrected_text: Optional[str] = None
    corrected_audio_url: Optional[str] = None
    accuracy_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    review_notes: Optional[str] = None


class OCRReviewRead(OCRReviewBase, DateTimeCoerceModel):
    """Response schema representing a persisted review record."""
    id: int
    reviewed_at: datetime

