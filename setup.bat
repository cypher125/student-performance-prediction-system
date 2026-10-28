@echo off
rem One-time setup on a new Windows computer. Needs Python 3.12 or later (python.org).
rem Node.js is only needed if frontend\out is missing (the web interface is prebuilt).
setlocal
cd /d "%~dp0backend"

echo [1/4] Creating the Python environment...
if not exist .venv\Scripts\python.exe (
  py -3 -m venv .venv 2>nul || python -m venv .venv
)
if not exist .venv\Scripts\python.exe (
  echo Python was not found. Install Python 3.12 or later from python.org and run setup.bat again.
  pause
  exit /b 1
)

.venv\Scripts\python.exe -c "import sys; sys.exit(sys.version_info < (3, 12))" || (
  echo This Python is too old: the system needs Python 3.12 or later from python.org.
  echo Delete the backend\.venv folder, install a newer Python and run setup.bat again.
  pause
  exit /b 1
)
echo [2/4] Installing Python packages (this can take a while on a slow connection)...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt || (pause & exit /b 1)

echo [3/4] Checking the trained model...
if not exist artifacts\model.joblib (
  echo No model found: training it now (about 40 minutes on a slow laptop^)...
  .venv\Scripts\python.exe -m ml.prepare_data || (pause & exit /b 1)
  .venv\Scripts\python.exe -m ml.train_models || (pause & exit /b 1)
)

if exist data\app.db (
  echo [4/4] Keeping the existing database, data\app.db
) else (
  echo [4/4] Creating the demo database...
  .venv\Scripts\python.exe -m app.seed || (pause & exit /b 1)
)

if not exist "%~dp0frontend\out\index.html" (
  echo Building the web interface...
  cd /d "%~dp0frontend"
  call npm install && call npm run build
)

echo.
echo Setup complete. Double-click start.bat to run the system.
pause
