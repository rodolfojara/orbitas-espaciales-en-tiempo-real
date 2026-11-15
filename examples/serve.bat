@echo off
cd /d "%~dp0output"
"C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe" -m http.server 8000
echo.
echo Abre en tu navegador: http://localhost:8000/ground_track.html
pause