from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel
from server.models.common import DateTimeCoerceModel


class ProductBase(SQLModel):
    category_id: Optional[int] = Field(default=None, foreign_key="categories.id", description="Category identifier")
    name: str = Field(max_length=150, nullable=False, description="Product title")
    class_name: Optional[str] = Field(default=None, max_length=50, index=True, description="COCO/YOLO classification tag (lowercase)")
    sku: Optional[str] = Field(default=None, max_length=50, unique=True, index=True, description="Stock Keeping Unit")
    price: float = Field(ge=0.0, nullable=False, description="Unit sales price")
    stock_quantity: int = Field(default=0, ge=0, nullable=False, description="Available inventory count")
    image_url: Optional[str] = Field(default=None, description="Product representative image URL")
    description: Optional[str] = Field(default=None, description="Product specifications and details")
    is_available: bool = Field(default=True, nullable=False, description="Selling availability flag")


class Product(ProductBase, table=True):
    __tablename__ = "products"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class ProductCreate(ProductBase):
    pass


class ProductUpdate(SQLModel):
    category_id: Optional[int] = None
    name: Optional[str] = None
    class_name: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    is_available: Optional[bool] = None


class ProductRead(ProductBase, DateTimeCoerceModel):
    id: int
    created_at: datetime

