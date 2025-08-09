@echo off
echo RAG Pipeline Startup Script
echo ===========================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Check if GOOGLE_API_KEY is set
if "%GOOGLE_API_KEY%"=="" (
    echo.
    echo WARNING: GOOGLE_API_KEY environment variable is not set
    echo Some features may not work properly
    echo.
    echo To set it, run: set GOOGLE_API_KEY=your_api_key_here
    echo.
)

REM Run the startup check
echo.
echo Running startup check...
python run.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo Press any key to exit...
    pause >nul
)
