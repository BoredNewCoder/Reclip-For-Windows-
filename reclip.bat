@echo off
setlocal

cd /d "%~dp0"

:: Check prerequisites
set MISSING=

:: Use --version not where -- avoids Win11 fake python Store stub
python --version >nul 2>&1 || set MISSING=%MISSING% python
ffmpeg  -version >nul 2>&1 || set MISSING=%MISSING% ffmpeg

if not "%MISSING%"=="" (
    echo Missing required tools:%MISSING%
    echo.
    echo Install with winget:
    echo %MISSING% | findstr /i "python" >nul && echo   winget install Python.Python.3
    echo %MISSING% | findstr /i "ffmpeg" >nul && echo   winget install Gyan.FFmpeg
    echo.
    echo After installing, open a NEW terminal and run reclip.bat again.
    pause
    exit /b 1
)

:: Set up venv (yt-dlp installed here via requirements.txt -- no system install needed)
if not exist "venv\" (
    echo Setting up virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment. Is Python installed correctly?
        echo Run: winget install Python.Python.3
        echo Then open a NEW terminal and try again.
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
    pip install -q -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

if not defined PORT set PORT=8899

echo.
echo   ReClip is running at http://localhost:%PORT%
echo.

python app.py
