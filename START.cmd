@echo off
cd /d "%~dp0"
if not exist "frontend\dist\index.html" call BUILD-FRONTEND.cmd
if exist ".venv\Scripts\python.exe" (set "PYTHON=.venv\Scripts\python.exe") else (set "PYTHON=py -3")
%PYTHON% "scripts\start_release.py"
pause
