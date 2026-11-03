@echo off
cd /d "%~dp0"
call "%~dp0.venv\Scripts\activate.bat"
start "" "%~dp0.venv\Scripts\pythonw.exe" -m pcad
