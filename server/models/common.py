from datetime import datetime
from typing import Any, Union
from pydantic import BaseModel, ConfigDict, field_validator


class CountResponse(BaseModel):
    """Standardized response schema for aggregate count queries."""
    count: int


class MessageResponse(BaseModel):
    """Standardized response schema for operational status messages."""
    message: str
    success: bool = True


class DateTimeCoerceModel(BaseModel):
    """
    Base Pydantic schema configured for SQLite ORM attributes.
    Coerces raw SQLite ISO strings into native Python datetime objects to prevent ResponseValidationError.
    """
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    @field_validator("*", mode="before")
    @classmethod
    def parse_sqlite_datetime(cls, v: Any) -> Any:
        if isinstance(v, str):
            # Parse standard ISO or SQLite formatted datetime strings
            # Examples: '2026-09-15 14:30:00', '2026-09-15T14:30:00.000Z'
            cleaned = v.replace("Z", "+00:00")
            try:
                return datetime.fromisoformat(cleaned)
            except (ValueError, TypeError):
                pass
        return v

