@echo off
setlocal

cd /d "%~dp0"

echo Building standalone detector executable...
pyinstaller -F detect_devices.py --name detect_devices.exe
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)

if not exist binary mkdir binary
copy /y dist\detect_devices.exe binary\detect_devices.exe >nul

del /q detect_devices.spec >nul 2>nul
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [OK] Standalone detector generated: binary\detect_devices.exe
echo [OK] Share these files with non-Python users:
echo      - run_device_detection.bat
echo      - binary\detect_devices.exe
pause
