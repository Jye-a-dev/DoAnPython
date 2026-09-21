import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlmodel import Field, SQLModel
from server.models.common import DateTimeCoerceModel


class OrderBase(SQLModel):
    user_id: str = Field(foreign_key="users.id", nullable=False, index=True, description="Purchaser user identifier")
    total_amount: float = Field(ge=0.0, nullable=False, description="Total order value in VND")
    shipping_address: str = Field(nullable=False, description="Delivery shipping address")
    phone_number: str = Field(max_length=20, nullable=False, description="Contact phone number")
    status: str = Field(default="pending", max_length=30, index=True, nullable=False, description="Order status: pending, paid, shipped, cancelled")
    audio_confirmation_url: Optional[str] = Field(default=None, description="Stream URL for TTS audio order confirmation")


class Order(OrderBase, table=True):
    __tablename__ = "orders"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class OrderItemBase(SQLModel):
    order_id: str = Field(foreign_key="orders.id", nullable=False, index=True, description="Parent order identifier")
    product_id: str = Field(foreign_key="products.id", nullable=False, description="Purchased product identifier")
    quantity: int = Field(ge=1, nullable=False, description="Purchased quantity")
    unit_price: float = Field(ge=0.0, nullable=False, description="Historical unit price at purchase time")


class OrderItem(OrderItemBase, table=True):
    __tablename__ = "order_items"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)


class OrderCreate(SQLModel):
    shipping_address: str = Field(..., description="Delivery shipping destination")
    phone_number: str = Field(..., description="Customer contact phone number")


class OrderItemRead(DateTimeCoerceModel):
    id: str
    order_id: str
    product_id: str
    quantity: int
    unit_price: float
    product_name: Optional[str] = None


class OrderRead(OrderBase, DateTimeCoerceModel):
    id: str
    created_at: datetime
    items: List[OrderItemRead] = []
