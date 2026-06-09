@echo off
chcp 65001 >nul
REM LAN share mode — binds 0.0.0.0, prints a link for teammates on the same network
python "%~dp0archive-server.py" --share
pause
