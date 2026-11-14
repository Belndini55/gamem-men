@echo off
title GameMen - budowanie EXE
cd /d "%~dp0"

where pyinstaller >nul 2>nul
if errorlevel 1 (
    echo Instalowanie PyInstaller...
    python -m pip install pyinstaller
)

pyinstaller --noconfirm --onedir --name GameMen ^
    --add-data "web;web" ^
    --icon NONE ^
    app.py

echo.
echo Gotowe! Aplikacja znajduje sie w folderze dist\GameMen\
pause
