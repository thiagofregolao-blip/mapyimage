@echo off
REM Mapy Image Manager - Startup Script for Windows

setlocal enabledelayedexpansion

echo =========================================
echo Mapy Image Manager
echo =========================================
echo.

REM Check Python version
echo Checking Python version...
python --version

REM Create virtual environment if not exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Initialize database
echo Initializing database...
python -c "from database import Database; db = Database(); print(f'Database initialized: {db.db_path}')"

REM Create necessary directories
if not exist "data" mkdir data
if not exist "uploads" mkdir uploads
if not exist "exports" mkdir exports

REM Check for .env file
if not exist ".env" (
    echo.
    echo WARNING: .env file not found!
    echo Copy .env.example to .env and add your SerpAPI key:
    echo   copy .env.example .env
    echo   notepad .env
    echo.
)

REM Display startup info
echo.
echo =========================================
echo Starting Mapy Image Manager
echo =========================================
echo.
echo Server will be available at:
echo   http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the application
uvicorn app:app --reload --host 0.0.0.0 --port 8000

pause
