@echo off
:: The Nathaniel Protocol - One-Click Setup
:: Double-click this file to install everything.
:: Requires internet connection for first-time setup.

:: Auto-elevate to Administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator access...
    powershell -Command "Start-Process cmd -ArgumentList '/c cd /d ""%~dp0"" && ""%~f0""' -Verb RunAs"
    exit /b
)

:: We're admin now. Run from the repo directory.
cd /d "%~dp0"

echo.
echo ============================================
echo   The Nathaniel Protocol - Setup
echo ============================================
echo.

:: Step 1: Bootstrap (Git, Python, uv, Kiro config, WSL, Ubuntu)
echo [1/2] Installing prerequisites and WSL...
echo.
set CALLED_FROM_SETUP_BAT=1
powershell -ExecutionPolicy Bypass -File "scripts\bootstrap-windows.ps1"
if %errorlevel% neq 0 (
    echo.
    echo [!] Bootstrap failed. Check the output above for errors.
    echo.
    pause
    exit /b 1
)

:: Step 2: WSL environment (Python, uv, Kiro CLI, setup.sh)
echo.
echo [2/2] Setting up WSL environment and tools...
echo.
powershell -ExecutionPolicy Bypass -File "scripts\setup-wsl.ps1"
if %errorlevel% neq 0 (
    echo.
    echo ============================================
    echo   Setup Incomplete
    echo ============================================
    echo.
    echo   Something went wrong. Check the output above.
    echo   If WSL was just installed, reboot and run setup.bat again.
    echo.
    pause
    exit /b
)

echo.
pause
