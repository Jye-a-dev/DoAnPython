from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session
from server.crud.crud_role import crud_role
from server.database import get_session
from server.models.common import CountResponse
from server.models.role import RoleCreate, RoleRead, RoleUpdate

router = APIRouter(prefix="/api/v1/roles", tags=["Roles"])


@router.get(
    "/count",
    response_model=CountResponse,
    summary="Get total roles count",
    description="Calculates total number of registered role records in the system."
)
def count_roles(
    session: Session = Depends(get_session)
) -> CountResponse:
    total = crud_role.count(session=session)
    return CountResponse(count=total)


@router.post(
    "",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new role",
    description="Registers a new role with unique name identifier and optional description."
)
def create_role(
    role_in: RoleCreate,
    session: Session = Depends(get_session)
) -> RoleRead:
    existing = crud_role.get_by_name(session=session, name=role_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Role with name '{role_in.name}' already exists."
        )
    return crud_role.create(session=session, obj_in=role_in)


@router.get(
    "",
    response_model=List[RoleRead],
    summary="List all roles",
    description="Retrieves paginated list of system roles."
)
def list_roles(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Maximum items to return"),
    session: Session = Depends(get_session)
) -> List[RoleRead]:
    return crud_role.get_multi(session=session, skip=skip, limit=limit)


@router.get(
    "/{role_id}",
    response_model=RoleRead,
    summary="Get role by ID",
    description="Retrieves detail of a specific role by its primary key."
)
def get_role(
    role_id: int,
    session: Session = Depends(get_session)
) -> RoleRead:
    role = crud_role.get(session=session, id=role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found."
        )
    return role


@router.put(
    "/{role_id}",
    response_model=RoleRead,
    summary="Update role",
    description="Updates role details (name, description)."
)
def update_role(
    role_id: int,
    role_in: RoleUpdate,
    session: Session = Depends(get_session)
) -> RoleRead:
    role = crud_role.get(session=session, id=role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found."
        )
    if role_in.name and role_in.name != role.name:
        existing = crud_role.get_by_name(session=session, name=role_in.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Role name '{role_in.name}' is already in use."
            )
    return crud_role.update(session=session, db_obj=role, obj_in=role_in)


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete role",
    description="Removes a role from the database. Will fail if foreign key references prevent deletion."
)
def delete_role(
    role_id: int,
    session: Session = Depends(get_session)
) -> None:
    role = crud_role.get(session=session, id=role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with ID {role_id} not found."
        )
    try:
        crud_role.remove(session=session, id=role_id)
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete role: {str(e)}"
        )

