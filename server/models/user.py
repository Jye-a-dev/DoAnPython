import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel
from server.models.common import DateTimeCoerceModel


class UserBase(SQLModel):
    """Base schema defining common user attributes."""
    google_id: Optional[str] = Field(default=None, max_length=100, unique=True, description="Google OAuth unique subject identifier")
    email: str = Field(max_length=100, unique=True, index=True, nullable=False, description="User email address")
    full_name: Optional[str] = Field(default=None, max_length=100, description="Full display name")
    avatar_url: Optional[str] = Field(default=None, description="URL of user profile photo")
    is_active: bool = Field(default=True, nullable=False, description="Account active status flag")
    role_id: int = Field(default=2, foreign_key="roles.id", nullable=False, description="Associated role identifier (1=admin, 2=user)")


class User(UserBase, table=True):
    """Database table mapping for 'users' table defined in schema.sql."""
    __tablename__ = "users"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    password_hash: Optional[str] = Field(default=None, max_length=255, description="Scrypt password hash")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class UserCreate(UserBase):
    """Payload schema for creating a new user."""
    password: Optional[str] = Field(default=None, description="Plaintext raw password")


class UserUpdate(SQLModel):
    """Payload schema for updating existing user details."""
    google_id: Optional[str] = Field(default=None, max_length=100)
    email: Optional[str] = Field(default=None, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=100)
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None
    role_id: Optional[int] = None


class UserRead(UserBase, DateTimeCoerceModel):
    """Response schema representing a persisted user record."""
    id: str
    created_at: datetime
