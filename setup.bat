@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo   EduFlash AI - Monorepo Automated Setup (Windows CMD)
echo ============================================================
echo.

:: Detect Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [-] ERROR: Python 3.10+ not found on PATH.
    echo     Please install Python from https://www.python.org/
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PY_VER=%%i
echo [*] Detected: %PY_VER%

:: Setup Root .env
if not exist ".env" (
    if exist ".env.example" (
        copy /Y ".env.example" ".env" >nul
        echo [+] Created root .env from .env.example
    )
)

:: Loop services
set "SERVICES=server pipeline client"
for %%S in (%SERVICES%) do (
    echo.
    echo ------------------------------------------------------------
    echo [*] Configuring [%%S]
    echo ------------------------------------------------------------
    
    if not exist "%%S\.env" (
        if exist "%%S\.env.example" (
            copy /Y "%%S\.env.example" "%%S\.env" >nul
            echo [+] Created %%S\.env from %%S\.env.example
        )
    )

    if not exist "%%S\.venv" (
        echo [*] Creating virtual environment in %%S\.venv...
        python -m venv "%%S\.venv"
        echo [+] Virtual environment created.
    ) else (
        echo [=] Virtual environment %%S\.venv already exists.
    )

    if exist "%%S\requirements.txt" (
        echo [*] Installing dependencies for %%S...
        "%%S\.venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
        "%%S\.venv\Scripts\python.exe" -m pip install -r "%%S\requirements.txt"
        echo [+] Dependencies installed for %%S.
    )
)

echo.
echo ============================================================
echo   Setup Complete!
echo ============================================================
echo Next steps:
echo   1. Download AI offline weights:
echo      pipeline\.venv\Scripts\python.exe pipeline\src\download_model.py
echo.
echo   2. Start all services:
echo      python server\scripts\run_e2e_stack.py
echo      (or 'npm start' if Node.js is installed)
echo ============================================================
echo.
pause

