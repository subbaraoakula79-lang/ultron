@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo                 ULTRON SYSTEM READINESS DIAGNOSTIC
echo =====================================================================
echo.

:: 1. Check Python
echo [1/6] Checking Python Environment...
set PYTHON_EXE=
if exist ".venv\Scripts\python.exe" (
    set PYTHON_EXE=.venv\Scripts\python.exe
    echo     [+] Dedicated virtual environment located: .venv\Scripts\python.exe
) else (
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON_EXE=python
        echo     [+] System Python located on PATH.
    ) else if exist "C:\Users\prgc\AppData\Local\Programs\Python\Python313\python.exe" (
        set PYTHON_EXE=C:\Users\prgc\AppData\Local\Programs\Python\Python313\python.exe
        echo     [+] Host Python 3.13 located.
    ) else (
        echo     [-] CRITICAL: Python executable not found. Please install Python 3.11+.
        goto :END
    )
)
"%PYTHON_EXE%" --version
echo.

:: 2. Check Dependencies
echo [2/6] Checking Core Python Dependencies...
"%PYTHON_EXE%" -c "import psutil; import watchdog; import pytest; print('    [+] psutil, watchdog, and pytest verified.')" 2>nul
if %errorlevel% neq 0 (
    echo     [-] Warning: Some dependencies are missing. Run setup_ultron.bat to install.
)
echo.

:: 3. Check Local RAM & Memory Budget
echo [3/6] Inspecting 8 GB RAM Telemetry...
"%PYTHON_EXE%" -c "import psutil; m=psutil.virtual_memory(); print(f'    [+] Total RAM: {m.total/(1024**3):.2f} GB | Available Free: {m.available/(1024**3):.2f} GB ({100-m.percent:.1f}%% free)'); print('    [+] RAM Allocation: Within 8 GB optimization profile.' if m.available > 800*1024*1024 else '    [!] Notice: Free RAM low (<800MB). Falling back to Qwen 1.7B profile.')"
echo.

:: 4. Check Ollama Local AI Runtime
echo [4/6] Checking Local Ollama AI Daemon...
where ollama >nul 2>&1
if %errorlevel% equ 0 (
    echo     [+] Ollama executable found on PATH.
    ollama --version
) else (
    echo     [!] Notice: 'ollama' is not in PATH or not yet installed.
    echo         To install Ollama, run: winget install Ollama.Ollama
    echo         Or download directly from: https://ollama.com/download
)
"%PYTHON_EXE%" -c "import urllib.request, json; (urllib.request.urlopen('http://localhost:11434/api/tags', timeout=2)); print('    [+] Ollama daemon is actively running on port 11434.')" 2>nul
if %errorlevel% neq 0 (
    echo     [!] Notice: Ollama daemon is currently offline at http://localhost:11434.
    echo         Start Ollama with: ollama run qwen3.5:2b-q4_K_M
    echo         Ultron will operate via Heuristic/Deterministic Mode until Ollama starts.
)
echo.

:: 5. Check Android & ADB Connectivity
echo [5/6] Checking Android ADB Connectivity...
set ADB_EXE=C:\Users\prgc\AppData\Local\Android\Sdk\platform-tools\adb.exe
if not exist "!ADB_EXE!" (
    where adb >nul 2>&1
    if !errorlevel! equ 0 (
        set ADB_EXE=adb
    )
)
if exist "!ADB_EXE!" (
    echo     [+] ADB located: !ADB_EXE!
    "!ADB_EXE!" devices
) else (
    echo     [!] ADB tool not detected. Mobile automation will be unavailable until Android SDK is added.
)
echo.

:: 6. Check Google ARTEMIS Integration
echo [6/6] Checking Google ARTEMIS Framework...
if exist "artemis\pyproject.toml" (
    echo     [+] Official Google ARTEMIS directory present in workspace.
    if exist "artemis\start.bat" (
        echo     [+] ARTEMIS launcher verified: artemis\start.bat
    )
) else (
    echo     [!] Google ARTEMIS repository not detected at artemis/.
)
echo.

echo =====================================================================
echo                DIAGNOSTIC COMPLETE - READY TO RUN
echo =====================================================================
echo To launch Ultron Holographic HUD: start_ultron.bat
echo.

:END
endlocal
pause
