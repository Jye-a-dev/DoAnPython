import json
import os
from typing import Any, Dict, List
from pathlib import Path
from dotenv import load_dotenv
import httpx
import reflex as rx

CLIENT_DIR = Path(__file__).resolve().parent
load_dotenv(CLIENT_DIR / ".env")
load_dotenv()

FASTAPI_BASE_URL = os.getenv("SERVER_URL", os.getenv("FASTAPI_BASE_URL", "http://localhost:3000"))


class DetectorState(rx.State):
    """Reflex application reactive state for managing uploads, API coordination, and media streaming."""

    is_processing: bool = False
    uploaded_image_url: str = ""
    audio_url: str = ""
    summary_text: str = ""
    json_output: str = ""
    error_message: str = ""
    history: List[Dict[str, Any]] = []

    async def handle_upload(self, files: List[rx.UploadFile]) -> None:
        """Processes multipart uploaded files and transmits to FastAPI detection endpoint."""
        if not files:
            self.error_message = "Vui lòng chọn hoặc kéo thả một file ảnh trước khi phân tích."
            return

        self.is_processing = True
        self.error_message = ""
        file = files[0]

        try:
            # Asynchronously read file stream bytes per Reflex v0.6+ standard
            file_bytes = await file.read()
            filename = getattr(file, "name", "upload.jpg") or "upload.jpg"
            content_type = getattr(file, "content_type", "image/jpeg") or "image/jpeg"

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{FASTAPI_BASE_URL}/api/v1/detect",
                    files={"image": (filename, file_bytes, content_type)}
                )

                if response.status_code == 200:
                    data = response.json()
                    self.summary_text = data.get("summary", "")

                    raw_img_url = data.get("image_url", "")
                    if raw_img_url.startswith("/"):
                        self.uploaded_image_url = f"{FASTAPI_BASE_URL}{raw_img_url}"
                    else:
                        self.uploaded_image_url = raw_img_url

                    raw_audio_url = data.get("audio_url", "")
                    if raw_audio_url and raw_audio_url.startswith("/"):
                        self.audio_url = f"{FASTAPI_BASE_URL}{raw_audio_url}"
                    else:
                        self.audio_url = raw_audio_url or ""

                    self.json_output = json.dumps(data, indent=2, ensure_ascii=False)
                    self.error_message = ""
                else:
                    self.error_message = f"Lỗi từ máy chủ ({response.status_code}): {response.text}"
        except Exception as exc:
            self.error_message = f"Không thể kết nối đến AI Pipeline Engine: {str(exc)}"
        finally:
            self.is_processing = False
            await self.fetch_history()

    async def fetch_history(self) -> None:
        """Retrieves recent 10 detection entries from backend SQLite store."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{FASTAPI_BASE_URL}/api/v1/history?limit=10")
                if response.status_code == 200:
                    records = response.json().get("records", [])
                    for record in records:
                        img = record.get("image_url", "")
                        if img.startswith("/"):
                            record["image_url"] = f"{FASTAPI_BASE_URL}{img}"
                        aud = record.get("audio_url", "")
                        if aud.startswith("/"):
                            record["audio_url"] = f"{FASTAPI_BASE_URL}{aud}"
                    self.history = records
        except Exception:
            pass

    def select_history_item(self, item: Dict[str, Any]) -> None:
        """Loads a historical detection into the active inspection view."""
        self.uploaded_image_url = item.get("image_url", "")
        self.audio_url = item.get("audio_url", "")
        self.summary_text = item.get("summary", "")
        raw_json = item.get("json_data", {})
        self.json_output = json.dumps(raw_json, indent=2, ensure_ascii=False)
        self.error_message = ""

    def clear_state(self) -> None:
        """Resets active inspection variables."""
        self.uploaded_image_url = ""
        self.audio_url = ""
        self.summary_text = ""
        self.json_output = ""
        self.error_message = ""

