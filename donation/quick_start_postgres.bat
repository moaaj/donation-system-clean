@echo off
echo ========================================
echo PostgreSQL Migration Quick Start Script
echo ========================================
echo.

echo Step 1: Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Step 2: Creating .env file from template...
if not exist .env (
    copy env_example.txt .env
    echo Please edit .env file with your database credentials
    echo Press any key to open .env file for editing...
    pause
    notepad .env
) else (
    echo .env file already exists
)

echo.
echo Step 3: Testing database connection...
python migrate_to_postgres.py
if %errorlevel% neq 0 (
    echo Error: Database connection failed
    echo Please check your PostgreSQL installation and .env file
    pause
    exit /b 1
)

echo.
echo Step 4: Starting development server...
echo Your app should now be running on PostgreSQL!
echo Visit: http://127.0.0.1:8000
echo.
python manage.py runserver

pause 