@echo off
title Zoho Deluge Scraper & AI Assistant
echo ======================================================================
echo  Launching Zoho Deluge Scraper & AI Assistant Desktop Application
echo ======================================================================
echo.

:: Check if Ollama is running locally
curl -s http://localhost:11434/api/tags >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Local Ollama service was not detected at http://localhost:11434!
    echo For AI Assistant chat and embeddings, please launch Ollama in a separate terminal:
    echo    ollama run llama3
    echo    ollama pull nomic-embed-text
    echo.
)

:: Launch the standalone application
if exist "%~dp0Zoho_AI_Assistant\Zoho_AI_Assistant.exe" (
    start "" "%~dp0Zoho_AI_Assistant\Zoho_AI_Assistant.exe"
) else if exist "%~dp0Zoho_AI_Assistant.exe" (
    start "" "%~dp0Zoho_AI_Assistant.exe"
) else (
    echo [ERROR] Zoho_AI_Assistant.exe not found!
    pause
)
