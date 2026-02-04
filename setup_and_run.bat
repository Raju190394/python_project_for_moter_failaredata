@echo off
SETLOCAL EnableDelayedExpansion

echo ======================================================
echo    Industrial Reliability Dashboard - Auto Setup
echo ======================================================
echo.

:: 1. Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/
    pause
    exit /b
)

echo [1/3] Python detected successfully.

:: 2. Install dependencies
echo [2/3] Installing required libraries (this may take a minute)...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to install dependencies. Check your internet connection.
    pause
    exit /b
)

echo [3/3] Dependencies installed. Initializing Dashboard...

:: 3. Run the application
echo.
echo Launching Dashboard in your browser...
echo.
python -m streamlit run app.py

pause
