@echo off
chcp 65001 >nul
set PYTHONUTF8=1
where py >nul 2>nul && (set "PYCMD=py -3") || (set "PYCMD=python")
%PYCMD% "%~dp0generate_data.py"
if errorlevel 1 (echo FAILED - see message above & pause & exit /b 1)
start "" "%~dp0..\dashboard\index.html"
