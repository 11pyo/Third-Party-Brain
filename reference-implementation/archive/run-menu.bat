@echo off
chcp 65001 >nul
REM Terminal UI (keyboard-only archive browser)
python "%~dp0archive-menu.py"
