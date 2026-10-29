"""
api_cards.py — CARDS, TAGS & AI GENERATOR API Client Services.
Orchestrator for modular sub-services in services.cards.
"""

from __future__ import annotations

from services.cards.cards_service import (
    create_card,
    create_cards_batch,
    delete_all_cards,
    delete_card,
    get_card_by_id,
    get_cards,
    update_card,
    update_card_notes,
)
from services.cards.tags_service import (
    add_card_tag,
    create_tag,
    delete_tag,
    get_card_tags,
    get_tag_by_id,
    get_tags,
    get_tags_for_card,
    remove_card_tag,
    update_tag,
)
from services.cards.ai_service import (
    generate_cards,
    generate_flashcards,
    transcribe_audio,
)

__all__ = [
    "get_cards",
    "get_card_by_id",
    "create_card",
    "create_cards_batch",
    "update_card",
    "update_card_notes",
    "delete_card",
    "delete_all_cards",
    "get_tags",
    "get_tag_by_id",
    "create_tag",
    "update_tag",
    "delete_tag",
    "get_card_tags",
    "add_card_tag",
    "remove_card_tag",
    "get_tags_for_card",
    "generate_cards",
    "transcribe_audio",
    "generate_flashcards",
]
