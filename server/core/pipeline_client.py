import httpx
from server.core.config import PIPELINE_SERVICE_URL, logger


def call_pipeline_inference(file_bytes: bytes, filename: str) -> dict:
    """Forward image upload to AI Pipeline Microservice (Port 3100)."""
    try:
        with httpx.Client(timeout=45.0) as client:
            files = {"file": (filename, file_bytes, "image/jpeg")}
            url = f"{PIPELINE_SERVICE_URL}/internal/v1/process"
            resp = client.post(url, files=files)
            if resp.status_code == 200:
                return resp.json()
            raise RuntimeError(f"Pipeline error HTTP {resp.status_code}: {resp.text}")
    except httpx.RequestError as ex:
        raise ConnectionError(f"Cannot reach AI Pipeline Service: {str(ex)}")


def call_pipeline_tts(text_content: str) -> str:
    """Invoke pipeline TTS endpoint non-blockingly or return empty string on failure."""
    try:
        with httpx.Client(timeout=30.0) as client:
            url = f"{PIPELINE_SERVICE_URL}/internal/v1/tts/synthesize"
            resp = client.post(url, json={"text": text_content})
            if resp.status_code == 200:
                return resp.json().get("audio_url", "")
            return ""
    except Exception as ex:
        logger.warning(f"Pipeline TTS invocation failed: {str(ex)}")
        return ""

