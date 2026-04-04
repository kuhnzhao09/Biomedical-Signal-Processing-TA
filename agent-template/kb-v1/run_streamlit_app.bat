@echo off
setlocal
cd /d "%~dp0"
python -m streamlit run "%~dp0streamlit_app.py" --server.headless true --browser.gatherUsageStats false --server.port 8501
pause
