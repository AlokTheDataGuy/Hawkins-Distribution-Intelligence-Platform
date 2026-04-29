@echo off
echo Starting HDIP backend and frontend...

cd /d "%~dp0"

start "HDIP Backend" cmd /k "venv\Scripts\activate && cd backend && uvicorn main:app --reload --port 8000"
timeout /t 2 >nul
start "HDIP Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo API docs: http://localhost:8000/docs
