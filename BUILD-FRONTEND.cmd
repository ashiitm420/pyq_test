@echo off
rem Builds frontend\dist for running MauryaHub on this PC. Render builds it automatically.
cd /d "%~dp0frontend"
where npm >nul 2>nul
if errorlevel 1 (echo Install Node.js 22 LTS from nodejs.org first. & pause & exit /b 1)
call npm ci || (pause & exit /b 1)
call npm run build || (pause & exit /b 1)
echo Frontend built.
