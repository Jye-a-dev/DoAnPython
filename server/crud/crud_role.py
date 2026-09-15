from typing import Optional
from sqlmodel import Session, select
from server.crud.base import CRUDBase
from server.models.role import Role, RoleCreate, RoleUpdate


class CRUDRole(CRUDBase[Role, RoleCreate, RoleUpdate]):
    """Role-specific repository operations."""

    def get_by_name(self, session: Session, name: str) -> Optional[Role]:
        """Lookup a role by its unique name identifier."""
        statement = select(Role).where(Role.name == name)
        return session.exec(statement).first()


crud_role = CRUDRole(Role)

