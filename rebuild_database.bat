@echo off
chcp 65001 >nul
echo ========================================
echo Rebuilding Database Script
echo ========================================
echo.

REM Check if MySQL is available
where mysql >nul 2>&1
if errorlevel 1 (
    echo Error: MySQL command not found. Please ensure MySQL is in your PATH.
    pause
    exit /b 1
)

echo Step 1: Dropping existing database (if exists)...
mysql -u root -p113442 -e "DROP DATABASE IF EXISTS novel_platform;" 2>nul
if errorlevel 1 (
    echo Warning: Failed to drop database. It may not exist. Continuing...
)

echo.
echo Step 2: Creating and initializing database from init_database.sql...
mysql -u root -p113442 --default-character-set=utf8mb4 < init_database.sql
if errorlevel 1 (
    echo Error: Failed to initialize database. Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo Step 3: Verifying categories data...
mysql -u root -p113442 --default-character-set=utf8mb4 novel_platform -e "SELECT * FROM categories;"

echo.
echo ========================================
echo Database rebuild completed successfully!
echo ========================================
pause



