from typing import List, Optional
from sqlmodel import Session, col, func, select
from server.crud.base import CRUDBase
from server.models.ocr_review import OCRReview, OCRReviewCreate, OCRReviewUpdate


class CRUDOCRReview(CRUDBase[OCRReview, OCRReviewCreate, OCRReviewUpdate]):
    """OCR human review repository operations."""

    def get_by_record_id(self, session: Session, record_id: int) -> Optional[OCRReview]:
        """Fetch unique review entry linked to a specific OCR record."""
        statement = select(OCRReview).where(OCRReview.record_id == record_id)
        return session.exec(statement).first()

    def get_multi_filtered(
        self,
        session: Session,
        skip: int = 0,
        limit: int = 100,
        admin_id: Optional[int] = None,
        record_id: Optional[int] = None
    ) -> List[OCRReview]:
        """Retrieve paginated reviews ordered by review timestamp descending."""
        statement = select(OCRReview).order_by(col(OCRReview.reviewed_at).desc())
        if admin_id is not None:
            statement = statement.where(OCRReview.admin_id == admin_id)
        if record_id is not None:
            statement = statement.where(OCRReview.record_id == record_id)
        statement = statement.offset(skip).limit(limit)
        return list(session.exec(statement).all())

    def count_filtered(
        self,
        session: Session,
        admin_id: Optional[int] = None
    ) -> int:
        """Calculate total number of review entries, optionally filtered by reviewer ID."""
        statement = select(func.count()).select_from(OCRReview)
        if admin_id is not None:
            statement = statement.where(OCRReview.admin_id == admin_id)
        result = session.exec(statement).one()
        return int(result)


crud_ocr_review = CRUDOCRReview(OCRReview)

