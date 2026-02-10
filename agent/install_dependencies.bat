@echo off
REM Install dependencies for Vishnorex Biometric Agent

title Install Dependencies

echo ================================================
echo   Vishnorex Biometric Agent
echo   Dependency Installation
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8 or later from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python found!
python --version
echo.

echo Installing required packages...
echo.

pip install -r requirements.txt

if %errorlevel% equ 0 (
    echo.
    echo ================================================
    echo   Installation Successful!
    echo ================================================
    echo.
    echo You can now run the agent using:
    echo   - start_agent.bat  (quick start)
    echo   - python biometric_agent.py  (with console)
    echo.
) else (
    echo.
    echo ================================================
    echo   Installation Failed!
    echo ================================================
    echo.
    echo Please check the error messages above.
    echo You may need to run this as Administrator.
    echo.
)

pause
