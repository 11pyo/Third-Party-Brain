@echo off
chcp 65001 >nul
REM Local mode — http://localhost:5174
python "%~dp0archive-server.py"
pause
