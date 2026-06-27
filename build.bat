@echo off
chcp 65001 >nul
echo ========================================
echo LANITS - Windows Build Script (PyInstaller)
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8+.
    exit /b 1
)

:: Install dependencies
echo [1/4] Installing dependencies...
pip install flask flask-socketio simple-websocket pystray Pillow zeroconf qrcode pyinstaller
if %errorlevel% neq 0 (
    echo [ERROR] pip install failed.
    exit /b 1
)

:: Clean previous builds
echo [2/4] Cleaning previous builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

:: Create icon (if not exists)
if not exist icon.png (
    echo [3/4] Creating icon...
    python -c "from PIL import Image; img=Image.new('RGBA',(256,256),(108,92,231,255)); img.save('icon.png')"
)

:: PyInstaller
echo [4/4] Building executable (this may take a few minutes)...
pyinstaller --onefile --noconsole --name LANITS ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --add-data "uploads;uploads" ^
    --add-data "clipboard_files;clipboard_files" ^
    --hidden-import flask_socketio ^
    --hidden-import engineio.async_drivers.threading ^
    --hidden-import pystray ^
    --hidden-import PIL._tkinter_finder ^
    --icon icon.png ^
    app.py

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo Build SUCCESS!
    echo Output: dist\LANITS.exe
    echo.
    echo Run: dist\LANITS.exe
    echo Or:  dist\LANITS.exe --mode client --connect http://SERVER_IP:9527
    echo ========================================
) else (
    echo [ERROR] Build failed.
    exit /b 1
)
