@echo off
chcp 65001 >nul
title LANITS - 创建桌面快捷方式
echo ========================================
echo   创建 LANITS 桌面快捷方式
echo ========================================
echo.

if not exist "%~dp0dist\LANITS.exe" (
    echo [ERROR] 未找到 dist\LANITS.exe，请先运行 build.bat 编译
    pause
    exit /b 1
)

powershell -Command ^
    "$ws = New-Object -ComObject WScript.Shell; ^
     $sc = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\LANITS.lnk'); ^
     $sc.TargetPath = '%~dp0dist\LANITS.exe'; ^
     $sc.WorkingDirectory = '%~dp0'; ^
     $sc.Description = 'LANITS - 局域网信息中转站'; ^
     $sc.IconLocation = '%~dp0dist\LANITS.exe, 0'; ^
     $sc.Save()"

if %errorlevel% equ 0 (
    echo   快捷方式已创建到桌面：LANITS.lnk
) else (
    echo [ERROR] 创建失败，请以管理员身份运行
)

pause
