@echo off
setlocal

:: ==========================================
:: i-HR Android Signed Build Script
:: ==========================================

:: 1. Sync Capacitor
echo [1/3] Syncing Capacitor...
call npx cap sync

:: 2. Set your Keystore details here
:: IMPORTANT: Replace these with your actual details or it will fail
set KEYSTORE_PATH=my-release-key.jks
set KEYSTORE_PASSWORD=i-HR@2026
set KEY_ALIAS=my-alias
set KEY_PASSWORD=i-HR@2026

:: 3. Run Gradle Build
echo [2/3] Building Signed APK...
cd android
call gradlew assembleRelease ^
  -PMYAPP_RELEASE_STORE_FILE=../../%KEYSTORE_PATH% ^
  -PMYAPP_RELEASE_STORE_PASSWORD=%KEYSTORE_PASSWORD% ^
  -PMYAPP_RELEASE_KEY_ALIAS=%KEY_ALIAS% ^
  -PMYAPP_RELEASE_KEY_PASSWORD=%KEY_PASSWORD%

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Build failed. Check your keystore path and passwords.
    pause
    exit /b %ERRORLEVEL%
)

:: 4. Done
echo.
echo [3/3] SUCCESS!
echo Your signed APK is located at:
echo android\app\build\outputs\apk\release\app-release.apk
echo.
pause
