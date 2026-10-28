"""
cards.py — Flashcards & Tags Junction API endpoints (Tag: Cards & Tags).
Orchestrator for modular route handlers in app.api.cards_routes.
"""

from __future__ import annotations

from flask import Blueprint
from app.api.cards_routes.crud_routes import (
    create_new_card,
    delete_all_cards_endpoint,
    delete_card_endpoint,
    get_all_cards,
    get_card_detail,
    register_crud_routes,
    update_card_detail,
)
from app.api.cards_routes.batch_routes import (
    create_cards_batch,
    register_batch_routes,
)
from app.api.cards_routes.tag_routes import (
    attach_tag_to_card,
    detach_tag_from_card,
    register_tag_routes,
)
from app.api.cards_routes.generator_routes import (
    generate_cards_from_doc_backward_compat,
    register_generator_routes,
)

cards_bp = Blueprint("cards", __name__, url_prefix="/api/cards")

# Register all modular route handlers on cards_bp
register_crud_routes(cards_bp)
register_batch_routes(cards_bp)
register_tag_routes(cards_bp)
register_generator_routes(cards_bp)

__all__ = [
    "cards_bp",
    "get_all_cards",
    "create_new_card",
    "get_card_detail",
    "update_card_detail",
    "delete_card_endpoint",
    "delete_all_cards_endpoint",
    "create_cards_batch",
    "attach_tag_to_card",
    "detach_tag_from_card",
    "generate_cards_from_doc_backward_compat",
]
