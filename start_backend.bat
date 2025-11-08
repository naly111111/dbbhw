@echo off
chcp 65001 >nul
echo ========================================
echo Starting Backend Server
echo ========================================

echo Checking Python environment...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found, please install Python first
    pause
    exit /b 1
)

echo Checking virtual environment...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

echo Virtual environment activated successfully

echo Installing dependencies...
rem Use python -m pip to avoid pip launcher issues
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo Pip not found, bootstrapping pip...
    python -m ensurepip --upgrade
)

python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo Error: Failed to upgrade pip/setuptools/wheel
)

python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo Skipping database migrations (using native SQL)...
REM echo Running database migrations...
REM python manage.py makemigrations
REM python manage.py migrate
REM if errorlevel 1 (
REM     echo Error: Database migration failed
REM     pause
REM     exit /b 1
REM )

echo Starting Django server...
echo Server URL: http://localhost:8000
echo Press Ctrl+C to stop server
python manage.py runserver
