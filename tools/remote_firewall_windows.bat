@echo off
rem TV Box - telefonos tavirányito: bejovo kapcsolatok engedelyezese a Windows tuzfalon.
rem Csak a helyi alhalozatrol (telefon, laptop) engedi a 8765-8784 TCP portokat.
rem Torles:  netsh advfirewall firewall delete rule name="TV Box Remote"

net session >nul 2>&1
if %errorlevel% neq 0 (
  echo Rendszergazdai jogosultsag kell - ujrainditas emelt joggal...
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
  exit /b
)

netsh advfirewall firewall delete rule name="TV Box Remote" >nul 2>&1
netsh advfirewall firewall add rule name="TV Box Remote" dir=in action=allow protocol=TCP localport=8765-8784 remoteip=localsubnet profile=any
if %errorlevel% equ 0 (
  echo.
  echo KESZ: a "TV Box Remote" szabaly letrejott. Probald ujra a telefonnal.
) else (
  echo.
  echo HIBA: a szabaly letrehozasa nem sikerult.
)
echo.
pause
