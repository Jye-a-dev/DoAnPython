from datetime import datetime
from app.core.database import db

# Bảng liên kết nhiều - nhiều giữa Card và Tag
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

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "folder_id": self.folder_id,
            "category_id": self.category_id,
            "title": self.title,
            "description": self.description,
            "is_public": self.is_public,
            "card_count": len(self.cards) if isinstance(self.cards, list) else 0,
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

    def __init__(
        self,
        question: str = "",
        answer: str = "",
        deck_id: int | None = None,
        document_id: int | None = None,
        explanation: str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.question = question
        self.answer = answer
        self.deck_id = deck_id
        self.document_id = document_id
        self.explanation = explanation

    def to_dict(self):
        return {
            "id": self.id,
            "deck_id": self.deck_id,
            "document_id": self.document_id,
            "question": self.question,
            "answer": self.answer,
            "explanation": self.explanation,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Tương thích ngược với các endpoint cũ
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
    name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="tags")
    cards = db.relationship("Card", secondary=card_tags, back_populates="tags")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
