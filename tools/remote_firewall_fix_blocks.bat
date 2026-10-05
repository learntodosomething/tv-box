@echo off
rem TV Box - python-ra vonatkozo bejovo TILTO tuzfalszabalyok listazasa/torlese (rendszergazdai jog kell).
net session >nul 2>&1
if %errorlevel% neq 0 (
  echo Rendszergazdai jogosultsag kell - ujrainditas emelt joggal...
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0remote_firewall_fix_blocks.ps1"
echo.
pause
