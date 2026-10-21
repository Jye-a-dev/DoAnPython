import os
from typing import Any, Dict, List, Optional
import httpx
from dotenv import load_dotenv

load_dotenv()
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:3000/api").rstrip("/")


def generate_flashcards(
    text: str, deck_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Gửi yêu cầu sinh flashcard tới Backend Server (Port 3000)."""
    payload: Dict[str, Any] = {"text": text}
    if deck_id is not None:
        payload["deck_id"] = deck_id

    try:
        with httpx.Client(base_url=BACKEND_API_URL, timeout=60.0) as client:
            res = client.post("/generate", json=payload)
            res.raise_for_status()
            data = res.json()
            return data.get("cards", data if isinstance(data, list) else [])
    except Exception:
        return []


def transcribe_audio(file_bytes: bytes, filename: str = "audio.wav") -> Dict[str, Any]:
    """Gửi file âm thanh tới Backend Server để bóc băng (Speech-to-Text)."""
    try:
        files = {"file": (filename, file_bytes, "application/octet-stream")}
        with httpx.Client(base_url=BACKEND_API_URL, timeout=120.0) as client:
            res = client.post("/transcribe", files=files)
            res.raise_for_status()
            return res.json()
    except Exception as exc:
        return {"error": str(exc)}
