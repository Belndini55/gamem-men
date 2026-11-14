@echo off
title GameMen - Menedzer Gier
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo Nie znaleziono Pythona. Zainstaluj Python 3.9+ z https://python.org
    echo W instalatorze zaznacz "Add Python to PATH".
    pause
    exit /b 1
)

python app.py %*
if errorlevel 1 pause
