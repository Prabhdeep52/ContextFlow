@echo off
echo RAG Pipeline - Complete Startup
echo ===============================

echo.
echo Starting Backend...
echo ------------------
start "Backend" cmd /k "cd backend && python run.py"

echo.
echo Starting Frontend...
echo -------------------
start "Frontend" cmd /k "cd frontend && npm start"

echo.
echo Both services are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to exit this launcher...
pause >nul
