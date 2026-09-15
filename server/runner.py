import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

SERVER_DIR = Path(__file__).resolve().parent
ROOT_DIR = SERVER_DIR.parent
PIPELINE_DIR = ROOT_DIR / "pipeline"

# Load local configurations
load_dotenv(SERVER_DIR / ".env")
load_dotenv(PIPELINE_DIR / ".env")

SERVER_PORT = os.getenv("SERVER_PORT", "3000")
SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
PIPELINE_PORT = os.getenv("PIPELINE_PORT", "3100")
PIPELINE_HOST = os.getenv("PIPELINE_HOST", "0.0.0.0")


def print_banner() -> None:
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    banner = f"""
==============================================================
🚀 KHOI CHAY DONG THOI: SERVER GATEWAY (3000) & PIPELINE (3100)
--------------------------------------------------------------
📡 [Pipeline Service]: http://localhost:{PIPELINE_PORT}
   📖 Pipeline Swagger: http://localhost:{PIPELINE_PORT}/docs
📡 [Server Gateway]:   http://localhost:{SERVER_PORT}
   📖 Server Swagger:   http://localhost:{SERVER_PORT}/docs
   🎯 Pipeline Link:    http://localhost:{PIPELINE_PORT}
==============================================================
"""
    print(banner, flush=True)


def stop_process(proc: subprocess.Popen) -> None:
    if proc and proc.poll() is None:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            try:
                proc.terminate()
                proc.wait(timeout=2.0)
            except Exception:
                proc.kill()


def main() -> None:
    print_banner()

    # 1. Start Pipeline Service on Port 3100
    pipeline_cmd = [
        sys.executable, "-m", "uvicorn", "app:app",
        "--host", PIPELINE_HOST,
        "--port", str(PIPELINE_PORT),
        "--reload"
    ]
    pipeline_proc = subprocess.Popen(pipeline_cmd, cwd=str(PIPELINE_DIR))

    # Give Pipeline a brief moment to bind port
    time.sleep(1.2)

    # 2. Start Server Gateway on Port 3000
    server_cmd = [
        sys.executable, "-m", "uvicorn", "app:app",
        "--host", SERVER_HOST,
        "--port", str(SERVER_PORT),
        "--reload"
    ]
    server_proc = subprocess.Popen(server_cmd, cwd=str(SERVER_DIR))

    try:
        while True:
            time.sleep(1.0)
            if pipeline_proc.poll() is not None or server_proc.poll() is not None:
                break
    except KeyboardInterrupt:
        print("\n[!] Nhan lenh dung (Ctrl+C). Dang dong cac tien trinh...", flush=True)
    finally:
        stop_process(pipeline_proc)
        stop_process(server_proc)
        print("[OK] Da dung tat ca cac tien trinh an toan.", flush=True)


if __name__ == "__main__":
    main()

