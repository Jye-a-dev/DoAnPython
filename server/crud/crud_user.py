from typing import List, Optional
from sqlmodel import Session, col, func, select
from server.crud.base import CRUDBase
from server.models.user import User, UserCreate, UserUpdate


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """User-specific repository operations."""

    def get_by_email(self, session: Session, email: str) -> Optional[User]:
        """Fetch user by unique email address."""
        statement = select(User).where(User.email == email)
        return session.exec(statement).first()

    def get_by_google_id(self, session: Session, google_id: str) -> Optional[User]:
        """Fetch user by unique Google OAuth ID."""
        statement = select(User).where(User.google_id == google_id)
        return session.exec(statement).first()

    def get_multi_filtered(
        self,
        session: Session,
        skip: int = 0,
        limit: int = 100,
        role_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> List[User]:
        """Retrieve paginated users with optional role, activity, and name/email filters."""
        statement = select(User)
        if role_id is not None:
            statement = statement.where(User.role_id == role_id)
        if is_active is not None:
            statement = statement.where(User.is_active == is_active)
        if search:
            search_pattern = f"%{search}%"
            statement = statement.where(
                (col(User.email).ilike(search_pattern)) | (col(User.full_name).ilike(search_pattern))
            )
        statement = statement.offset(skip).limit(limit)
        return list(session.exec(statement).all())

    def count_filtered(
        self,
        session: Session,
        role_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> int:
        """Calculate total number of users matching specified filter criteria."""
        statement = select(func.count()).select_from(User)
        if role_id is not None:
            statement = statement.where(User.role_id == role_id)
        if is_active is not None:
            statement = statement.where(User.is_active == is_active)
        if search:
            search_pattern = f"%{search}%"
            statement = statement.where(
                (col(User.email).ilike(search_pattern)) | (col(User.full_name).ilike(search_pattern))
            )
        result = session.exec(statement).one()
        return int(result)


crud_user = CRUDUser(User)

