@echo off
echo ===================================================
echo   📦 BubbleWrap Monitor - Starting All Services
echo ===================================================

echo [1/2] Starting Background Scheduler...
start /b python scheduler.py

echo [2/2] Starting Streamlit Dashboard...
start /b streamlit run app.py --server.port 8501 --server.address 0.0.0.0

echo.
echo All services are starting in the background.
echo Dashboard: http://localhost:8501
echo.
pause
