#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scripts/run_e2e_stack.py

Orchestrator quản lý vòng đời ứng dụng EduFlash AI toàn trình qua 3 tầng:
  Client (Port 5000) -> Server (Port 3000) -> AI Pipeline (Port 8000)

Thực hiện:
1. Sequential Startup:
   - Khởi động Backend Server (Port 3000) & chờ socket/HTTP ready.
   - Khởi động AI Pipeline (Port 8000) & polling healthcheck /api/pi/health.
   - Khởi động NiceGUI Client (Port 5000) & chờ tín hiệu ready.
2. Graceful Teardown:
   - Lắng nghe Ctrl+C / SIGINT / SIGTERM.
   - Thu dọn sạch sẽ cây tiến trình (process tree) và giải phóng triệt để các cổng 3000, 8000, 5000.
"""

from __future__ import annotations

import atexit
import os
import re
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.request import Request, urlopen

# Thiết lập bảng màu ANSI cho log đa tiến trình
CLR_RESET = "\033[0m"
CLR_CYAN = "\033[36m"
CLR_MAGENTA = "\033[35m"
CLR_GREEN = "\033[32m"
CLR_YELLOW = "\033[33m"
CLR_RED = "\033[31m"
CLR_BOLD = "\033[1m"

ROOT_DIR = Path(__file__).resolve().parent.parent

SERVER_PORT = int(os.getenv("PORT", 3000))
PIPELINE_PORT = int(os.getenv("PIPELINE_PORT", 8000))
CLIENT_PORT = int(os.getenv("CLIENT_PORT", 5000))

# Quản lý danh sách tiến trình con
_managed_processes: List[subprocess.Popen] = []
_is_shutting_down = False


def log(prefix: str, msg: str, color: str = CLR_RESET) -> None:
    """In log có màu sắc định dạng chuẩn theo từng service."""
    timestamp = time.strftime("%H:%M:%S")
    sys.stdout.write(f"{color}[{timestamp}][{prefix}]{CLR_RESET} {msg}\n")
    sys.stdout.flush()


def resolve_python(service_name: str) -> str:
    """Tìm python executable trong .venv của service hoặc root .venv."""
    is_win = sys.platform == "win32"
    service_venv = (
        ROOT_DIR / service_name / ".venv" / "Scripts" / "python.exe"
        if is_win
        else ROOT_DIR / service_name / ".venv" / "bin" / "python"
    )
    if service_venv.exists():
        return str(service_venv)

    root_venv = (
        ROOT_DIR / ".venv" / "Scripts" / "python.exe"
        if is_win
        else ROOT_DIR / ".venv" / "bin" / "python"
    )
    if root_venv.exists():
        return str(root_venv)

    return sys.executable


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Kiểm tra xem port có đang bị chiếm dụng hay không."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.6)
        return s.connect_ex((host, port)) == 0


def kill_processes_on_ports(ports: List[int]) -> None:
    """Giải phóng cưỡng chế các cổng bị treo zombie hoặc tiến trình chạy ngầm sót lại."""
    is_win = sys.platform == "win32"
    for port in ports:
        if not is_port_in_use(port):
            continue
        log(
            "PORT-CLEANER",
            f"Phát hiện cổng {port} đang bị chiếm dụng. Đang giải phóng...",
            CLR_YELLOW,
        )
        if is_win:
            try:
                cmd = f"netstat -ano -p tcp | findstr :{port}"
                out = subprocess.check_output(
                    cmd, shell=True, text=True, stderr=subprocess.DEVNULL
                )
                for line in out.strip().splitlines():
                    if "LISTENING" in line:
                        parts = re.split(r"\s+", line.strip())
                        if len(parts) >= 5:
                            pid = parts[-1]
                            if pid and pid != "0" and pid != str(os.getpid()):
                                subprocess.run(
                                    ["taskkill", "/F", "/PID", pid],
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL,
                                )
                                log(
                                    "PORT-CLEANER",
                                    f"Đã giải phóng PID {pid} trên cổng {port}",
                                    CLR_YELLOW,
                                )
            except Exception:
                pass
        else:
            try:
                subprocess.run(
                    f"lsof -ti :{port} | xargs -r kill -9",
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass


def stream_logs(proc: subprocess.Popen, prefix: str, color: str) -> None:
    """Đọc và chuyển tiếp log stream từ stdout/stderr của tiến trình con theo thời gian thực."""

    def _reader(pipe):
        try:
            for line in iter(pipe.readline, ""):
                if not line:
                    break
                clean_line = line.rstrip()
                if clean_line:
                    sys.stdout.write(f"{color}[{prefix}]{CLR_RESET} {clean_line}\n")
                    sys.stdout.flush()
        except Exception:
            pass
        finally:
            try:
                pipe.close()
            except Exception:
                pass

    if proc.stdout:
        threading.Thread(target=_reader, args=(proc.stdout,), daemon=True).start()
    if proc.stderr:
        threading.Thread(target=_reader, args=(proc.stderr,), daemon=True).start()


def spawn_service(
    name: str,
    py_executable: str,
    script_rel_path: str,
    extra_env: Dict[str, str],
    color: str,
) -> subprocess.Popen:
    """Khởi động một service dưới dạng tiến trình con với biến môi trường tùy biến."""
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env.update(extra_env)

    script_path = str(ROOT_DIR / script_rel_path)
    proc = subprocess.Popen(
        [py_executable, script_path],
        cwd=str(ROOT_DIR),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    _managed_processes.append(proc)
    stream_logs(proc, name, color)
    return proc


def wait_for_http(
    url: str,
    timeout_sec: float = 30.0,
    interval_sec: float = 0.5,
    expected_status: int = 200,
) -> bool:
    """Thực hiện HTTP polling cho đến khi endpoint trả về status code kỳ vọng."""
    start = time.time()
    while time.time() - start < timeout_sec:
        try:
            req = Request(url, headers={"User-Agent": "E2E-Orchestrator"})
            with urlopen(req, timeout=1.5) as res:
                if res.status == expected_status:
                    return True
        except Exception:
            pass
        time.sleep(interval_sec)
    return False


def wait_for_socket(
    port: int, host: str = "127.0.0.1", timeout_sec: float = 25.0
) -> bool:
    """Polling TCP socket cho đến khi cổng chấp nhận kết nối."""
    start = time.time()
    while time.time() - start < timeout_sec:
        if is_port_in_use(port, host=host):
            return True
        time.sleep(0.4)
    return False


def teardown_all() -> None:
    """Dọn dẹp sạch sẽ toàn bộ 3 tầng tiến trình và giải phóng các cổng."""
    global _is_shutting_down
    if _is_shutting_down:
        return
    _is_shutting_down = True

    log(
        "ORCHESTRATOR",
        "Đang dừng toàn bộ 3 tầng tiến trình (Graceful Teardown)...",
        CLR_BOLD + CLR_YELLOW,
    )

    for proc in _managed_processes:
        if proc.poll() is None:
            if sys.platform == "win32":
                try:
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                except Exception:
                    pass
            else:
                try:
                    proc.terminate()
                except Exception:
                    pass

    # Đảm bảo giải phóng sạch sẽ 3 cổng 3000, 8000, 5000
    time.sleep(0.5)
    kill_processes_on_ports([SERVER_PORT, PIPELINE_PORT, CLIENT_PORT])
    log(
        "ORCHESTRATOR",
        f"Đã giải phóng sạch sẽ cả 3 cổng ({SERVER_PORT}, {PIPELINE_PORT}, {CLIENT_PORT}).",
        CLR_BOLD + CLR_GREEN,
    )


def _signal_handler(signum, frame):
    log("ORCHESTRATOR", f"Nhận tín hiệu dừng (Signal {signum}) / Ctrl+C.", CLR_RED)
    teardown_all()
    sys.exit(0)


def run_orchestration() -> None:
    """Thực thi luồng điều phối Sequential Startup toàn trình."""
    # Đăng ký handler bắt tín hiệu dừng
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)
    atexit.register(teardown_all)

    # Dọn dẹp cổng trước khi bắt đầu
    kill_processes_on_ports([SERVER_PORT, PIPELINE_PORT, CLIENT_PORT])

    server_py = resolve_python("server")
    pipeline_py = resolve_python("pipeline")
    client_py = resolve_python("client")

    print("\n" + "=" * 65)
    print(f"{CLR_BOLD}  EDUFLASH AI - E2E FULL-STACK ORCHESTRATION RUNNER{CLR_RESET}")
    print("=" * 65)
    print(f"  Backend Server:  http://127.0.0.1:{SERVER_PORT}  [{server_py}]")
    print(f"  AI Pipeline:     http://127.0.0.1:{PIPELINE_PORT}  [{pipeline_py}]")
    print(f"  Frontend Client: http://127.0.0.1:{CLIENT_PORT}  [{client_py}]")
    print("=" * 65 + "\n")

    # -----------------------------------------------------------------------
    # BƯỚC 1: KÍCH HOẠT BACKEND SERVER (PORT 3000)
    # -----------------------------------------------------------------------
    log(
        "STEP-1",
        f"Khởi động Backend Server tại http://127.0.0.1:{SERVER_PORT}...",
        CLR_CYAN,
    )
    server_proc = spawn_service(
        name="SERVER",
        py_executable=server_py,
        script_rel_path="server/app/main.py",
        extra_env={
            "PORT": str(SERVER_PORT),
            "AI_PIPELINE_URL": f"http://127.0.0.1:{PIPELINE_PORT}/api",
            "PYTHONPATH": os.pathsep.join(
                filter(
                    None,
                    [
                        str(ROOT_DIR / "server"),
                        str(ROOT_DIR),
                        os.getenv("PYTHONPATH", ""),
                    ],
                )
            ),
        },
        color=CLR_CYAN,
    )

    if not wait_for_socket(SERVER_PORT, timeout_sec=25.0):
        log(
            "ERROR",
            f"Backend Server không phản hồi sau 25s trên cổng {SERVER_PORT}.",
            CLR_RED,
        )
        teardown_all()
        sys.exit(1)
    log("STEP-1", f"Backend Server đã mở cổng {SERVER_PORT} thành công!", CLR_GREEN)

    # -----------------------------------------------------------------------
    # BƯỚC 2: KÍCH HOẠT AI PIPELINE (PORT 8000) & HEALTHCHECK
    # -----------------------------------------------------------------------
    pipeline_health_url = f"http://127.0.0.1:{PIPELINE_PORT}/api/pi/health"
    log(
        "STEP-2",
        f"Khởi động AI Pipeline và polling Healthcheck ({pipeline_health_url})...",
        CLR_MAGENTA,
    )

    pipeline_proc = spawn_service(
        name="PIPELINE",
        py_executable=pipeline_py,
        script_rel_path="pipeline/main.py",
        extra_env={
            "PORT": str(PIPELINE_PORT),
            "PYTHONPATH": os.pathsep.join(
                filter(
                    None,
                    [
                        str(ROOT_DIR / "pipeline"),
                        str(ROOT_DIR),
                        os.getenv("PYTHONPATH", ""),
                    ],
                )
            ),
        },
        color=CLR_MAGENTA,
    )

    is_healthy = wait_for_http(
        url=pipeline_health_url,
        timeout_sec=40.0,
        expected_status=200,
    )
    if not is_healthy:
        # Fallback thử endpoint /api/health
        is_healthy = wait_for_http(
            url=f"http://127.0.0.1:{PIPELINE_PORT}/api/health",
            timeout_sec=5.0,
            expected_status=200,
        )

    if not is_healthy:
        log(
            "ERROR",
            f"AI Pipeline Polling Healthcheck thất bại sau 45s tại {pipeline_health_url}.",
            CLR_RED,
        )
        teardown_all()
        sys.exit(1)
    log(
        "STEP-2",
        f"AI Pipeline Healthcheck đạt chuẩn (HTTP 200 OK) tại {pipeline_health_url}!",
        CLR_GREEN,
    )

    # -----------------------------------------------------------------------
    # BƯỚC 3: KHỞI CHẠY NICEGUI CLIENT (PORT 5000)
    # -----------------------------------------------------------------------
    log(
        "STEP-3",
        f"Khởi chạy NiceGUI Client tại http://127.0.0.1:{CLIENT_PORT}...",
        CLR_GREEN,
    )
    client_proc = spawn_service(
        name="CLIENT",
        py_executable=client_py,
        script_rel_path="client/main.py",
        extra_env={
            "PORT": str(CLIENT_PORT),
            "BACKEND_API_URL": f"http://127.0.0.1:{SERVER_PORT}/api",
            "PYTHONPATH": os.pathsep.join(
                filter(
                    None,
                    [
                        str(ROOT_DIR / "client"),
                        str(ROOT_DIR),
                        os.getenv("PYTHONPATH", ""),
                    ],
                )
            ),
        },
        color=CLR_GREEN,
    )

    if not wait_for_socket(CLIENT_PORT, timeout_sec=25.0):
        log("ERROR", f"NiceGUI Client không phản hồi trên cổng {CLIENT_PORT}.", CLR_RED)
        teardown_all()
        sys.exit(1)

    print("\n" + "=" * 65)
    log(
        "SUCCESS",
        f"{CLR_BOLD}HỆ THỐNG TOÀN TRÌNH 3 TẦNG ĐÃ SẴN SÀNG!{CLR_RESET}",
        CLR_GREEN,
    )
    print(
        f"  👉 Truy cập ứng dụng: {CLR_BOLD}http://127.0.0.1:{CLIENT_PORT}{CLR_RESET}"
    )
    print(f"  👉 Backend Swagger:   http://127.0.0.1:{SERVER_PORT}/docs/")
    print(f"  👉 Pipeline Swagger:  http://127.0.0.1:{PIPELINE_PORT}/docs")
    print(f"  [Bấm Ctrl+C bất cứ lúc nào để dừng và giải phóng 3 cổng sạch sẽ]")
    print("=" * 65 + "\n")

    # Giữ tiến trình điều phối lắng nghe vòng đời
    try:
        while True:
            for p, name in [
                (server_proc, "Backend Server"),
                (pipeline_proc, "AI Pipeline"),
                (client_proc, "Frontend Client"),
            ]:
                if p.poll() is not None:
                    log(
                        "WARNING",
                        f"Tiến trình {name} đã thoát với mã code {p.returncode}. Bắt đầu teardown...",
                        CLR_YELLOW,
                    )
                    teardown_all()
                    return
            time.sleep(1.0)
    except KeyboardInterrupt:
        teardown_all()


if __name__ == "__main__":
    run_orchestration()
