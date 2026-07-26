@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\make.ps1" -Target "%~1"
exit /b %ERRORLEVEL%
