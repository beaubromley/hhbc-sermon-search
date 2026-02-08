@echo off
cd /d "%~dp0"

REM If /auto flag is passed, redirect all output to a log file
if "%1"=="/auto" (
    if not exist logs mkdir logs
    call :run >> "logs\update.log" 2>&1
    exit /b
)

REM Otherwise run interactively
call :run
pause
exit /b

:run
echo ========================================
echo HHBC Sermon Search - Full Update
echo ========================================
echo %date% %time%
echo.

call .venv\Scripts\activate
python update_and_export.py

echo.
echo ========================================
echo Done! New sermons are live immediately.
echo ========================================
echo %date% %time%
echo.
exit /b
