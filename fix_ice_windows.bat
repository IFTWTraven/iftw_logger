@echo off
REM Fix zeroc-ice "not installed" issue on another PC
REM This script installs zeroc-ice in the current Python environment

setlocal enabledelayedexpansion

echo.
echo ========================================
echo zeroc-ice Installation/Fix Script
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please ensure Python is installed and added to PATH
    pause
    exit /b 1
)

echo Detected Python:
python --version
echo Python location: 
for /f "delims=" %%i in ('python -c "import sys; print(sys.executable)"') do set "PYTHON_EXE=%%i"
echo !PYTHON_EXE!

REM Check Python version
for /f "delims=" %%i in ('python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set "PYTHON_VERSION=%%i"
echo Python version: !PYTHON_VERSION!

REM Check for Python 3.14+ incompatibility
for /f "tokens=1,2 delims=." %%a in ("!PYTHON_VERSION!") do (
    set "MAJOR=%%a"
    set "MINOR=%%b"
)

if !MAJOR! equ 3 if !MINOR! geq 14 (
    echo.
    echo ========================================
    echo WARNING: Python !MAJOR!.!MINOR! detected
    echo ========================================
    echo.
    echo zeroc-ice does NOT have pre-built wheels for Python 3.14+ yet
    echo This will likely fail with 'DLL load failed' errors
    echo.
    echo RECOMMENDED SOLUTION:
    echo   Use Python 3.11.5 or 3.12 instead:
    echo   - py -3.11 -m pip install --only-binary :all: zeroc-ice
    echo   - py -3.11 saleae2automation/main.py
    echo   - or use the same commands with py -3.12
    echo.
    set /p continue="Continue anyway? (type 'yes' to continue): "
    if /i not "!continue!"=="yes" (
        echo.
        echo Please switch to Python 3.11.5 or 3.12 first.
        pause
        exit /b 0
    )
)

echo.

REM First, run diagnostic
echo.
echo ========================================
echo Running diagnostic...
echo ========================================
python diagnose_ice.py

echo.
echo ========================================
echo Attempting zeroc-ice installation...
echo ========================================
echo.

REM Try installing with pre-built wheels first (avoids C++ compiler requirement)
echo [1/2] Attempting installation with pre-built wheels...
python -m pip install --upgrade --only-binary :all: zeroc-ice >nul 2>&1

if %errorlevel% equ 0 (
    echo [SUCCESS] zeroc-ice installed with pre-built wheels
    goto verify
)

REM If pre-built fails, try standard installation
echo [1/2] Pre-built installation failed, trying standard installation...
python -m pip install --upgrade zeroc-ice

if %errorlevel% neq 0 (
    echo.
    echo [FAILED] Could not install zeroc-ice
    echo.
    echo Alternative methods to try:
    echo   1. Using conda (often better for zeroc-ice):
    echo      conda install -c conda-forge zeroc-ice
    echo.
    echo   2. Upgrade Python to 3.11 or 3.12 (better wheel support)
    echo.
    echo   3. Install Visual Studio C++ Build Tools for compilation
    echo.
    pause
    exit /b 1
)

:verify
echo.
echo ========================================
echo Verifying installation...
echo ========================================
python -c "import Ice; print('[SUCCESS] Ice module imported successfully')" 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Import test failed
    echo Please verify manually by running:
    echo   python -c "import Ice"
) else (
    echo [SUCCESS] Installation verified!
)

echo.
echo ========================================
echo Next steps:
echo ========================================
echo 1. Close and reopen the saleae2automation application
echo 2. Try using Ellisys mode again
echo 3. If issues persist, run 'diagnose_ice.py' again for debugging
echo.

pause
