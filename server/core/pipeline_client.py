import atexit
import httpx
from server.core.config import PIPELINE_SERVICE_URL, logger


class PipelineServiceError(Exception):
    """Base exception for AI Pipeline microservice communication."""
    pass


class PipelineUnavailableError(PipelineServiceError):
    """Raised when the AI Pipeline microservice cannot be reached (HTTP 503)."""
    pass


class PipelineExecutionError(PipelineServiceError):
    """Raised when the AI Pipeline encounters processing or unprocessable data errors (HTTP 422)."""
    pass


class PipelineTimeoutError(PipelineServiceError):
    """Raised when the AI Pipeline communication times out (HTTP 504)."""
    pass


# Module-level singleton client for connection pooling & Keep-Alive socket reuse
http_client = httpx.Client(
    timeout=httpx.Timeout(15.0, connect=3.0),
    limits=httpx.Limits(max_keepalive_connections=20, max_connections=50)
)
atexit.register(http_client.close)


def call_pipeline_inference(file_bytes: bytes, filename: str) -> dict:
    """Forward image upload to AI Pipeline Microservice (Port 3100)."""
    files = {"file": (filename, file_bytes, "image/jpeg")}
    url = f"{PIPELINE_SERVICE_URL}/internal/v1/process"
    try:
        resp = http_client.post(url, files=files)
        if resp.status_code == 200:
            return resp.json()
        if resp.status_code in (400, 422):
            raise PipelineExecutionError(f"Pipeline rejected payload (HTTP {resp.status_code}): {resp.text}")
        if resp.status_code in (502, 503):
            raise PipelineUnavailableError(f"Pipeline unavailable (HTTP {resp.status_code}): {resp.text}")
        raise PipelineExecutionError(f"Pipeline returned unexpected status {resp.status_code}: {resp.text}")
    except httpx.TimeoutException as ex:
        raise PipelineTimeoutError(f"Pipeline inference request timed out: {str(ex)}") from ex
    except (httpx.NetworkError, httpx.ConnectError) as ex:
        raise PipelineUnavailableError(f"Cannot reach AI Pipeline Service: {str(ex)}") from ex
    except httpx.RequestError as ex:
        raise PipelineUnavailableError(f"Pipeline request error: {str(ex)}") from ex


def call_pipeline_tts(text_content: str) -> str:
    """Invoke pipeline TTS endpoint non-blockingly or return empty string on failure."""
    url = f"{PIPELINE_SERVICE_URL}/internal/v1/tts/synthesize"
    try:
        resp = http_client.post(url, json={"text": text_content}, timeout=10.0)
        if resp.status_code == 200:
            return resp.json().get("audio_url", "")
        logger.warning(f"Pipeline TTS failed with HTTP {resp.status_code}: {resp.text}")
        return ""
    except Exception as ex:
        logger.warning(f"Pipeline TTS invocation failed: {str(ex)}")
        return ""


