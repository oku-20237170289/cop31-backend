@echo off
title COP31 Backend API
chcp 65001 > nul
echo ========================================================
echo       COP31 Harita ve Etkinlik Platformu Backend
echo                  IDD ORG Teknoloji Ekibi
echo ========================================================
echo.
echo Servis baslatiliyor...
echo Swagger Dokumantasyonu: http://127.0.0.1:8000/docs
echo.
call "%~dp0venv\Scripts\activate.bat"
python "%~dp0run.py"
pause
