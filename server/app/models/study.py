from datetime import datetime
from app.core.database import db


class StudySession(db.Model):
    __tablename__ = "study_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    deck_id = db.Column(
        db.Integer,
        db.ForeignKey("decks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ended_at = db.Column(db.DateTime, nullable=True)
    total_reviewed = db.Column(db.Integer, default=0, nullable=False)

    user = db.relationship("User", back_populates="study_sessions")
    deck = db.relationship("Deck", back_populates="study_sessions")
    reviews = db.relationship(
        "StudyReview", back_populates="session", cascade="all, delete-orphan"
    )

    # Thuộc tính tương thích ngược
    @property
    def start_time(self):
        return self.started_at

    @start_time.setter
    def start_time(self, value):
        self.started_at = value

    @property
    def end_time(self):
        return self.ended_at

    @end_time.setter
    def end_time(self, value):
        self.ended_at = value

    @property
    def total_cards_reviewed(self):
        return self.total_reviewed

    @total_cards_reviewed.setter
    def total_cards_reviewed(self, value):
        self.total_reviewed = value

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "deck_id": self.deck_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "total_reviewed": self.total_reviewed,
            "start_time": self.started_at.isoformat() if self.started_at else None,
            "end_time": self.ended_at.isoformat() if self.ended_at else None,
            "total_cards_reviewed": self.total_reviewed,
        }


class StudyReview(db.Model):
    __tablename__ = "study_reviews"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(
        db.Integer,
        db.ForeignKey("study_sessions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    card_id = db.Column(
        db.Integer,
        db.ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    review_rating = db.Column(db.Integer, nullable=False)
    ease_factor = db.Column(db.Float, default=2.5, nullable=False)
    interval_days = db.Column(db.Integer, default=1, nullable=False)
    repetitions = db.Column(db.Integer, default=0, nullable=False)
    next_review_date = db.Column(db.DateTime, nullable=True, index=True)
    reviewed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    session = db.relationship("StudySession", back_populates="reviews")
    card = db.relationship("Card", back_populates="study_reviews")
    user = db.relationship("User", back_populates="study_reviews")

    @property
    def rating(self):
        return self.review_rating

    @rating.setter
    def rating(self, value):
        self.review_rating = value

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "card_id": self.card_id,
            "user_id": self.user_id,
            "review_rating": self.review_rating,
            "rating": self.review_rating,
            "ease_factor": self.ease_factor,
            "interval_days": self.interval_days,
            "repetitions": self.repetitions,
            "next_review_date": (
                self.next_review_date.isoformat() if self.next_review_date else None
            ),
            "reviewed_at": (self.reviewed_at.isoformat() if self.reviewed_at else None),
        }


class UserFavorite(db.Model):
    __tablename__ = "user_favorites"
    __table_args__ = (
        db.UniqueConstraint("user_id", "card_id", name="uq_user_card_favorite"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    deck_id = db.Column(
        db.Integer,
        db.ForeignKey("decks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    card_id = db.Column(
        db.Integer,
        db.ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="favorites")
    deck = db.relationship("Deck", back_populates="favorites")
    card = db.relationship("Card", back_populates="favorites")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "deck_id": self.deck_id,
            "card_id": self.card_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AIGenerationLog(db.Model):
    __tablename__ = "ai_generation_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id = db.Column(
        db.Integer,
        db.ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    deck_id = db.Column(
        db.Integer,
        db.ForeignKey("decks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    model_name = db.Column(db.String(100), default="flan-t5-base", nullable=False)
    cards_generated = db.Column(db.Integer, default=0, nullable=False)
    inference_time_seconds = db.Column(db.Float, default=0.0, nullable=False)
    prompt_tokens = db.Column(db.Integer, default=0, nullable=False)
    completion_tokens = db.Column(db.Integer, default=0, nullable=False)
    status = db.Column(db.String(50), default="SUCCESS", nullable=False)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="ai_logs")
    document = db.relationship("Document", back_populates="ai_logs")
    deck = db.relationship("Deck", back_populates="ai_logs")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "document_id": self.document_id,
            "deck_id": self.deck_id,
            "model_name": self.model_name,
            "cards_generated": self.cards_generated,
            "inference_time_seconds": self.inference_time_seconds,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
