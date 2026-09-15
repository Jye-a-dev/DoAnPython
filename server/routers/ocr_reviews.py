from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session
from server.crud.crud_ocr_record import crud_ocr_record
from server.crud.crud_ocr_review import crud_ocr_review
from server.crud.crud_user import crud_user
from server.database import get_session
from server.models.common import CountResponse
from server.models.ocr_review import OCRReviewCreate, OCRReviewRead, OCRReviewUpdate

router = APIRouter(prefix="/api/v1/ocr-reviews", tags=["OCR Reviews"])


@router.get(
    "/count",
    response_model=CountResponse,
    summary="Get OCR reviews count",
    description="Calculates total count of completed reviews, optionally filtered by reviewer ID."
)
def count_ocr_reviews(
    admin_id: Optional[int] = Query(None, description="Filter count by reviewing administrator ID"),
    session: Session = Depends(get_session)
) -> CountResponse:
    total = crud_ocr_review.count_filtered(session=session, admin_id=admin_id)
    return CountResponse(count=total)


@router.post(
    "",
    response_model=OCRReviewRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create OCR review",
    description="Submits an administrative correction, updated audio URL, and accuracy score for an OCR record."
)
def create_ocr_review(
    review_in: OCRReviewCreate,
    session: Session = Depends(get_session)
) -> OCRReviewRead:
    # 1. Validate linked OCR record exists
    record = crud_ocr_record.get(session=session, id=review_in.record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Target OCR record with ID {review_in.record_id} does not exist."
        )

    # 2. Check record_id uniqueness (schema defines record_id as UNIQUE)
    existing_review = crud_ocr_review.get_by_record_id(session=session, record_id=review_in.record_id)
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Review for OCR record ID {review_in.record_id} already exists."
        )

    # 3. Validate reviewing admin exists
    admin = crud_user.get(session=session, id=review_in.admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Admin user with ID {review_in.admin_id} does not exist."
        )

    return crud_ocr_review.create(session=session, obj_in=review_in)


@router.get(
    "",
    response_model=List[OCRReviewRead],
    summary="List OCR reviews",
    description="Retrieves paginated review entries ordered chronologically descending."
)
def list_ocr_reviews(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Maximum items to return"),
    admin_id: Optional[int] = Query(None, description="Filter by reviewing admin ID"),
    record_id: Optional[int] = Query(None, description="Filter by target record ID"),
    session: Session = Depends(get_session)
) -> List[OCRReviewRead]:
    return crud_ocr_review.get_multi_filtered(
        session=session,
        skip=skip,
        limit=limit,
        admin_id=admin_id,
        record_id=record_id
    )


@router.get(
    "/{review_id}",
    response_model=OCRReviewRead,
    summary="Get OCR review by ID",
    description="Retrieves detail of a single review entry by primary key."
)
def get_ocr_review(
    review_id: int,
    session: Session = Depends(get_session)
) -> OCRReviewRead:
    review = crud_ocr_review.get(session=session, id=review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with ID {review_id} not found."
        )
    return review


@router.put(
    "/{review_id}",
    response_model=OCRReviewRead,
    summary="Update OCR review",
    description="Updates review details such as corrected text, audio URL, or accuracy score."
)
def update_ocr_review(
    review_id: int,
    review_in: OCRReviewUpdate,
    session: Session = Depends(get_session)
) -> OCRReviewRead:
    review = crud_ocr_review.get(session=session, id=review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with ID {review_id} not found."
        )

    if review_in.admin_id is not None and review_in.admin_id != review.admin_id:
        admin = crud_user.get(session=session, id=review_in.admin_id)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Admin user with ID {review_in.admin_id} does not exist."
            )

    return crud_ocr_review.update(session=session, db_obj=review, obj_in=review_in)


@router.delete(
    "/{review_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete OCR review",
    description="Removes a review entry by primary key."
)
def delete_ocr_review(
    review_id: int,
    session: Session = Depends(get_session)
) -> None:
    review = crud_ocr_review.get(session=session, id=review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Review with ID {review_id} not found."
        )
    crud_ocr_review.remove(session=session, id=review_id)

