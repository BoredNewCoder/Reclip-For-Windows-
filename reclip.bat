@echo off
setlocal
cd /d "%~dp0"

echo.
echo ================================================
echo               ReClip Launcher
echo ================================================
echo.

:: ==================== PYTHON SETUP ====================
if not exist "python\python.exe" (
    echo Downloading Python, please wait...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.3/python-3.13.3-embed-amd64.zip' -OutFile 'python-embed.zip' -UseBasicParsing"
    if not exist "python-embed.zip" (
        echo.
        echo ERROR: Download failed. Check your internet connection.
        echo Close this window and run reclip.bat again.
        echo.
        pause
        exit /b 1
    )
    powershell -Command "Expand-Archive -Path 'python-embed.zip' -DestinationPath 'python' -Force"
    del python-embed.zip

    :: Enable site-packages so pip works
    powershell -Command "(Get-Content 'python\python313._pth') -replace '#import site','import site' | Set-Content 'python\python313._pth'"

    :: Install pip
    echo Installing pip...
    powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py' -UseBasicParsing"
    python\python.exe get-pip.py -q
    del get-pip.py
)

echo Python OK.

:: ==================== DEPENDENCIES ====================
if not exist "python\Lib\site-packages\flask" (
    echo First-time setup: downloading packages, this may take a few minutes...
) else (
    echo Checking for updates...
)
python\python.exe -m pip install -U -r requirements.txt -q
echo Ready.

:: ==================== KILL STALE PORT ====================
if not defined PORT set PORT=8899
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%PORT% " ^| findstr "LISTENING" 2^>nul') do (
    taskkill /F /PID %%p >nul 2>&1
)

:: ==================== LAUNCH ====================
echo.
echo ================================================
echo  ReClip is running!
echo.
echo  Your browser will open automatically.
echo  If it doesn't, go to: http://localhost:%PORT%
echo.
echo  Keep this window open while using ReClip.
echo  To stop ReClip: press Ctrl+C or close this window.
echo ================================================
echo.

python\python.exe app.py

if errorlevel 1 (
    echo.
    echo ReClip stopped unexpectedly.
    echo.
    pause
)