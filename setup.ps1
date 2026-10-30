# ============================================================
# EduFlash AI - Monorepo Automated Setup (PowerShell)
# ============================================================
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  EduFlash AI - Monorepo Automated Setup (PowerShell)" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# 1. Check Python
$pyCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pyCmd) {
    Write-Host "[-] ERROR: Python 3.10+ not found on PATH." -ForegroundColor Red
    Write-Host "    Please install Python from https://www.python.org/" -ForegroundColor Yellow
    exit 1
}

$pyVer = & python --version 2>&1
Write-Host "[*] Detected: $pyVer" -ForegroundColor Green

# 2. Setup Root .env
if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[+] Created root .env from .env.example" -ForegroundColor Green
}

# 3. Setup services
$services = @("server", "pipeline", "client")

foreach ($svc in $services) {
    Write-Host "`n------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "[*] Configuring [$($svc.ToUpper())]..." -ForegroundColor Yellow
    Write-Host "------------------------------------------------------------" -ForegroundColor DarkGray

    # Setup .env
    $envPath = Join-Path $svc ".env"
    $envExPath = Join-Path $svc ".env.example"
    if (-not (Test-Path $envPath) -and (Test-Path $envExPath)) {
        Copy-Item $envExPath $envPath
        Write-Host "[+] Created $svc/.env from $svc/.env.example" -ForegroundColor Green
    }

    # Setup .venv
    $venvPath = Join-Path $svc ".venv"
    if (-not (Test-Path $venvPath)) {
        Write-Host "[*] Creating virtual environment in $svc/.venv..." -ForegroundColor Gray
        & python -m venv $venvPath
        Write-Host "[+] Virtual environment created." -ForegroundColor Green
    } else {
        Write-Host "[=] Virtual environment $svc/.venv already exists." -ForegroundColor Gray
    }

    # Install requirements
    $reqPath = Join-Path $svc "requirements.txt"
    $pipPath = Join-Path $svc ".venv\Scripts\pip.exe"
    $pythonPath = Join-Path $svc ".venv\Scripts\python.exe"

    if (Test-Path $reqPath) {
        Write-Host "[*] Installing dependencies for $svc..." -ForegroundColor Gray
        if (Test-Path $pythonPath) {
            & $pythonPath -m pip install --upgrade pip --quiet
            & $pythonPath -m pip install -r $reqPath
        } else {
            & python -m pip install -r $reqPath
        }
        Write-Host "[+] Dependencies installed successfully for $svc." -ForegroundColor Green
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Download AI offline weights:" -ForegroundColor Yellow
Write-Host "     .\pipeline\.venv\Scripts\python.exe pipeline\src\download_model.py" -ForegroundColor White
Write-Host "`n  2. Start all 3 services:" -ForegroundColor Yellow
Write-Host "     python server\scripts\run_e2e_stack.py" -ForegroundColor White
Write-Host "     (or 'npm start' / 'npm run dev' if Node.js is installed)`n" -ForegroundColor Gray

