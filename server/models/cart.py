import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel
from server.models.common import DateTimeCoerceModel


class CartItemBase(SQLModel):
    user_id: str = Field(foreign_key="users.id", nullable=False, index=True, description="Owner user identifier")
    product_id: str = Field(foreign_key="products.id", nullable=False, description="Referenced product identifier")
    record_id: Optional[str] = Field(default=None, foreign_key="ocr_records.id", nullable=True, description="Associated camera scan record")
    quantity: int = Field(default=1, ge=1, nullable=False, description="Item quantity in cart")


class CartItem(CartItemBase, table=True):
    __tablename__ = "cart_items"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class CartItemCreate(SQLModel):
    product_id: str = Field(..., description="Target product identifier")
    quantity: int = Field(default=1, ge=1, description="Quantity to add")
    record_id: Optional[str] = Field(default=None, description="Optional scan record ID that triggered this add")


class CartItemUpdate(SQLModel):
    quantity: int = Field(..., ge=0, description="Updated quantity (0 to remove)")


class CartItemRead(CartItemBase, DateTimeCoerceModel):
    id: str
    user_id: str
    product_id: str
    record_id: Optional[str] = None
    created_at: datetime
