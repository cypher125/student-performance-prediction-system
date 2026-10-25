@echo off
rem Starts the system at http://localhost:8000 and opens it in the browser.
setlocal
cd /d "%~dp0backend"
if not exist .venv\Scripts\python.exe (
  echo The system is not set up yet. Run setup.bat first.
  pause
  exit /b 1
)
if not exist data\app.db (
  echo Creating the demo database...
  .venv\Scripts\python.exe -m app.seed || (pause & exit /b 1)
)
echo Starting the Student Performance Prediction System...
echo Leave this window open while using the system; close it to stop.
start "" cmd /c "timeout /t 15 >nul & start http://localhost:8000"
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
