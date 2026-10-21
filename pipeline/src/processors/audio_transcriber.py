"""
audio_transcriber.py — Speech-to-Text inference processor using Whisper (offline).
Handles audio byte streams (io.BytesIO or raw bytes) and executes transcription.
"""

from __future__ import annotations

import io
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, BinaryIO, Optional, Union

logger = logging.getLogger(__name__)


class AudioTranscriber:
    """Speech-to-text processor using OpenAI Whisper offline models."""

    def __init__(
        self,
        model_size: str = "base",
        device: Optional[str] = None,
        download_root: Optional[str] = None,
    ) -> None:
        self.model_size = model_size
        self.download_root = download_root
        self._device = device or ("cuda" if self._has_cuda() else "cpu")
        self._model = None

    @staticmethod
    def _has_cuda() -> bool:
        try:
            import torch

            return torch.cuda.is_available()
        except ImportError:
            return False

    def load_model(self) -> None:
        """Lazy-load the Whisper model weights into target device memory."""
        if self._model is not None:
            return

        try:
            import whisper

            logger.info(
                "Loading Whisper model '%s' on %s (root: %s)...",
                self.model_size,
                self._device,
                self.download_root,
            )
            self._model = whisper.load_model(
                self.model_size,
                device=self._device,
                download_root=self.download_root,
            )
            logger.info("Whisper model '%s' loaded successfully.", self.model_size)
        except Exception as exc:
            logger.error("Failed to load Whisper model '%s': %s", self.model_size, exc)
            raise

    def is_loaded(self) -> bool:
        """Check if model weights are already loaded in memory."""
        return self._model is not None

    def get_info(self) -> dict[str, Any]:
        """Return metadata regarding the model configuration and runtime state."""
        return {
            "loaded": self.is_loaded(),
            "model_size": self.model_size,
            "device": self._device,
            "download_root": self.download_root,
        }

    def transcribe(
        self,
        audio_data: Union[bytes, io.BytesIO, BinaryIO],
        filename: Optional[str] = None,
        language: Optional[str] = "vi",
    ) -> dict[str, Any]:
        """
        Transcribe raw audio bytes to text.

        Args:
            audio_data: In-memory byte array or BytesIO stream.
            filename: Original filename to preserve audio format suffix for ffmpeg.
            language: Target language code (e.g. 'vi', 'en').

        Returns:
            Dict containing transcription text, detected language, and duration.
        """
        if not self.is_loaded():
            self.load_model()

        if isinstance(audio_data, io.BytesIO):
            raw_bytes = audio_data.getvalue()
        elif isinstance(audio_data, bytes):
            raw_bytes = audio_data
        elif hasattr(audio_data, "read"):
            raw_bytes = audio_data.read()
        else:
            raise ValueError("Unsupported audio data container. Expected bytes or io.BytesIO.")

        if not raw_bytes:
            raise ValueError("Audio byte stream is empty (0 bytes).")

        suffix = ".wav"
        if filename and "." in filename:
            ext = Path(filename).suffix.lower()
            if ext in {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac"}:
                suffix = ext

        # Transient disk write required for ffmpeg pipeline decoding in Whisper
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        temp_path = temp_file.name

        try:
            temp_file.write(raw_bytes)
            temp_file.flush()
            temp_file.close()

            options: dict[str, Any] = {
                "fp16": (self._device != "cpu"),
            }
            if language:
                options["language"] = language

            assert self._model is not None
            result = self._model.transcribe(temp_path, **options)

            transcribed_text = result.get("text", "").strip()
            detected_lang = result.get("language", language or "vi")

            duration_seconds = 0.0
            segments = result.get("segments", [])
            if segments:
                duration_seconds = round(float(segments[-1].get("end", 0.0)), 2)

            return {
                "text": transcribed_text,
                "language": detected_lang,
                "duration_seconds": duration_seconds,
            }
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

