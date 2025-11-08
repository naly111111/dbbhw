@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================
echo Starting Frontend Server
echo ========================================

echo Checking Node.js environment...
node --version >nul 2>&1
if errorlevel 1 (
    echo Error: Node.js not found, please install Node.js first
    pause
    exit /b 1
)

echo Checking npm...
echo Installing dependencies...
call npm install

call npm run serve


endlocal

