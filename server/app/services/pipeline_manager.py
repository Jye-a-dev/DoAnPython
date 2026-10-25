from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional
from urllib.error import URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_PIPELINE_DIR = _PROJECT_ROOT / "pipeline"

_pipeline_process: Optional[subprocess.Popen] = None


def resolve_pipeline_python() -> str:
    """Xác định đường dẫn Python trong virtualenv của pipeline."""
    is_win = sys.platform == "win32"
    venv_py = (
        _PIPELINE_DIR / ".venv" / "Scripts" / "python.exe"
        if is_win
        else _PIPELINE_DIR / ".venv" / "bin" / "python"
    )
    if venv_py.exists():
        return str(venv_py)

    root_venv_py = (
        _PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
        if is_win
        else _PROJECT_ROOT / ".venv" / "bin" / "python"
    )
    if root_venv_py.exists():
        return str(root_venv_py)

    return sys.executable


def is_pipeline_healthy(
    url: str = "http://127.0.0.1:8000/api/pi/health", timeout: float = 2.0
) -> bool:
    """Gửi GET request kiểm tra phản hồi HTTP 200 từ AI Pipeline Healthcheck."""
    candidate_urls = [
        url,
        url.replace("/pi/health", "/health"),
    ]
    for target in candidate_urls:
        try:
            req = Request(
                target,
                headers={"User-Agent": "PipelineManager-HealthCheck"},
                method="GET",
            )
            with urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            continue
    return False


def poll_pipeline_health(
    url: str = "http://127.0.0.1:8000/api/pi/health",
    timeout: float = 40.0,
    interval: float = 0.5,
) -> bool:
    """Polling liên tục cho đến khi AI Pipeline sẵn sàng hoặc hết thời gian timeout."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_pipeline_healthy(url=url, timeout=1.5):
            return True
        time.sleep(interval)
    return False


def start_pipeline(
    port: int = 8000,
    wait_ready: bool = True,
    timeout: float = 40.0,
) -> Optional[subprocess.Popen]:
    """Khởi động tiến trình AI Pipeline độc lập tại Port 8000 và chờ hoàn tất Healthcheck."""
    global _pipeline_process

    if is_pipeline_healthy(f"http://127.0.0.1:{port}/api/pi/health", timeout=1.0):
        logger.info("AI Pipeline đã đang chạy và phản hồi tốt tại port %s.", port)
        return _pipeline_process

    py_exe = resolve_pipeline_python()
    main_script = str(_PIPELINE_DIR / "main.py")

    env = os.environ.copy()
    env["PORT"] = str(port)
    env["PYTHONUNBUFFERED"] = "1"

    logger.info(
        "Đang kích hoạt AI Pipeline qua pipeline_manager (Port %s): %s %s",
        port,
        py_exe,
        main_script,
    )

    _pipeline_process = subprocess.Popen(
        [py_exe, main_script],
        cwd=str(_PROJECT_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if wait_ready:
        healthy = poll_pipeline_health(
            url=f"http://127.0.0.1:{port}/api/pi/health",
            timeout=timeout,
        )
        if not healthy:
            logger.warning(
                "AI Pipeline chưa phản hồi kịp sau %ss, tiến trình vẫn đang chạy ngầm (PID %s).",
                timeout,
                _pipeline_process.pid,
            )
        else:
            logger.info("AI Pipeline đã hoàn tất Healthcheck (/api/pi/health).")

    return _pipeline_process


def stop_pipeline() -> None:
    """Dừng tiến trình AI Pipeline an toàn."""
    global _pipeline_process
    if _pipeline_process is not None:
        try:
            if sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(_pipeline_process.pid)],
                    capture_output=True,
                )
            else:
                _pipeline_process.terminate()
                _pipeline_process.wait(timeout=3)
        except Exception as exc:
            logger.warning(
                "Lỗi dừng AI Pipeline (PID %s): %s", _pipeline_process.pid, exc
            )
        finally:
            _pipeline_process = None
