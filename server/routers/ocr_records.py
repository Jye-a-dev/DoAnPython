from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session
from server.crud.crud_ocr_record import crud_ocr_record
from server.crud.crud_user import crud_user
from server.database import get_session
from server.models.common import CountResponse
from server.models.ocr_record import OCRRecordCreate, OCRRecordRead, OCRRecordUpdate

router = APIRouter(prefix="/api/v1/ocr-records", tags=["OCR Records"])


@router.get(
    "/count",
    response_model=CountResponse,
    summary="Get OCR records count",
    description="Calculates total number of OCR records, optionally filtered by user ID and processing status."
)
def count_ocr_records(
    user_id: Optional[int] = Query(None, description="Filter count by capturing user ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter count by status (pending, approved, rejected)"),
    session: Session = Depends(get_session)
) -> CountResponse:
    total = crud_ocr_record.count_filtered(
        session=session,
        user_id=user_id,
        status=status_filter
    )
    return CountResponse(count=total)


@router.post(
    "",
    response_model=OCRRecordRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create OCR record",
    description="Registers an immutable OCR detection record with raw text, metadata, and synthesized audio URL."
)
def create_ocr_record(
    record_in: OCRRecordCreate,
    session: Session = Depends(get_session)
) -> OCRRecordRead:
    # Verify capturing user exists
    user = crud_user.get(session=session, id=record_in.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with ID {record_in.user_id} does not exist."
        )
    return crud_ocr_record.create(session=session, obj_in=record_in)


@router.get(
    "",
    response_model=List[OCRRecordRead],
    summary="List OCR records",
    description="Retrieves paginated detection records ordered chronologically descending with optional filters."
)
def list_ocr_records(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Maximum items to return"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (e.g. pending, approved, rejected)"),
    session: Session = Depends(get_session)
) -> List[OCRRecordRead]:
    return crud_ocr_record.get_multi_filtered(
        session=session,
        skip=skip,
        limit=limit,
        user_id=user_id,
        status=status_filter
    )


@router.get(
    "/{record_id}",
    response_model=OCRRecordRead,
    summary="Get OCR record by ID",
    description="Retrieves single detection record details by primary key."
)
def get_ocr_record(
    record_id: int,
    session: Session = Depends(get_session)
) -> OCRRecordRead:
    record = crud_ocr_record.get(session=session, id=record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"OCR record with ID {record_id} not found."
        )
    return record


@router.put(
    "/{record_id}",
    response_model=OCRRecordRead,
    summary="Update OCR record",
    description="Updates status, image or audio pointers, or textual content of an existing record."
)
def update_ocr_record(
    record_id: int,
    record_in: OCRRecordUpdate,
    session: Session = Depends(get_session)
) -> OCRRecordRead:
    record = crud_ocr_record.get(session=session, id=record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"OCR record with ID {record_id} not found."
        )

    if record_in.user_id is not None and record_in.user_id != record.user_id:
        user = crud_user.get(session=session, id=record_in.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with ID {record_in.user_id} does not exist."
            )

    return crud_ocr_record.update(session=session, db_obj=record, obj_in=record_in)


@router.delete(
    "/{record_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete OCR record",
    description="Deletes an OCR record and cascades deletion to linked reviews."
)
def delete_ocr_record(
    record_id: int,
    session: Session = Depends(get_session)
) -> None:
    record = crud_ocr_record.get(session=session, id=record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"OCR record with ID {record_id} not found."
        )
    crud_ocr_record.remove(session=session, id=record_id)

