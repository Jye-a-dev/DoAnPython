from typing import Any, Dict, Optional, Tuple


def validate_deck_payload(
    data: Any, is_update: bool = False
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate payload cho thao tác tạo hoặc cập nhật bộ thẻ (Deck).
    - title: không được để trống hoặc chỉ chứa khoảng trắng, tối đa 150 ký tự.
    - user_id: phải là số nguyên dương hợp lệ (bắt buộc khi tạo mới).

    Trả về:
        (is_valid, error_message, cleaned_data)
    """
    if not isinstance(data, dict):
        return False, "Dữ liệu payload phải là JSON object", None

    title = data.get("title")
    user_id = data.get("user_id")
    description = data.get("description")
    is_public = data.get("is_public", False)
    folder_id = data.get("folder_id")
    category_id = data.get("category_id")

    # Kiểm tra title
    if not is_update or "title" in data:
        if title is None or not isinstance(title, str) or not title.strip():
            return False, "Tiêu đề bộ thẻ (title) không được để trống hoặc chỉ chứa khoảng trắng", None
        if len(title.strip()) > 150:
            return False, "Tiêu đề bộ thẻ không được vượt quá 150 ký tự", None

    # Kiểm tra user_id
    cleaned_user_id = None
    if not is_update or "user_id" in data:
        if user_id is None:
            if not is_update:
                return False, "Trường 'user_id' là bắt buộc khi tạo bộ thẻ mới", None
        else:
            try:
                cleaned_user_id = int(user_id)
                if cleaned_user_id <= 0:
                    return False, "Trường 'user_id' phải là số nguyên dương", None
            except (ValueError, TypeError):
                return False, "Trường 'user_id' không hợp lệ (phải là số nguyên)", None

    cleaned_data: Dict[str, Any] = {}
    if title is not None:
        cleaned_data["title"] = title.strip()
    if cleaned_user_id is not None:
        cleaned_data["user_id"] = cleaned_user_id
    if description is not None:
        cleaned_data["description"] = (
            description.strip() if isinstance(description, str) else None
        )
    if "is_public" in data or not is_update:
        cleaned_data["is_public"] = bool(is_public)

    if folder_id is not None:
        try:
            cleaned_data["folder_id"] = int(folder_id)
        except (ValueError, TypeError):
            return False, "Trường 'folder_id' phải là số nguyên", None
    elif not is_update:
        cleaned_data["folder_id"] = None

    if category_id is not None:
        try:
            cleaned_data["category_id"] = int(category_id)
        except (ValueError, TypeError):
            return False, "Trường 'category_id' phải là số nguyên", None
    elif not is_update:
        cleaned_data["category_id"] = None

    return True, None, cleaned_data

