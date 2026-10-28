"""
ai_gateway_routes package — Modular route handlers for AI Generation and STT.
"""

from __future__ import annotations

from app.api.ai_gateway_routes.generation_routes import (
    generate_from_document_endpoint,
    generate_from_raw_text,
    register_generation_routes,
)
from app.api.ai_gateway_routes.transcribe_routes import (
    register_transcribe_routes,
    transcribe_audio_endpoint,
)

__all__ = [
    "generate_from_raw_text",
    "generate_from_document_endpoint",
    "register_generation_routes",
    "transcribe_audio_endpoint",
    "register_transcribe_routes",
]
