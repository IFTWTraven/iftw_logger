@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

if not exist "%SCRIPT_DIR%logs" mkdir "%SCRIPT_DIR%logs"
for /f %%I in ('powershell -NoLogo -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "TS=%%I"
set "LOG_FILE=%SCRIPT_DIR%logs\device_detection_%TS%.log"

echo ==================================================
echo Device Detection Launcher
echo Log: %LOG_FILE%
echo ==================================================

set "PY_CMD="
if exist "%SCRIPT_DIR%..\.venv\Scripts\python.exe" set "PY_CMD=%SCRIPT_DIR%..\.venv\Scripts\python.exe"
if "%PY_CMD%"=="" if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" set "PY_CMD=%SCRIPT_DIR%.venv\Scripts\python.exe"
if "%PY_CMD%"=="" where py >nul 2>nul && set "PY_CMD=py"
if "%PY_CMD%"=="" where python >nul 2>nul && set "PY_CMD=python"

if not "%PY_CMD%"=="" (
    echo [INFO] Running with Python command: %PY_CMD%
    if /I "%PY_CMD%"=="py" (
        py "%SCRIPT_DIR%detect_devices.py" --all-methods --verbose --list --vid-summary > "%LOG_FILE%" 2>&1
    ) else (
        "%PY_CMD%" "%SCRIPT_DIR%detect_devices.py" --all-methods --verbose --list --vid-summary > "%LOG_FILE%" 2>&1
    )
    set "EXIT_CODE=!ERRORLEVEL!"
    type "%LOG_FILE%"
    echo.
    echo [INFO] Finished with exit code: !EXIT_CODE!
    echo [INFO] Log saved to: %LOG_FILE%
    pause
    exit /b !EXIT_CODE!
)

if exist "%SCRIPT_DIR%binary\detect_devices.exe" (
    echo [INFO] Python not found. Running packaged executable.
    "%SCRIPT_DIR%binary\detect_devices.exe" --all-methods --verbose --list --vid-summary > "%LOG_FILE%" 2>&1
    set "EXIT_CODE=!ERRORLEVEL!"
    type "%LOG_FILE%"
    echo.
    echo [INFO] Finished with exit code: !EXIT_CODE!
    echo [INFO] Log saved to: %LOG_FILE%
    pause
    exit /b !EXIT_CODE!
)

echo [ERROR] No Python runtime and no packaged executable found.
echo [ERROR] Expected one of:
echo         1) Python/py launcher in PATH
echo         2) ..\.venv\Scripts\python.exe
echo         3) binary\detect_devices.exe
echo.
echo [TIP] Ask your admin to run build_detect_devices_standalone.bat and share binary\detect_devices.exe.
pause
exit /b 2
