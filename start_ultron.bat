@echo off
setlocal

echo =====================================================================
echo                INITIALIZING ULTRON HOLOGRAPHIC AI AGENT
echo =====================================================================
echo.

set PY_BIN=.venv\Scripts\python.exe
if not exist "%PY_BIN%" (
    if exist "C:\Users\prgc\AppData\Local\Programs\Python\Python313\python.exe" (
        set PY_BIN=C:\Users\prgc\AppData\Local\Programs\Python\Python313\python.exe
    ) else (
        set PY_BIN=python
    )
)

echo [*] Launching Ultron Core & Holographic HUD on localhost:8080...
start "" "http://localhost:8080"
"%PY_BIN%" main.py hud

endlocal
