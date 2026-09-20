from typing import Optional
from sqlmodel import Field, SQLModel
from server.models.common import DateTimeCoerceModel


class CategoryBase(SQLModel):
    name: str = Field(max_length=100, unique=True, nullable=False, description="Category name")
    slug: str = Field(max_length=100, unique=True, nullable=False, description="SEO-friendly slug")
    description: Optional[str] = Field(default=None, description="Category description")


class Category(CategoryBase, table=True):
    __tablename__ = "categories"

    id: Optional[int] = Field(default=None, primary_key=True)


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase, DateTimeCoerceModel):
    id: int

