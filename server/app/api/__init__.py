from app.api.documents import documents_bp
from app.api.generator import generator_bp
from app.api.decks import decks_bp
from app.api.cards import cards_bp
from app.api.study import study_bp
from app.api.system import system_bp

__all__ = [
    "documents_bp",
    "generator_bp",
    "decks_bp",
    "cards_bp",
    "study_bp",
    "system_bp",
]

