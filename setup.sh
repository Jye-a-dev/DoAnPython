#!/usr/bin/env bash
# ============================================================
# EduFlash AI - Monorepo Automated Setup (Linux / macOS)
# ============================================================

set -euo pipefail

echo "============================================================"
echo "  EduFlash AI - Monorepo Automated Setup (Bash)"
echo "============================================================"
echo ""

# 1. Detect Python 3
if command -v python3 >/dev/null 2>&1; then
    PY_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PY_CMD="python"
else
    echo "[-] ERROR: Python 3.10+ not found on PATH." >&2
    echo "    Please install Python 3.10+ and add it to your PATH." >&2
    exit 1
fi

PY_VER=$($PY_CMD --version 2>&1)
echo "[*] Detected: $PY_VER"

# 2. Root .env setup
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    echo "[+] Created root .env from .env.example"
fi

# 3. Setup services
SERVICES=("server" "pipeline" "client")

for SVC in "${SERVICES[@]}"; do
    echo ""
    echo "------------------------------------------------------------"
    echo "[*] Configuring [${SVC^^}]..."
    echo "------------------------------------------------------------"

    # Copy .env
    if [ ! -f "$SVC/.env" ] && [ -f "$SVC/.env.example" ]; then
        cp "$SVC/.env.example" "$SVC/.env"
        echo "[+] Created $SVC/.env from $SVC/.env.example"
    fi

    # Create virtualenv
    if [ ! -d "$SVC/.venv" ]; then
        echo "[*] Creating virtual environment in $SVC/.venv..."
        $PY_CMD -m venv "$SVC/.venv"
        echo "[+] Virtual environment created."
    else
        echo "[=] Virtual environment $SVC/.venv already exists."
    fi

    # Install dependencies
    if [ -f "$SVC/requirements.txt" ]; then
        echo "[*] Installing dependencies for $SVC..."
        "$SVC/.venv/bin/python" -m pip install --upgrade pip --quiet
        "$SVC/.venv/bin/python" -m pip install -r "$SVC/requirements.txt"
        echo "[+] Dependencies installed successfully for $SVC."
    fi
done

echo ""
echo "============================================================"
echo "  Setup Complete!"
echo "============================================================"
echo "Next steps:"
echo "  1. Download AI offline weights:"
echo "     pipeline/.venv/bin/python pipeline/src/download_model.py"
echo ""
echo "  2. Start all 3 services:"
echo "     python3 server/scripts/run_e2e_stack.py"
echo "     (or 'npm start' / 'npm run dev' if Node.js is installed)"
echo "============================================================"
echo ""

