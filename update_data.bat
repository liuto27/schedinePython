@echo off
echo ============================================
echo Running local update of CSV data...
echo ============================================
REM Step 1: Run the download_data.py script to update CSVs locally
python download_data.py
if ERRORLEVEL 1 (
    echo ERROR: download_data.py encountered an error.
    pause
    exit /b 1
)

echo ============================================
echo Committing and pushing changes to GitHub...
echo ============================================
REM Step 2: Add, commit, and push changes to GitHub
git add data/.
git commit -m "Automatic update: refreshed CSV data"
git push origin main
if ERRORLEVEL 1 (
    echo ERROR: Git push failed.
    pause
    exit /b 1
)