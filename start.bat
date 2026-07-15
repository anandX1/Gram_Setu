@echo off
echo =======================================================
echo AI GramSetu - Local Server Startup (Node & Python ML)
echo =======================================================
echo.

:: 1. Check for Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH!
    echo Please install it from https://nodejs.org/
    pause
    exit /b
)

:: 2. Check for Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install it from https://www.python.org/
    pause
    exit /b
)

echo [1/5] Installing Node.js dependencies (if any)...
call npm install

echo.
echo [2/5] Installing Python ML dependencies (this might take a minute)...
pip install -r requirements_new.txt

echo.
echo [3/5] Starting the Node.js API server on port 3000...
start "AI GramSetu - Node.js Server" cmd /c "node server.js & pause"

echo.
echo [4/5] Starting the Python ML server on port 5000...
start "AI GramSetu - ML Server" cmd /c "python ml_server.py & pause"

echo.
echo [5/5] Launching Cloudflare Tunnel...
echo Downloading cloudflared.exe (if not exists)...
if not exist cloudflared.exe (
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'cloudflared.exe'"
)

echo.
echo =========================================================================
echo ALL SERVERS ARE RUNNING!
echo.
echo Please wait a few seconds and look for the "trycloudflare.com" URL below.
echo Copy that URL and give it to your visitor as part of your Vercel link:
echo.
echo Example: https://your-vercel.app/?api=https://xxxxx.trycloudflare.com
echo =========================================================================
echo.
cloudflared.exe tunnel --url http://localhost:3000

pause
