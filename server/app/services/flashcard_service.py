from datetime import datetime
from typing import Any, Dict, List, Optional
from app.core.database import db
from app.models.flashcard import Card, Deck, Tag


# ==============================================================================
# DECK CRUD SERVICES
# ==============================================================================


def create_deck(data: Dict[str, Any]) -> Deck:
    """Tạo mới một bộ thẻ (Deck)."""
    deck = Deck()
    deck.user_id = data["user_id"]
    deck.title = data["title"]
    deck.description = data.get("description")
    deck.folder_id = data.get("folder_id")
    deck.category_id = data.get("category_id")
    deck.is_public = data.get("is_public", False)
    db.session.add(deck)
    db.session.commit()
    return deck


def get_deck_by_id(deck_id: int) -> Optional[Deck]:
    """Truy vấn thông tin chi tiết một bộ thẻ theo ID."""
    return db.session.get(Deck, deck_id)


def list_decks(
    user_id: Optional[int] = None, is_public: Optional[bool] = None
) -> List[Deck]:
    """Lấy danh sách các bộ thẻ, hỗ trợ lọc theo user_id hoặc trạng thái công khai."""
    query = Deck.query
    if user_id is not None:
        query = query.filter_by(user_id=user_id)
    if is_public is not None:
        query = query.filter_by(is_public=is_public)
    return query.order_by(Deck.created_at.desc()).all()


def update_deck(deck_id: int, data: Dict[str, Any]) -> Optional[Deck]:
    """Cập nhật thông tin một bộ thẻ."""
    deck = db.session.get(Deck, deck_id)
    if not deck:
        return None

    if "title" in data:
        deck.title = data["title"]
    if "description" in data:
        deck.description = data["description"]
    if "is_public" in data:
        deck.is_public = bool(data["is_public"])
    if "folder_id" in data:
        deck.folder_id = data["folder_id"]
    if "category_id" in data:
        deck.category_id = data["category_id"]

    deck.updated_at = datetime.utcnow()
    db.session.commit()
    return deck


def delete_deck(deck_id: int) -> bool:
    """Xóa bộ thẻ theo ID (cascade xóa các cards bên trong theo cấu hình Model)."""
    deck = db.session.get(Deck, deck_id)
    if not deck:
        return False
    db.session.delete(deck)
    db.session.commit()
    return True


# ==============================================================================
# CARD CRUD SERVICES
# ==============================================================================


def create_card(data: Dict[str, Any]) -> Card:
    """Tạo mới một flashcard và liên kết tag (nếu có)."""
    card = Card(
        question=data["question"],
        answer=data["answer"],
        explanation=data.get("explanation"),
        difficulty=data.get("difficulty", "medium"),
        deck_id=data.get("deck_id"),
        document_id=data.get("document_id"),
    )
    db.session.add(card)

    # Xử lý gán tags nếu có danh sách tag names
    tags_list = data.get("tags", [])
    for tag_name in tags_list:
        tag = get_or_create_tag(tag_name)
        card.tags.append(tag)

    db.session.commit()
    return card


def get_card_by_id(card_id: int) -> Optional[Card]:
    """Truy vấn thông tin chi tiết flashcard theo ID."""
    return db.session.get(Card, card_id)


def list_cards(
    deck_id: Optional[int] = None, document_id: Optional[int] = None
) -> List[Card]:
    """Lấy danh sách các flashcards, hỗ trợ lọc theo deck_id hoặc document_id."""
    query = Card.query
    if deck_id is not None:
        query = query.filter_by(deck_id=deck_id)
    if document_id is not None:
        query = query.filter_by(document_id=document_id)
    return query.order_by(Card.created_at.desc()).all()


def update_card(card_id: int, data: Dict[str, Any]) -> Optional[Card]:
    """Cập nhật nội dung câu hỏi, câu trả lời, giải thích hoặc tags của flashcard."""
    card = db.session.get(Card, card_id)
    if not card:
        return None

    if "question" in data:
        card.question = data["question"]
    if "answer" in data:
        card.answer = data["answer"]
    if "explanation" in data:
        card.explanation = data["explanation"]
    if "difficulty" in data:
        card.difficulty = data["difficulty"]
    if "deck_id" in data:
        card.deck_id = data["deck_id"]

    # Cập nhật tags nếu được truyền vào
    if "tags" in data and isinstance(data["tags"], list):
        card.tags.clear()
        for tag_name in data["tags"]:
            tag = get_or_create_tag(tag_name)
            card.tags.append(tag)

    card.updated_at = datetime.utcnow()
    db.session.commit()
    return card


def delete_card(card_id: int) -> bool:
    """Xóa flashcard theo ID."""
    card = db.session.get(Card, card_id)
    if not card:
        return False
    db.session.delete(card)
    db.session.commit()
    return True


# ==============================================================================
# TAG SERVICES
# ==============================================================================


def get_or_create_tag(name: str, user_id: Optional[int] = None) -> Tag:
    """Truy vấn tag đã tồn tại hoặc tạo mới nếu chưa có."""
    clean_name = name.strip()
    tag = Tag.query.filter_by(name=clean_name).first()
    if not tag:
        tag = Tag()
        tag.name = clean_name
        tag.user_id = user_id
        db.session.add(tag)
        db.session.commit()
    return tag

