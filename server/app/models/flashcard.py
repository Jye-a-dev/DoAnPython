from app.core.database import db


class Flashcard(db.Model):
    __tablename__ = "flashcards"

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.Text, nullable=False)

    def __init__(self, question: str, answer: str, **kwargs):
        super().__init__(**kwargs)
        self.question = question
        self.answer = answer

    def to_dict(self):
        return {"id": self.id, "question": self.question, "answer": self.answer}
