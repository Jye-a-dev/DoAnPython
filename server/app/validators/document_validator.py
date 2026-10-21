import os
from typing import Any, Tuple, Optional

# Kích thước tối đa cho phép: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {"pdf", "txt"}
ALLOWED_MIME_TYPES = {"application/pdf", "text/plain", "application/octet-stream"}


def validate_document_upload(
    file_storage: Any,
) -> Tuple[bool, Optional[str], Optional[bytes], Optional[str]]:
    """
    Kiểm tra tính hợp lệ của file upload:
    - Bắt buộc phải có file_storage và filename.
    - Định dạng file chỉ chấp nhận PDF hoặc TXT (dựa trên đuôi file và MIME type).
    - File không được rỗng (0 byte).
    - Dung lượng tối đa 10MB.

    Trả về:
        (is_valid, error_message, file_bytes, file_type)
    """
    if file_storage is None:
        return False, "Vui lòng chọn file tài liệu để upload", None, None

    filename = getattr(file_storage, "filename", None)
    if not filename or not filename.strip():
        return False, "Tên file không hợp lệ hoặc để trống", None, None

    filename = filename.strip()
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    if ext not in ALLOWED_EXTENSIONS:
        return (
            False,
            f"Định dạng file '.{ext}' không được hỗ trợ. Chỉ chấp nhận application/pdf (.pdf) và text/plain (.txt)",
            None,
            None,
        )

    # Đọc dữ liệu nhị phân vào RAM
    if hasattr(file_storage, "read"):
        file_bytes = file_storage.read()
        # Đặt lại con trỏ để các hàm tiếp theo có thể đọc lại nếu cần
        if hasattr(file_storage, "seek"):
            file_storage.seek(0)
    elif isinstance(file_storage, (bytes, bytearray)):
        file_bytes = bytes(file_storage)
    else:
        return False, "Đối tượng file không hỗ trợ đọc dữ liệu nhị phân", None, None

    # Kiểm tra file rỗng
    if not file_bytes or len(file_bytes) == 0:
        return False, "File upload rỗng (dung lượng 0 bytes)", None, None

    # Kiểm tra kích thước tối đa 10MB
    if len(file_bytes) > MAX_FILE_SIZE:
        return (
            False,
            f"Dung lượng file vượt quá giới hạn tối đa cho phép (10MB). Kích thước file: {len(file_bytes) / (1024 * 1024):.2f}MB",
            None,
            None,
        )

    # Kiểm tra MIME type nếu file_storage cung cấp content_type
    content_type = getattr(file_storage, "content_type", None)
    if content_type:
        content_type_clean = content_type.split(";")[0].strip().lower()
        if (
            content_type_clean not in ALLOWED_MIME_TYPES
            and not content_type_clean.startswith("text/")
        ):
            return (
                False,
                f"MIME type '{content_type_clean}' không được chấp nhận. Chỉ cho phép application/pdf và text/plain",
                None,
                None,
            )

    return True, None, file_bytes, ext
