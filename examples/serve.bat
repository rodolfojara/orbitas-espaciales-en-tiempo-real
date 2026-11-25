@echo off
cd /d "%~dp0.."
if exist "%~dp0..\.venv\Scripts\python.exe" (
    "%~dp0..\.venv\Scripts\python.exe" examples/serve.py
) else (
    python examples/serve.py
)
pause
