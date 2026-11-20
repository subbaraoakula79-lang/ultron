@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo                ULTRON AUTONOMOUS AGENT ENVIRONMENT SETUP
echo =====================================================================
echo.

:: 1. Find Python
set HOST_PYTHON=
if exist "C:\Users\prgc\AppData\Local\Programs\Python\Python313\python.exe" (
    set HOST_PYTHON=C:\Users\prgc\AppData\Local\Programs\Python\Python313\python.exe
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        set HOST_PYTHON=python
    ) else (
        echo [-] Error: Python 3.11+ is required. Please install Python first.
        pause
        exit /b 1
    )
)

echo [*] Using Host Python: "!HOST_PYTHON!"
"!HOST_PYTHON!" --version

:: 2. Setup Virtual Environment
if not exist ".venv\Scripts\python.exe" (
    echo [*] Creating isolated virtual environment in .venv...
    "!HOST_PYTHON!" -m venv .venv
) else (
    echo [+] Existing virtual environment detected in .venv.
)

:: 3. Install Requirements
echo [*] Installing dependencies from requirements.txt and requirements-dev.txt...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt

:: 4. Environment File Setup
if not exist ".env" (
    echo [*] Initializing .env configuration from .env.example...
    copy .env.example .env >nul
    echo [+] .env created.
) else (
    echo [+] .env already exists.
)

:: 5. Ollama Instructions
echo.
echo =====================================================================
echo                      OLLAMA MODEL SETUP GUIDE
echo =====================================================================
echo ULTRON runs 100%% locally using free open-weights models.
echo If Ollama is installed, run the following command to download the model:
echo.
echo     ollama pull qwen3.5:2b-q4_K_M
echo.
echo If available RAM is under 1.5 GB free, pull the lightweight fallback:
echo.
echo     ollama pull qwen3:1.7b
echo.
echo =====================================================================
echo [+] Setup complete. Run start_ultron.bat to launch ULTRON.
echo =====================================================================
echo.

endlocal
pause
