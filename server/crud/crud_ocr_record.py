from typing import List, Optional
from sqlmodel import Session, col, func, select
from server.crud.base import CRUDBase
from server.models.ocr_record import OCRRecord, OCRRecordCreate, OCRRecordUpdate


class CRUDOCRRecord(CRUDBase[OCRRecord, OCRRecordCreate, OCRRecordUpdate]):
    """OCR detection records repository operations."""

    def get_multi_filtered(
        self,
        session: Session,
        skip: int = 0,
        limit: int = 100,
        user_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[OCRRecord]:
        """Retrieve paginated detection records ordered chronologically descending."""
        statement = select(OCRRecord).order_by(col(OCRRecord.created_at).desc())
        if user_id is not None:
            statement = statement.where(OCRRecord.user_id == user_id)
        if status:
            statement = statement.where(OCRRecord.status == status)
        statement = statement.offset(skip).limit(limit)
        return list(session.exec(statement).all())

    def count_filtered(
        self,
        session: Session,
        user_id: Optional[int] = None,
        status: Optional[str] = None
    ) -> int:
        """Calculate total number of records matching filter conditions."""
        statement = select(func.count()).select_from(OCRRecord)
        if user_id is not None:
            statement = statement.where(OCRRecord.user_id == user_id)
        if status:
            statement = statement.where(OCRRecord.status == status)
        result = session.exec(statement).one()
        return int(result)


crud_ocr_record = CRUDOCRRecord(OCRRecord)

