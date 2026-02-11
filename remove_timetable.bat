@echo off
echo ========================================
echo Removing Timetable Management System
echo ========================================
echo.

REM Delete Python files
echo Deleting Python files...
del /F /Q "timetable_management.py" 2>nul
del /F /Q "timetable_api_routes.py" 2>nul
del /F /Q "hierarchical_timetable.py" 2>nul
del /F /Q "hierarchical_timetable_routes.py" 2>nul
del /F /Q "diagnose_timetable.py" 2>nul
del /F /Q "full_timetable_diagnostic.py" 2>nul

REM Delete JavaScript files
echo Deleting JavaScript files...
del /F /Q "static\js\timetable_management.js" 2>nul
del /F /Q "static\js\staff_timetable.js" 2>nul
del /F /Q "static\js\timetable_admin_override.js" 2>nul

REM Delete HTML templates
echo Deleting HTML templates...
del /F /Q "templates\timetable_management.html" 2>nul
del /F /Q "templates\staff_timetable.html" 2>nul
del /F /Q "templates\staff_period_assignment.html" 2>nul

REM Delete CSS files
echo Deleting CSS files...
del /F /Q "static\css\timetable_management.css" 2>nul

REM Delete documentation files
echo Deleting documentation files...
del /F /Q "HIERARCHICAL_TIMETABLE_COMPLETE.md" 2>nul
del /F /Q "HIERARCHICAL_TIMETABLE_GUIDE.md" 2>nul
del /F /Q "HIERARCHICAL_TIMETABLE_IMPLEMENTATION_SUMMARY.md" 2>nul
del /F /Q "README_TIMETABLE.md" 2>nul
del /F /Q "TIMETABLE_API_REFERENCE.md" 2>nul
del /F /Q "TIMETABLE_ERROR_FIXES.md" 2>nul
del /F /Q "TIMETABLE_FIX_COMPLETE.md" 2>nul
del /F /Q "TIMETABLE_FIX_DOCUMENTATION.md" 2>nul
del /F /Q "TIMETABLE_IMPLEMENTATION_GUIDE.md" 2>nul
del /F /Q "TIMETABLE_IMPLEMENTATION_SUMMARY.md" 2>nul
del /F /Q "TIMETABLE_INTEGRATION_COMPLETE.md" 2>nul
del /F /Q "TIMETABLE_QUICKSTART.md" 2>nul
del /F /Q "TIMETABLE_QUICK_ACCESS.md" 2>nul
del /F /Q "TIMETABLE_SESSION_FIX.md" 2>nul
del /F /Q "TIMETABLE_STAFF_PERIOD_FIXES.md" 2>nul
del /F /Q "TIMETABLE_SYSTEM_FIXED.md" 2>nul
del /F /Q "TIMETABLE_TESTING_GUIDE.md" 2>nul

REM Delete .gemini documentation
echo Deleting .gemini documentation...
del /F /Q ".gemini\timetable_*.md" 2>nul
del /F /Q ".gemini\csrf_fix_documentation.md" 2>nul

echo.
echo ========================================
echo Timetable files removed successfully!
echo ========================================
echo.
echo IMPORTANT: You still need to:
echo 1. Remove timetable routes from app.py
echo 2. Remove timetable menu items from templates
echo 3. Drop timetable database tables (if desired)
echo.
pause
