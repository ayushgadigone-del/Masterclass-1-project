@echo off
title Legal Rights Navigator - Frontend
cd /d "%~dp0frontend"

echo.
echo  =====================================================
echo   Legal Rights Navigator : Pre-Litigation Engine
echo   SDG 16 LegalTech MVP
echo  =====================================================
echo.

:: Check Node is available
where node >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Node.js not found. Please install from https://nodejs.org
    pause
    exit /b 1
)

:: Install deps if node_modules is missing
if not exist "node_modules\" (
    echo  Installing dependencies (first run only)...
    call npm install
    echo.
)

echo  Starting Next.js dev server...
echo  Opening http://localhost:3000 in your browser...
echo.
echo  Press Ctrl+C in this window to stop the server.
echo.

:: Open browser after a short delay (server needs ~4s to be ready)
start "" cmd /c "timeout /t 5 /nobreak >nul && start http://localhost:3000"

:: Start the dev server (keeps window open)
call npm run dev
pause
