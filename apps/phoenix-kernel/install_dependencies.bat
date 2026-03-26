@echo off
title INSTALLING DEPENDENCIES
echo ============================================================
echo 📦 INSTALLING REZHIVE DEPENDENCIES
echo ============================================================
echo.

cd /d D:\Rezonic_Agentic\apps\phoenix-kernel

echo [1/3] Installing core dependencies...
pip install fastapi uvicorn httpx psutil pynvml pyperclip

echo.
echo [2/3] Installing data science dependencies...
pip install pandas numpy scipy matplotlib

echo.
echo [3/3] Installing web and utility dependencies...
pip install requests beautifulsoup4 PyYAML aiofiles websocket-client

echo.
echo ============================================================
echo ✅ All dependencies installed!
echo ============================================================
pause