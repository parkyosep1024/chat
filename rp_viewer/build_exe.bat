@echo off
rem RP Viewer EXE build script (PyInstaller --onedir)
rem Output: dist\RPViewer\RPViewer.exe
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python launcher "py" not found. Install Python 3 from python.org.
    goto :fail
)

echo [1/3] Installing build dependencies...
py -m pip install --upgrade -r requirements.txt pyinstaller
if errorlevel 1 goto :fail

echo [2/3] Running tests...
py -m unittest discover -s tests
if errorlevel 1 goto :fail

echo [3/3] Building EXE...
py -m PyInstaller --noconfirm --clean --noconsole --onedir --name RPViewer ^
    --exclude-module tkinter ^
    main.py
if errorlevel 1 goto :fail

echo.
echo Build complete: "%~dp0dist\RPViewer\RPViewer.exe"
echo Settings file:  "%APPDATA%\RPViewer\settings.json"
endlocal
pause
exit /b 0

:fail
echo.
echo [FAILED] Build did not complete.
endlocal
pause
exit /b 1
