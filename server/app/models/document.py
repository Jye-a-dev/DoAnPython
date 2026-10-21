from datetime import datetime
from app.core.database import db


class Document(db.Model):
    __tablename__ = "documents"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size_bytes = db.Column(db.Integer, nullable=False)
    file_blob = db.Column(db.LargeBinary, nullable=False)
    extracted_text = db.Column(db.Text, nullable=True)
    content_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="documents")
    cards = db.relationship("Card", back_populates="document")
    ai_logs = db.relationship("AIGenerationLog", back_populates="document")

    def __init__(
        self,
        user_id: int,
        filename: str,
        file_type: str,
        file_blob: bytes,
        extracted_text: str | None = None,
        file_size_bytes: int | None = None,
        file_size: int | None = None,
        content_hash: str | None = None,
        file_hash: str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.filename = filename
        self.file_type = file_type
        self.file_blob = file_blob
        self.extracted_text = extracted_text
        self.file_size_bytes = (
            file_size_bytes
            if file_size_bytes is not None
            else (file_size if file_size is not None else len(file_blob))
        )
        self.content_hash = content_hash or file_hash or ""

    @property
    def file_size(self):
        return self.file_size_bytes

    @file_size.setter
    def file_size(self, value):
        self.file_size_bytes = value

    @property
    def file_hash(self):
        return self.content_hash

    @file_hash.setter
    def file_hash(self, value):
        self.content_hash = value

    def to_dict(self, include_blob: bool = False):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "filename": self.filename,
            "file_type": self.file_type,
            "file_size_bytes": self.file_size_bytes,
            "file_size": self.file_size_bytes,
            "content_hash": self.content_hash,
            "file_hash": self.content_hash,
            "extracted_text": self.extracted_text,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_blob and self.file_blob:
            data["file_blob_length"] = len(self.file_blob)
        return data

