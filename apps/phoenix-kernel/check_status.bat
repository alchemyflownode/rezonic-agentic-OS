@echo off
title SYSTEM STATUS - RezHive + ComfyUI
echo ============================================================
echo 🔍 CHECKING SYSTEM STATUS
echo ============================================================
echo.

echo 📡 Checking Phoenix API...
curl -s http://localhost:8002/health 2>nul
if %ERRORLEVEL% EQU 0 (
    echo   ✅ Phoenix is running
) else (
    echo   ❌ Phoenix is NOT running
)

echo.
echo 🎨 Checking ComfyUI...
curl -s http://localhost:8188/system_stats 2>nul
if %ERRORLEVEL% EQU 0 (
    echo   ✅ ComfyUI is running
) else (
    echo   ❌ ComfyUI is NOT running
)

echo.
echo ============================================================
echo.
echo 💡 To start systems:
echo    start_both.bat
echo.
echo 💡 To stop systems:
echo    stop_all.bat
echo.
echo ============================================================
pause