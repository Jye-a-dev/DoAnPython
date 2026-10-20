from datetime import datetime
from app.core.database import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    color_code = db.Column(db.String(7), default="#3B82F6", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="categories")
    folders = db.relationship("Folder", back_populates="category")
    decks = db.relationship("Deck", back_populates="category")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "color_code": self.color_code,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Folder(db.Model):
    __tablename__ = "folders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    parent_id = db.Column(
        db.Integer,
        db.ForeignKey("folders.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="folders")
    category = db.relationship("Category", back_populates="folders")
    parent = db.relationship(
        "Folder",
        remote_side=[id],
        backref=db.backref("children", cascade="all, delete-orphan"),
    )
    decks = db.relationship("Deck", back_populates="folder")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "parent_id": self.parent_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

