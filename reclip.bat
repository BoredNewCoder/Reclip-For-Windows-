@echo off
setlocal
cd /d "%~dp0"

echo.
echo ================================================
echo               ReClip Launcher
echo ================================================
echo.

:: Check winget
where winget >nul 2>&1
if %errorlevel% neq 0 (
    echo Winget is not installed.
    echo.
    echo 1. Open the Microsoft Store
    echo 2. Search for "App Installer"
    echo 3. Install or Update it
    echo.
    echo Then close this window and run reclip.bat again.
    pause
    exit /b 1
)

:: ==================== PYTHON SECTION ====================
where py >nul 2>&1
if %errorlevel% neq 0 (
    where python >nul 2>&1
    if %errorlevel% neq 0 (
        echo Installing Python 3.13 for current user...
        echo.

        winget install --id Python.Python.3.13 --scope user --exact --silent --accept-package-agreements --accept-source-agreements

        echo.
        echo ================================================
        echo Python 3.13 installed successfully.
        echo.
        echo IMPORTANT:
        echo Close this window completely (click the X),
        echo then double-click reclip.bat again.
        echo ================================================
        pause
        exit /b 0
    )
)

echo Python detected.

:: ==================== FFMPEG SECTION ====================
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing FFmpeg...
    winget install --id Gyan.FFmpeg --exact --silent --accept-package-agreements --accept-source-agreements
    echo FFmpeg installed.
    echo.
)

:: ==================== VENV CREATION ====================
if exist "venv\" (
    if not exist "venv\Scripts\python.exe" (
        echo Removing broken venv...
        rmdir /s /q venv
    )
)

if not exist "venv\" (
    echo Creating virtual environment...
    py -m venv venv || python -m venv venv
    if errorlevel 1 (
        echo Failed to create venv.
        echo Please close this window and run reclip.bat again.
        pause
        exit /b 1
    )
    echo Virtual environment created.
)

:: ==================== UPDATE DEPENDENCIES ====================
echo Updating dependencies from requirements.txt...
venv\Scripts\python -m pip install --upgrade pip -q
venv\Scripts\pip install -U -r requirements.txt -q
echo Dependencies updated.
echo.

:: ==================== LAUNCH RECLIP ====================
if not defined PORT set PORT=8899

:: Kill stale process
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%PORT% " ^| findstr "LISTENING" 2^>nul') do (
    taskkill /F /PID %%p >nul 2>&1
)

echo ================================================
echo ReClip is running at http://localhost:%PORT%
echo Press Ctrl+C to stop.
echo ================================================
echo.

venv\Scripts\python app.py

if errorlevel 1 (
    echo.
    echo Error starting ReClip.
    pause
)