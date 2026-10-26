#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""scripts/e2e_utils.py — Helper utilities for E2E Stack Orchestrator."""

from __future__ import annotations

import os
import re
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Dict, List
from urllib.request import Request, urlopen

# ANSI Color Codes
CLR_RESET = "\033[0m"
CLR_CYAN = "\033[36m"
CLR_MAGENTA = "\033[35m"
CLR_GREEN = "\033[32m"
CLR_YELLOW = "\033[33m"
CLR_RED = "\033[31m"
CLR_BOLD = "\033[1m"


def log(prefix: str, msg: str, color: str = CLR_RESET) -> None:
    """In log có màu sắc định dạng chuẩn theo từng service."""
    timestamp = time.strftime("%H:%M:%S")
    sys.stdout.write(f"{color}[{timestamp}][{prefix}]{CLR_RESET} {msg}\n")
    sys.stdout.flush()


def resolve_python(root_dir: Path, service_name: str) -> str:
    """Tìm python executable trong .venv của service hoặc root .venv."""
    is_win = sys.platform == "win32"
    service_venv = (
        root_dir / service_name / ".venv" / "Scripts" / "python.exe"
        if is_win
        else root_dir / service_name / ".venv" / "bin" / "python"
    )
    if service_venv.exists():
        return str(service_venv)

    root_venv = (
        root_dir / ".venv" / "Scripts" / "python.exe"
        if is_win
        else root_dir / ".venv" / "bin" / "python"
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
    root_dir: Path,
    name: str,
    py_executable: str,
    script_rel_path: str,
    extra_env: Dict[str, str],
    color: str,
    managed_list: List[subprocess.Popen],
) -> subprocess.Popen:
    """Khởi động một service dưới dạng tiến trình con với biến môi trường tùy biến."""
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env.update(extra_env)

    script_path = str(root_dir / script_rel_path)
    proc = subprocess.Popen(
        [py_executable, script_path],
        cwd=str(root_dir),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    managed_list.append(proc)
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
