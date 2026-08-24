@echo off
TITLE Project Sentry Launcher

echo ========================================================
echo         Project Sentry - 1-Click Startup Script
echo ========================================================
echo.

:: 1. Check Python Virtual Environment
if not exist ".venv\Scripts\python.exe" (
    echo [*] Creating virtual environment - .venv...
    python -m venv .venv
    echo [*] Installing backend dependencies...
    .\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
) else (
    echo [+] Virtual environment detected - .venv
)

:: 2. Check Node Modules
if not exist "frontend\node_modules" (
    echo [*] Installing frontend dependencies - npm install...
    cd frontend
    call npm install
    cd ..
) else (
    echo [+] Frontend node_modules detected.
)

echo.
echo ========================================================
echo Launching Project Sentry Backend and Frontend...
echo ========================================================
echo.

:: 3. Launch Switch Emulator
start "Sentry Switch Emulator" cmd /k "title Sentry Switch Emulator && cd backend && ..\.venv\Scripts\python.exe switch_emulator.py"

:: 4. Launch FastAPI Backend
start "Sentry FastAPI Backend" cmd /k "title Sentry FastAPI Backend && cd backend && ..\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"

:: 5. Launch React Frontend
start "Sentry React Dashboard" cmd /k "title Sentry React Dashboard && cd frontend && npm start"

echo [+] All services starting! 
echo     - Switch Emulator: 127.0.0.1:2222
echo     - Backend API: http://127.0.0.1:8000
echo     - Frontend Dashboard: http://localhost:3000
echo.
pause
