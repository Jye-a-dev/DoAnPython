#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scripts/run_e2e_stack.py

Orchestrator quản lý vòng đời ứng dụng EduFlash AI toàn trình qua 3 tầng:
  Client (Port 5000) -> Server (Port 3000) -> AI Pipeline (Port 8000)
"""

from __future__ import annotations

import atexit
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import List

# Import modular helper utilities
try:
    from .e2e_utils import (
        CLR_BOLD,
        CLR_CYAN,
        CLR_GREEN,
        CLR_MAGENTA,
        CLR_RED,
        CLR_RESET,
        CLR_YELLOW,
        is_port_in_use,
        kill_processes_on_ports,
        log,
        resolve_python,
        spawn_service,
        wait_for_http,
        wait_for_socket,
    )
except ImportError:
    from e2e_utils import (
        CLR_BOLD,
        CLR_CYAN,
        CLR_GREEN,
        CLR_MAGENTA,
        CLR_RED,
        CLR_RESET,
        CLR_YELLOW,
        is_port_in_use,
        kill_processes_on_ports,
        log,
        resolve_python,
        spawn_service,
        wait_for_http,
        wait_for_socket,
    )

ROOT_DIR = Path(__file__).resolve().parents[2]

SERVER_PORT = int(os.getenv("PORT", 3000))
PIPELINE_PORT = int(os.getenv("PIPELINE_PORT", 8000))
CLIENT_PORT = int(os.getenv("CLIENT_PORT", 5000))

# Quản lý danh sách tiến trình con
_managed_processes: List[subprocess.Popen] = []
_is_shutting_down = False


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


def run_orchestration() -> None:
    """Điều phối toàn bộ quy trình khởi động tuần tự và giám sát sức khỏe 3 tầng."""
    # Đăng ký signal handlers để dọn dẹp tiến trình khi tắt
    atexit.register(teardown_all)
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit(0))

    print("\n" + "=" * 65)
    log(
        "ORCHESTRATOR",
        f"{CLR_BOLD}KHỞI ĐỘNG HỆ THỐNG TOÀN TRÌNH EDUFLASH AI (3 TẦNG){CLR_RESET}",
        CLR_CYAN,
    )
    print("=" * 65)

    # Giải phóng trước các cổng nếu đang bị chiếm dụng
    kill_processes_on_ports([SERVER_PORT, PIPELINE_PORT, CLIENT_PORT])

    # Xác định python executable cho từng service
    server_py = resolve_python(ROOT_DIR, "server")
    pipeline_py = resolve_python(ROOT_DIR, "pipeline")
    client_py = resolve_python(ROOT_DIR, "client")

    log("CONFIG", f"Root Dir:     {ROOT_DIR}")
    log("CONFIG", f"Server Py:   {server_py}")
    log("CONFIG", f"Pipeline Py: {pipeline_py}")
    log("CONFIG", f"Client Py:   {client_py}")

    # -----------------------------------------------------------------------
    # BƯỚC 1: KHỞI CHẠY BACKEND SERVER (PORT 3000)
    # -----------------------------------------------------------------------
    log(
        "STEP-1",
        f"Khởi chạy Backend Server tại http://127.0.0.1:{SERVER_PORT}...",
        CLR_CYAN,
    )
    server_proc = spawn_service(
        root_dir=ROOT_DIR,
        name="SERVER",
        py_executable=server_py,
        script_rel_path="server/app/main.py",
        extra_env={
            "PORT": str(SERVER_PORT),
            "FLASK_ENV": "development",
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
        managed_list=_managed_processes,
    )

    if not wait_for_socket(SERVER_PORT, timeout_sec=20.0):
        log("ERROR", f"Backend Server không phản hồi trên cổng {SERVER_PORT}.", CLR_RED)
        teardown_all()
        sys.exit(1)

    log("STEP-1", f"Backend Server đã lắng nghe trên cổng {SERVER_PORT}!", CLR_GREEN)

    # -----------------------------------------------------------------------
    # BƯỚC 2: KHỞI CHẠY AI PIPELINE (PORT 8000)
    # -----------------------------------------------------------------------
    log(
        "STEP-2",
        f"Khởi chạy AI Pipeline tại http://127.0.0.1:{PIPELINE_PORT}...",
        CLR_MAGENTA,
    )
    pipeline_proc = spawn_service(
        root_dir=ROOT_DIR,
        name="PIPELINE",
        py_executable=pipeline_py,
        script_rel_path="pipeline/app/main.py",
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
        managed_list=_managed_processes,
    )

    if not wait_for_socket(PIPELINE_PORT, timeout_sec=30.0):
        log("ERROR", f"AI Pipeline không mở cổng {PIPELINE_PORT}.", CLR_RED)
        teardown_all()
        sys.exit(1)

    pipeline_health_url = f"http://127.0.0.1:{PIPELINE_PORT}/api/pi/health"
    log(
        "STEP-2",
        f"Đang kiểm tra AI Pipeline healthcheck ({pipeline_health_url})...",
        CLR_MAGENTA,
    )
    if not wait_for_http(pipeline_health_url, timeout_sec=30.0, expected_status=200):
        log("WARNING", "Healthcheck AI Pipeline chưa sẵn sàng, tiếp tục...", CLR_YELLOW)
    else:
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
        root_dir=ROOT_DIR,
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
        managed_list=_managed_processes,
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
    print("  [Bấm Ctrl+C bất cứ lúc nào để dừng và giải phóng 3 cổng sạch sẽ]")
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
