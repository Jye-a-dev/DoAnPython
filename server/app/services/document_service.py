import hashlib
import io
import os
from typing import Any, List, Optional
import pypdf
from app.core.database import db
from app.models.document import Document


def process_and_save_document(user_id: int, file_storage: Any) -> Document:
    """
    Xử lý và lưu trữ tài liệu hoàn toàn trong bộ nhớ RAM:
    - Đọc binary từ file_storage.read().
    - Tính hash SHA-256 (hashlib.sha256(file_bytes).hexdigest()) và kiểm tra chống trùng lặp.
    - Đọc text trực tiếp từ io.BytesIO(file_bytes) bằng pypdf.PdfReader (nếu PDF) hoặc decode('utf-8', errors='ignore') (nếu TXT).
    - Khởi tạo Document và lưu vào cột BLOB documents.file_blob. Tuyệt đối không ghi file cục bộ.

    :param user_id: ID người dùng sở hữu tài liệu
    :param file_storage: FileStorage đối tượng upload từ Flask request hoặc file-like object
    :return: Thực thể Document đã lưu trong cơ sở dữ liệu
    """
    if hasattr(file_storage, "read"):
        file_bytes = file_storage.read()
    elif isinstance(file_storage, (bytes, bytearray)):
        file_bytes = bytes(file_storage)
    else:
        raise ValueError("file_storage không hợp lệ hoặc không có phương thức read()")

    filename = getattr(file_storage, "filename", None) or "document"
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    if not ext:
        ext = "txt"
    file_size = len(file_bytes)

    # 1. Tính mã băm SHA-256 để chống trùng lặp file trong database
    content_hash = hashlib.sha256(file_bytes).hexdigest()
    existing_document = Document.query.filter_by(content_hash=content_hash).first()
    if existing_document:
        return existing_document

    # 2. Đọc text trực tiếp từ RAM qua io.BytesIO(file_bytes)
    extracted_text = ""
    if ext == "pdf":
        try:
            pdf_stream = io.BytesIO(file_bytes)
            reader = pypdf.PdfReader(pdf_stream)
            page_texts = [p.extract_text() or "" for p in reader.pages]
            extracted_text = "\n\n".join(
                t.strip() for t in page_texts if t.strip()
            ).strip()
        except Exception as exc:
            extracted_text = f"[PDF Extraction Error: {str(exc)}]"
    else:
        extracted_text = file_bytes.decode("utf-8", errors="ignore").strip()

    # 3. Khởi tạo Document và lưu thẳng vào cột BLOB mà không tạo file trung gian
    document = Document(
        user_id=user_id,
        filename=filename,
        file_type=ext,
        file_size_bytes=file_size,
        file_blob=file_bytes,
        extracted_text=extracted_text,
        content_hash=content_hash,
    )
    db.session.add(document)
    db.session.commit()

    return document


# Tương thích ngược với các tên gọi cũ
save_document_from_memory = process_and_save_document


def get_document_by_id(doc_id: int) -> Optional[Document]:
    """Truy vấn Document theo ID."""
    return db.session.get(Document, doc_id)


def list_documents(user_id: Optional[int] = None) -> List[Document]:
    """Lấy danh sách Document, hỗ trợ lọc theo user_id."""
    query = Document.query
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    return query.order_by(Document.created_at.desc()).all()


def delete_document(doc_id: int) -> bool:
    """Xóa Document khỏi cơ sở dữ liệu."""
    doc = db.session.get(Document, doc_id)
    if not doc:
        return False
    db.session.delete(doc)
    db.session.commit()
    return True
