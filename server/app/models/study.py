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
    start_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    total_cards_reviewed = db.Column(db.Integer, default=0, nullable=False)

    user = db.relationship("User", back_populates="study_sessions")
    deck = db.relationship("Deck", back_populates="study_sessions")
    reviews = db.relationship(
        "StudyReview", back_populates="session", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "deck_id": self.deck_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_cards_reviewed": self.total_cards_reviewed,
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

    # SM-2 Parameters:
    # rating: Đánh giá chất lượng nhớ (0-5)
    # ease_factor: Hệ số dễ (mặc định 2.5, min 1.3)
    # interval_days: Khoảng cách ngày ôn tập tiếp theo (mặc định 1)
    # repetitions: Số lần lặp lại liên tiếp đạt chuẩn
    rating = db.Column(db.Integer, nullable=False)
    ease_factor = db.Column(db.Float, default=2.5, nullable=False)
    interval_days = db.Column(db.Integer, default=1, nullable=False)
    repetitions = db.Column(db.Integer, default=0, nullable=False)
    next_review_date = db.Column(db.DateTime, nullable=True, index=True)
    reviewed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    session = db.relationship("StudySession", back_populates="reviews")
    card = db.relationship("Card", back_populates="study_reviews")
    user = db.relationship("User", back_populates="study_reviews")

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "card_id": self.card_id,
            "user_id": self.user_id,
            "rating": self.rating,
            "ease_factor": self.ease_factor,
            "interval_days": self.interval_days,
            "repetitions": self.repetitions,
            "next_review_date": (
                self.next_review_date.isoformat() if self.next_review_date else None
            ),
            "reviewed_at": (
                self.reviewed_at.isoformat() if self.reviewed_at else None
            ),
        }


class UserFavorite(db.Model):
    __tablename__ = "user_favorites"

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
    prompt_tokens = db.Column(db.Integer, default=0, nullable=False)
    completion_tokens = db.Column(db.Integer, default=0, nullable=False)
    model_name = db.Column(db.String(100), default="flan-t5-base", nullable=False)
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
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "model_name": self.model_name,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

