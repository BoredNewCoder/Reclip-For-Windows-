@echo off
setlocal
cd /d "%~dp0"

:: Check prerequisites
set MISSING=

py --version >nul 2>&1 || python --version >nul 2>&1 || set MISSING=%MISSING% python
ffmpeg -version >nul 2>&1 || set MISSING=%MISSING% ffmpeg

if not "%MISSING%"=="" (
    echo.
    echo Missing: %MISSING%
    echo Installing...

    echo %MISSING% | findstr /i "python" >nul && (
        echo Installing Python...
        winget install Python.Python.3 --silent --accept-package-agreements --accept-source-agreements -e
    )

    echo %MISSING% | findstr /i "ffmpeg" >nul && (
        echo Installing FFmpeg...
        winget install Gyan.FFmpeg --silent --accept-package-agreements --accept-source-agreements -e
    )

    echo.
    echo ================================================
    echo Install done.
    echo CLOSE this window now,
    echo then double-click reclip.bat again.
    echo ================================================
    pause
    exit /b 0
)

:: Create venv using py launcher (more reliable)
if not exist "venv\" (
    echo Creating virtual environment...
    py -m venv venv
    if errorlevel 1 (
        echo Failed to create venv. Try running again.
        pause
        exit /b 1
    )
    venv\Scripts\pip install -q -r requirements.txt
)

if not defined PORT set PORT=8899

:: Kill old process
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%PORT% " ^| findstr "LISTENING"') do taskkill /F /PID %%p >nul 2>&1

echo.
echo ReClip is running at http://localhost:%PORT%
echo.
venv\Scripts\python app.py

if errorlevel 1 (
    echo.
    echo Error starting ReClip.
    pause
)
