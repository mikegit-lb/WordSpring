@echo off
setlocal
cd /d "%~dp0"

py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if errorlevel 1 goto error
py -3 -m venv .venv
if errorlevel 1 goto error
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 goto error
python -m pip install -r requirements.lock
if errorlevel 1 goto error

echo.
echo WordSpring .venv klasorune kuruldu. Baslatmak icin run_windows.bat dosyasini calistir.
exit /b 0

:error
echo.
echo Kurulum basarisiz. Python 3.11 veya daha yenisini yukleyip tekrar dene.
exit /b 1
