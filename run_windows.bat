@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo WordSpring henuz kurulmamadi. Once setup_windows.bat dosyasini calistir.
  exit /b 1
)
.venv\Scripts\python.exe main.py
