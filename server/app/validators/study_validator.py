from typing import Any, Dict, Optional, Tuple

VALID_REVIEW_RATINGS = {1, 2, 3, 4}


def validate_study_session_payload(
    data: Any,
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate payload mở phiên học mới (Study Session).
    - user_id: phải là số nguyên dương.
    - deck_id: phải là số nguyên dương.
    """
    if not isinstance(data, dict):
        return False, "Dữ liệu payload phải là JSON object", None

    user_id = data.get("user_id")
    deck_id = data.get("deck_id")

    if user_id is None:
        return False, "Trường 'user_id' không được để trống", None
    try:
        user_id_int = int(user_id)
        if user_id_int <= 0:
            return False, "Trường 'user_id' phải là số nguyên dương", None
    except (ValueError, TypeError):
        return False, "Trường 'user_id' phải là số nguyên", None

    if deck_id is None:
        return False, "Trường 'deck_id' không được để trống", None
    try:
        deck_id_int = int(deck_id)
        if deck_id_int <= 0:
            return False, "Trường 'deck_id' phải là số nguyên dương", None
    except (ValueError, TypeError):
        return False, "Trường 'deck_id' phải là số nguyên", None

    return True, None, {"user_id": user_id_int, "deck_id": deck_id_int}


def validate_study_review_payload(
    data: Any,
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate payload ghi nhận đánh giá Spaced Repetition (SRS).
    - review_rating: phải thuộc [1, 2, 3, 4].
    - ease_factor: phải > 1.3.
    - card_id: phải là số nguyên dương.
    - session_id: tùy chọn, số nguyên dương.
    - user_id: tùy chọn hoặc bắt buộc nếu không truyền session.
    """
    if not isinstance(data, dict):
        return False, "Dữ liệu payload phải là JSON object", None

    # Hỗ trợ cả 'review_rating' và 'rating'
    rating_raw = data.get("review_rating") if "review_rating" in data else data.get("rating")
    if rating_raw is None:
        return False, "Trường 'review_rating' không được để trống", None
    try:
        review_rating = int(rating_raw)
        if review_rating not in VALID_REVIEW_RATINGS:
            return (
                False,
                f"Giá trị review_rating ({review_rating}) không hợp lệ. Phải thuộc tập [1, 2, 3, 4]",
                None,
            )
    except (ValueError, TypeError):
        return False, "Trường 'review_rating' phải là số nguyên thuộc [1, 2, 3, 4]", None

    ease_factor_raw = data.get("ease_factor", 2.5)
    try:
        ease_factor = float(ease_factor_raw)
        if ease_factor <= 1.3:
            return (
                False,
                f"Hệ số ease_factor ({ease_factor}) không hợp lệ. Phải lớn hơn 1.3",
                None,
            )
    except (ValueError, TypeError):
        return False, "Trường 'ease_factor' phải là số thực lớn hơn 1.3", None

    card_id = data.get("card_id")
    if card_id is None:
        return False, "Trường 'card_id' không được để trống", None
    try:
        card_id_int = int(card_id)
        if card_id_int <= 0:
            return False, "Trường 'card_id' phải là số nguyên dương", None
    except (ValueError, TypeError):
        return False, "Trường 'card_id' phải là số nguyên", None

    session_id = data.get("session_id")
    cleaned_session_id = None
    if session_id is not None:
        try:
            cleaned_session_id = int(session_id)
            if cleaned_session_id <= 0:
                return False, "Trường 'session_id' phải là số nguyên dương", None
        except (ValueError, TypeError):
            return False, "Trường 'session_id' phải là số nguyên", None

    user_id = data.get("user_id")
    cleaned_user_id = None
    if user_id is not None:
        try:
            cleaned_user_id = int(user_id)
            if cleaned_user_id <= 0:
                return False, "Trường 'user_id' phải là số nguyên dương", None
        except (ValueError, TypeError):
            return False, "Trường 'user_id' phải là số nguyên", None

    interval_days = data.get("interval_days", 1)
    try:
        interval_days_int = max(1, int(interval_days))
    except (ValueError, TypeError):
        interval_days_int = 1

    cleaned_data: Dict[str, Any] = {
        "card_id": card_id_int,
        "session_id": cleaned_session_id,
        "user_id": cleaned_user_id,
        "review_rating": review_rating,
        "ease_factor": ease_factor,
        "interval_days": interval_days_int,
    }
    return True, None, cleaned_data

