from typing import Any, Dict, Optional, Tuple

VALID_DIFFICULTIES = {"easy", "medium", "hard"}


def validate_card_payload(
    data: Any, is_update: bool = False
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Validate payload cho thao tác tạo hoặc cập nhật flashcard.
    - question và answer không được để trống hoặc chỉ chứa khoảng trắng.
    - difficulty (nếu có) phải thuộc {'easy', 'medium', 'hard'}.

    Trả về:
        (is_valid, error_message, cleaned_data)
    """
    if not isinstance(data, dict):
        return False, "Dữ liệu payload phải là JSON object", None

    question = (
        data.get("question") if data.get("question") is not None else data.get("front")
    )
    answer = data.get("answer") if data.get("answer") is not None else data.get("back")
    explanation = data.get("explanation")
    difficulty = data.get("difficulty", "medium")
    deck_id = data.get("deck_id")
    document_id = data.get("document_id")
    tags = data.get("tags")

    # Khi tạo mới: question và answer là bắt buộc
    if not is_update or "question" in data:
        if question is None or not isinstance(question, str) or not question.strip():
            return (
                False,
                "Trường 'question' không được để trống hoặc chỉ chứa khoảng trắng",
                None,
            )

    if not is_update or "answer" in data:
        if answer is None or not isinstance(answer, str) or not answer.strip():
            return (
                False,
                "Trường 'answer' không được để trống hoặc chỉ chứa khoảng trắng",
                None,
            )

    cleaned_difficulty = "medium"
    if difficulty is not None:
        if (
            not isinstance(difficulty, str)
            or difficulty.lower().strip() not in VALID_DIFFICULTIES
        ):
            return (
                False,
                f"Độ khó '{difficulty}' không hợp lệ. Chỉ chấp nhận: {', '.join(VALID_DIFFICULTIES)}",
                None,
            )
        cleaned_difficulty = difficulty.lower().strip()

    cleaned_data: Dict[str, Any] = {}
    if question is not None:
        cleaned_data["question"] = question.strip()
    if answer is not None:
        cleaned_data["answer"] = answer.strip()
    if explanation is not None:
        cleaned_data["explanation"] = (
            explanation.strip() if isinstance(explanation, str) else None
        )
    if "difficulty" in data or not is_update:
        cleaned_data["difficulty"] = cleaned_difficulty
    if deck_id is not None:
        try:
            cleaned_data["deck_id"] = int(deck_id)
        except (ValueError, TypeError):
            return False, "Trường 'deck_id' phải là số nguyên", None
    elif not is_update:
        cleaned_data["deck_id"] = None

    if document_id is not None:
        try:
            cleaned_data["document_id"] = int(document_id)
        except (ValueError, TypeError):
            return False, "Trường 'document_id' phải là số nguyên", None
    elif not is_update:
        cleaned_data["document_id"] = None

    if tags is not None:
        if not isinstance(tags, list):
            return False, "Trường 'tags' phải là danh sách các nhãn (chuỗi)", None
        cleaned_tags = [str(t).strip() for t in tags if str(t).strip()]
        cleaned_data["tags"] = cleaned_tags

    return True, None, cleaned_data
