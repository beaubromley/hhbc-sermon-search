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
set PYTHONIOENCODING=utf-8
python -u update_and_export.py

REM speakers.json is the only data file the site serves statically; publish it if it changed.
pushd ..
git add frontend/public/data/speakers.json
git diff --cached --quiet -- frontend/public/data/speakers.json || (git commit -m "Update speakers.json" -- frontend/public/data/speakers.json && git push)
popd

echo.
echo ========================================
echo Done! New sermons are live immediately.
echo ========================================
echo %date% %time%
echo.
exit /b
