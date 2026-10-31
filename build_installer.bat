@echo off
setlocal
cd /d "%~dp0"

if not exist dist\WordSpring.exe (
  call build_windows.bat
  if errorlevel 1 exit /b 1
)

set "ISCC="
for %%P in (
  "%ProgramFiles(x86)%\Inno Setup 7\ISCC.exe"
  "%ProgramFiles%\Inno Setup 7\ISCC.exe"
  "%LOCALAPPDATA%\Programs\Inno Setup 7\ISCC.exe"
) do if exist "%%~P" set "ISCC=%%~P"

if not defined ISCC (
  echo Inno Setup 7 is required. Install it from https://jrsoftware.org/isdl.php
  exit /b 1
)

"%ISCC%" installer\WordSpring.iss
if errorlevel 1 exit /b 1

echo.
echo Installer created: dist\WordSpring-Setup.exe
