import hashlib
import io
import os
from typing import Any
import pypdf
from app.core.database import db
from app.models.document import Document


def save_document_from_memory(user_id: int, file_storage: Any) -> Document:
    """
    Đọc dữ liệu nhị phân trực tiếp từ RAM, bóc tách text (PDF/TXT)
    và lưu trữ trực tiếp dưới dạng BLOB vào SQLite Database.
    Tuyệt đối không lưu file vật lý hay ghi tạm vào thư mục cục bộ.

    :param user_id: ID của người dùng sở hữu tài liệu
    :param file_storage: Đối tượng FileStorage từ Flask request hoặc file-like object
    :return: Đối tượng Document đã lưu vào cơ sở dữ liệu
    """
    # 1. Đọc dữ liệu nhị phân trực tiếp từ RAM
    if hasattr(file_storage, "read"):
        file_bytes = file_storage.read()
    elif isinstance(file_storage, (bytes, bytearray)):
        file_bytes = bytes(file_storage)
    else:
        raise ValueError("file_storage không hợp lệ hoặc không có phương thức read()")

    filename = getattr(file_storage, "filename", None) or "document"
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    file_size = len(file_bytes)

    # 2. Tạo mã băm SHA-256 để chống trùng lặp file trong DB
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    # Kiểm tra xem file đã tồn tại trong DB chưa
    existing_document = Document.query.filter_by(content_hash=file_hash).first()
    if existing_document:
        return existing_document

    # 3. Dùng io.BytesIO(file_bytes) kết hợp pypdf để bóc tách văn bản trong RAM
    extracted_text = ""
    if ext == "pdf":
        try:
            pdf_stream = io.BytesIO(file_bytes)
            reader = pypdf.PdfReader(pdf_stream)
            page_texts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    page_texts.append(text.strip())
            extracted_text = "\n\n".join(page_texts).strip()
        except Exception as exc:
            extracted_text = f"[PDF Extraction Error: {str(exc)}]"
    else:
        # Mặc định coi là file văn bản thuần (TXT, MD, CSV, v.v.)
        extracted_text = file_bytes.decode("utf-8", errors="replace").strip()

    # 4. Tạo và lưu đối tượng Document vào DB với file_blob=file_bytes
    document = Document(
        user_id=user_id,
        filename=filename,
        file_type=ext if ext else "bin",
        file_size_bytes=file_size,
        content_hash=file_hash,
        file_blob=file_bytes,
        extracted_text=extracted_text,
    )
    db.session.add(document)
    db.session.commit()

    return document
