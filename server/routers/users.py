from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session
from server.crud.crud_role import crud_role
from server.crud.crud_user import crud_user
from server.database import get_session
from server.models.common import CountResponse
from server.models.user import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get(
    "/count",
    response_model=CountResponse,
    summary="Get users count",
    description="Calculates total number of users matching optional filter criteria (role, active state, search)."
)
def count_users(
    role_id: Optional[int] = Query(None, description="Filter count by specific role ID"),
    is_active: Optional[bool] = Query(None, description="Filter count by active status"),
    search: Optional[str] = Query(None, description="Search keyword in email or name"),
    session: Session = Depends(get_session)
) -> CountResponse:
    total = crud_user.count_filtered(
        session=session,
        role_id=role_id,
        is_active=is_active,
        search=search
    )
    return CountResponse(count=total)


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Registers a new user record linked to a valid role ID."
)
def create_user(
    user_in: UserCreate,
    session: Session = Depends(get_session)
) -> UserRead:
    # Validate foreign key constraint on role_id
    role = crud_role.get(session=session, id=user_in.role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role with ID {user_in.role_id} does not exist."
        )

    # Validate email uniqueness
    existing_user = crud_user.get_by_email(session=session, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email '{user_in.email}' already exists."
        )

    # Validate google_id uniqueness if provided
    if user_in.google_id:
        existing_google = crud_user.get_by_google_id(session=session, google_id=user_in.google_id)
        if existing_google:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with google_id '{user_in.google_id}' already exists."
            )

    return crud_user.create(session=session, obj_in=user_in)


@router.get(
    "",
    response_model=List[UserRead],
    summary="List all users",
    description="Retrieves paginated user accounts with optional filtering and keyword search."
)
def list_users(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Maximum items to return"),
    role_id: Optional[int] = Query(None, description="Filter by role ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search term for name or email"),
    session: Session = Depends(get_session)
) -> List[UserRead]:
    return crud_user.get_multi_filtered(
        session=session,
        skip=skip,
        limit=limit,
        role_id=role_id,
        is_active=is_active,
        search=search
    )


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Get user by ID",
    description="Retrieves details for an individual user account by primary key."
)
def get_user(
    user_id: int,
    session: Session = Depends(get_session)
) -> UserRead:
    user = crud_user.get(session=session, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found."
        )
    return user


@router.put(
    "/{user_id}",
    response_model=UserRead,
    summary="Update user details",
    description="Updates existing user profile and settings."
)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    session: Session = Depends(get_session)
) -> UserRead:
    user = crud_user.get(session=session, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found."
        )

    # Validate foreign key if role_id is being modified
    if user_in.role_id is not None and user_in.role_id != user.role_id:
        role = crud_role.get(session=session, id=user_in.role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target role ID {user_in.role_id} does not exist."
            )

    # Validate email uniqueness if changing
    if user_in.email is not None and user_in.email != user.email:
        existing = crud_user.get_by_email(session=session, email=user_in.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{user_in.email}' is already registered to another account."
            )

    return crud_user.update(session=session, db_obj=user, obj_in=user_in)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Deletes a user account and cascades deletion to associated OCR records."
)
def delete_user(
    user_id: int,
    session: Session = Depends(get_session)
) -> None:
    user = crud_user.get(session=session, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found."
        )
    crud_user.remove(session=session, id=user_id)

