@echo off
REM Vishnorex Biometric Agent Launcher
REM This batch file starts the agent in the background

title Vishnorex Biometric Agent

echo ================================================
echo   Vishnorex Biometric Agent
echo ================================================
echo.
echo Starting agent...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or later from python.org
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import PyQt5" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Start the agent
echo Agent starting... (window will minimize to system tray)
echo.
start /B pythonw biometric_agent.py

echo Agent launched successfully!
echo Look for the agent icon in your system tray.
echo.
timeout /t 3 >nul

exit
