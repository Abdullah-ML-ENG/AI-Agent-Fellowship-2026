@echo off
title Enterprise Document Intelligence Platform
echo ==========================================================
echo Starting Enterprise Document Intelligence Platform...
echo ==========================================================
cd /d "%~dp0"
"C:\Users\win 11\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m streamlit run app.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to start Streamlit. Please verify Python installation.
    pause
)
