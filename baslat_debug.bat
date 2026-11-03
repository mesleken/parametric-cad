@echo off
title Parametrik CAD - Konsol Modu
cd /d "%~dp0"
call "%~dp0.venv\Scripts\activate.bat"
python -m pcad
pause
