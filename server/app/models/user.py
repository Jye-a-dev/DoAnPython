from datetime import datetime
from app.core.database import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    profile = db.relationship(
        "UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    categories = db.relationship(
        "Category", back_populates="user", cascade="all, delete-orphan"
    )
    folders = db.relationship(
        "Folder", back_populates="user", cascade="all, delete-orphan"
    )
    decks = db.relationship(
        "Deck", back_populates="user", cascade="all, delete-orphan"
    )
    documents = db.relationship(
        "Document", back_populates="user", cascade="all, delete-orphan"
    )
    tags = db.relationship(
        "Tag", back_populates="user", cascade="all, delete-orphan"
    )
    study_sessions = db.relationship(
        "StudySession", back_populates="user", cascade="all, delete-orphan"
    )
    study_reviews = db.relationship(
        "StudyReview", back_populates="user", cascade="all, delete-orphan"
    )
    favorites = db.relationship(
        "UserFavorite", back_populates="user", cascade="all, delete-orphan"
    )
    ai_logs = db.relationship(
        "AIGenerationLog", back_populates="user", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    full_name = db.Column(db.String(120), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    timezone = db.Column(db.String(50), default="UTC", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = db.relationship("User", back_populates="profile")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "timezone": self.timezone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

