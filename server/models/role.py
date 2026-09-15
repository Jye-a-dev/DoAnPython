from typing import Optional
from sqlmodel import Field, SQLModel
from server.models.common import DateTimeCoerceModel


class RoleBase(SQLModel):
    """Base schema defining common role attributes."""
    name: str = Field(max_length=20, unique=True, nullable=False, description="Unique identifier name for role (e.g. admin, user)")
    description: Optional[str] = Field(default=None, description="Detailed description of role responsibilities")


class Role(RoleBase, table=True):
    """Database table mapping for 'roles' table defined in schema.sql."""
    __tablename__ = "roles"

    id: Optional[int] = Field(default=None, primary_key=True)


class RoleCreate(RoleBase):
    """Payload schema for creating a new role."""
    pass


class RoleUpdate(SQLModel):
    """Payload schema for updating an existing role."""
    name: Optional[str] = Field(default=None, max_length=20)
    description: Optional[str] = None


class RoleRead(RoleBase, DateTimeCoerceModel):
    """Response schema representing a persisted role record."""
    id: int

