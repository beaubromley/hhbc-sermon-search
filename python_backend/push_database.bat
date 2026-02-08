@echo off
echo ========================================
echo Pushing Updated Database to GitHub
echo ========================================

cd /d "%~dp0"

echo Adding database and video data...
git add data/database/transcripts.db
git add data/transcripts/video_data.json

echo Committing changes...
git commit -m "Updated database - %date% %time%"

echo Pushing to GitHub...
git push

echo.
echo ========================================
echo Database pushed successfully!
echo Streamlit will auto-update in 1-2 minutes
echo ========================================
pause
