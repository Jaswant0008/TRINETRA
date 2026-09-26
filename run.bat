@echo off
title TRINETRA - Multimodal Intelligence Fusion System
color 0A
echo =====================================================================
echo   TRINETRA - Multimodal Intelligence Fusion System (PS-05)
echo   Starting Backend API Server & Frontend UI...
echo =====================================================================
echo.
echo Opening browser at http://127.0.0.1:8000 ...
start http://127.0.0.1:8000
echo.
echo Starting FastAPI Uvicorn Server on 127.0.0.1:8000...
cd /d "%~dp0backend"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
