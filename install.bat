@echo off
setlocal
echo Launching Tokyo84 UltraStar Deluxe Theme Installer...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
echo.
pause
