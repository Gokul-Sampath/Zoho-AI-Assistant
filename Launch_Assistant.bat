@echo off
title Zoho Deluge Scraper & AI Assistant
echo ======================================================================
echo  Launching Zoho Deluge Scraper & AI Assistant
echo ======================================================================
echo.

:: 1. Check if Python with Streamlit is available on the machine
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    python -c "import streamlit" >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo [INFO] Starting application via Python Streamlit runtime...
        cd /d "%~dp0"
        if exist "App.py" (
            start "" python -m streamlit run App.py
            exit /b 0
        )
        if exist "..\\App.py" (
            cd ..
            start "" python -m streamlit run App.py
            exit /b 0
        )
    )
)

:: 2. Fall back to standalone executable if Python environment is absent
if exist "%~dp0Zoho_AI_Assistant\Zoho_AI_Assistant.exe" (
    echo [INFO] Starting standalone executable...
    start "" "%~dp0Zoho_AI_Assistant\Zoho_AI_Assistant.exe"
) else if exist "%~dp0Zoho_AI_Assistant.exe" (
    echo [INFO] Starting standalone executable...
    start "" "%~dp0Zoho_AI_Assistant.exe"
) else (
    echo [ERROR] Neither Python with Streamlit nor Zoho_AI_Assistant.exe was found!
    pause
)
