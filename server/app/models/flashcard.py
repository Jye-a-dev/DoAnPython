from datetime import datetime
from app.core.database import db

# Bảng phụ nhiều - nhiều giữa Card và Tag
card_tags = db.Table(
    "card_tags",
    db.Column(
        "card_id",
        db.Integer,
        db.ForeignKey("cards.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "tag_id",
        db.Integer,
        db.ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column("created_at", db.DateTime, default=datetime.utcnow, nullable=False),
)


class Deck(db.Model):
    __tablename__ = "decks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    folder_id = db.Column(
        db.Integer,
        db.ForeignKey("folders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_public = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = db.relationship("User", back_populates="decks")
    folder = db.relationship("Folder", back_populates="decks")
    category = db.relationship("Category", back_populates="decks")
    cards = db.relationship("Card", back_populates="deck", cascade="all, delete-orphan")
    study_sessions = db.relationship(
        "StudySession", back_populates="deck", cascade="all, delete-orphan"
    )
    favorites = db.relationship(
        "UserFavorite", back_populates="deck", cascade="all, delete-orphan"
    )
    ai_logs = db.relationship("AIGenerationLog", back_populates="deck")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "folder_id": self.folder_id,
            "category_id": self.category_id,
            "title": self.title,
            "description": self.description,
            "is_public": self.is_public,
            "card_count": len(self.cards) if self.cards else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Card(db.Model):
    __tablename__ = "cards"

    id = db.Column(db.Integer, primary_key=True)
    deck_id = db.Column(
        db.Integer,
        db.ForeignKey("decks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    document_id = db.Column(
        db.Integer,
        db.ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text, nullable=True)
    difficulty = db.Column(db.String(20), default="medium", nullable=False)
    tts_text = db.Column(db.Text, nullable=True)
    tts_lang = db.Column(db.String(10), default="en-US", nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    deck = db.relationship("Deck", back_populates="cards")
    document = db.relationship("Document", back_populates="cards")
    tags = db.relationship("Tag", secondary=card_tags, back_populates="cards")
    study_reviews = db.relationship(
        "StudyReview", back_populates="card", cascade="all, delete-orphan"
    )
    favorites = db.relationship(
        "UserFavorite", back_populates="card", cascade="all, delete-orphan"
    )

    @property
    def front(self) -> str:
        return self.question

    @front.setter
    def front(self, value: str):
        self.question = value

    @property
    def back(self) -> str:
        return self.answer

    @back.setter
    def back(self, value: str):
        self.answer = value

    def __init__(
        self,
        question: str = "",
        answer: str = "",
        deck_id: int | None = None,
        document_id: int | None = None,
        explanation: str | None = None,
        difficulty: str = "medium",
        front: str | None = None,
        back: str | None = None,
        tts_text: str | None = None,
        tts_lang: str | None = "en-US",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.question = front if front is not None else question
        self.answer = back if back is not None else answer
        self.deck_id = deck_id
        self.document_id = document_id
        self.explanation = explanation
        self.difficulty = difficulty
        self.tts_text = tts_text
        self.tts_lang = tts_lang if tts_lang is not None else "en-US"

    def to_dict(self):
        return {
            "id": self.id,
            "deck_id": self.deck_id,
            "document_id": self.document_id,
            "question": self.question,
            "answer": self.answer,
            "front": self.question,
            "back": self.answer,
            "explanation": self.explanation,
            "difficulty": self.difficulty,
            "tts_text": self.tts_text,
            "tts_lang": self.tts_lang,
            "tags": [t.name for t in self.tags] if self.tags else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Tương thích ngược với các module sử dụng tên Flashcard
Flashcard = Card


class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="tags")
    cards = db.relationship("Card", secondary=card_tags, back_populates="tags")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
