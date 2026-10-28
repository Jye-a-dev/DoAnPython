"""
ai_gateway.py — AI Pipeline Gateway endpoints (Tag: AI Generator).
Orchestrator for modular route handlers in app.api.ai_gateway_routes.
"""

from __future__ import annotations

from flask import Blueprint
from app.api.ai_gateway_routes.generation_routes import (
    generate_from_document_endpoint,
    generate_from_raw_text,
    register_generation_routes,
)
from app.api.ai_gateway_routes.transcribe_routes import (
    register_transcribe_routes,
    transcribe_audio_endpoint,
)

ai_gateway_bp = Blueprint("ai_gateway", __name__, url_prefix="/api")

# Register all modular route handlers on ai_gateway_bp
register_generation_routes(ai_gateway_bp)
register_transcribe_routes(ai_gateway_bp)

# Alias for backward compatibility
generator_bp = ai_gateway_bp

__all__ = [
    "ai_gateway_bp",
    "generator_bp",
    "generate_from_raw_text",
    "generate_from_document_endpoint",
    "transcribe_audio_endpoint",
]
