"""
transcribe_routes.py — Audio transcription endpoints via Whisper STT Pipeline.
"""

from __future__ import annotations

from flask import Blueprint, jsonify, request
from app.services.ai_service import transcribe_audio_service


def transcribe_audio_endpoint():
    """
    Bóc băng giọng nói sang văn bản (POST /api/transcribe)
    ---
    tags:
      - AI Generator
    summary: Forward file audio sang Whisper STT Pipeline bóc băng thành văn bản
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: Tệp âm thanh cần bóc băng (.mp3, .wav, .m4a)
      - name: language
        in: formData
        type: string
        required: false
        default: vi
        description: Mã ngôn ngữ (mặc định vi)
    responses:
      200:
        description: Bóc băng âm thanh thành công
      400:
        description: File âm thanh không hợp lệ hoặc rỗng
      500:
        description: Lỗi tiến trình Whisper STT
    """
    if "file" not in request.files:
        return jsonify({"error": "Không tìm thấy file âm thanh trong form data"}), 400

    audio_file = request.files["file"]
    filename = audio_file.filename or "audio.wav"
    language = request.form.get("language", "vi")

    file_bytes = audio_file.read()
    if not file_bytes:
        return jsonify({"error": "File âm thanh rỗng (0 bytes)"}), 400

    try:
        result = transcribe_audio_service(
            file_bytes=file_bytes,
            filename=filename,
            language=language,
        )
        return jsonify(result), 200
    except Exception as exc:
        return jsonify({"error": f"Lỗi bóc băng âm thanh: {str(exc)}"}), 500


def register_transcribe_routes(bp: Blueprint) -> None:
    bp.add_url_rule(
        "/transcribe", view_func=transcribe_audio_endpoint, methods=["POST"]
    )
