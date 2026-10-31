@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Run setup_windows.bat first.
  exit /b 1
)
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean WordSpring.spec
if errorlevel 1 exit /b 1
echo.
echo Derleme tamamlandi: dist\WordSpring.exe
