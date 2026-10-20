import os
import httpx
from dotenv import load_dotenv

load_dotenv()
SERVER_URL = os.getenv("FLASK_API_URL", "http://127.0.0.1:8000/api")


def generate_flashcards(text: str):
    try:
        with httpx.Client(base_url=SERVER_URL, timeout=30.0) as client:
            res = client.post("/generate", json={"text": text})
            res.raise_for_status()
            return res.json().get("cards", [])
    except Exception:
        return []
