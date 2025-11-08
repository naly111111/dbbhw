@echo off
chcp 65002 >nul
echo ========================================
echo start all servers
echo ========================================

echo start the backend server...
start "Backend Server" cmd /k "start_backend.bat"

echo wait for 5 seconds...
timeout /t 4 /nobreak >nul

echo start the frontend server...
start "Frontend Server" cmd /k "start_frontend.bat"

echo ========================================
echo server has started
echo backend: http://localhost:8001
echo frontend: http://localhost:8081
echo ========================================
echo push any key to close the window...
pause >nul