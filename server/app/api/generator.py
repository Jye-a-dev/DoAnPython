"""
generator.py — Backward compatibility wrapper for ai_gateway.py.
"""

from __future__ import annotations

from app.api.ai_gateway import (
    ai_gateway_bp,
    generate_from_document_endpoint,
    generate_from_raw_text,
    generator_bp,
    transcribe_audio_endpoint,
)

__all__ = [
    "ai_gateway_bp",
    "generator_bp",
    "generate_from_document_endpoint",
    "generate_from_raw_text",
    "transcribe_audio_endpoint",
]
