import os
import sys
import urllib.request
from pathlib import Path

# Fix Windows console UTF-8 encoding issue
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

WEIGHTS_URL = "https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11m.pt"
FALLBACK_URL = "https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8m.pt"
PROJECT_ROOT = Path(__file__).resolve().parent


def download_file(url: str, output_path: Path) -> None:
    print(f"[+] Dang tai trong so tu: {url}")
    try:
        def reporthook(count: int, block_size: int, total_size: int) -> None:
            if total_size > 0:
                percent = int(count * block_size * 100 / total_size)
                print(f"\rTien do: {percent}% [{count * block_size} / {total_size} bytes]", end="", flush=True)

        opener = urllib.request.build_opener()
        opener.addheaders = [("User-Agent", "Mozilla/5.0")]
        urllib.request.install_opener(opener)
        urllib.request.urlretrieve(url, output_path, reporthook=reporthook)
        print(f"\n[OK] Tai thanh cong: {output_path.name}")
    except Exception as ex:
        if output_path.exists():
            output_path.unlink()
        raise ex


if __name__ == "__main__":
    target_weights = PROJECT_ROOT / "yolo11m.pt"
    if target_weights.exists() and target_weights.stat().st_size > 10_000_000:
        print(f"[i] Tep {target_weights.name} da ton tai san ({target_weights.stat().st_size / (1024*1024):.2f} MB).")
    else:
        try:
            download_file(WEIGHTS_URL, target_weights)
        except Exception:
            print("\n[!] Khong the tai yolo11m.pt, thu fallback sang yolov8m.pt...")
            fallback_weights = PROJECT_ROOT / "yolov8m.pt"
            download_file(FALLBACK_URL, fallback_weights)

