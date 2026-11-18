@echo off
setlocal

:: Prefer verified full Python installation
if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe" (
    set PY_CMD="C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313\python.exe"
    goto RUN
)

if exist "C:\Program Files\Python313\python.exe" (
    set PY_CMD="C:\Program Files\Python313\python.exe"
    goto RUN
)

where py >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PY_CMD=py
    goto RUN
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PY_CMD=python
    goto RUN
)

echo [!] Error: Python 3.13 was not found in standard paths.
pause
exit /b 1

:RUN
cd /d "%~dp0"
if "%~1"=="" (
    %PY_CMD% main.py --help
) else (
    %PY_CMD% main.py %*
)
