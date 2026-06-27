@echo off
chcp 65001 >nul
title LANITS - 局域网信息中转站
echo ========================================
echo   LANITS - 一键启动
echo ========================================
echo.

:: Check if exe exists
if exist "%~dp0dist\LANITS.exe" (
    set EXE=%~dp0dist\LANITS.exe
) else (
    echo [INFO] 未找到编译版，使用 Python 运行...
    where python >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] 未找到 Python，请安装 Python 3.8+
        pause
        exit /b 1
    )
    set EXE=python "%~dp0app.py"
)

:: Create desktop shortcut (powershell)
echo [1/2] 创建桌面快捷方式...
powershell -Command ^
    "$ws = New-Object -ComObject WScript.Shell; ^
     $sc = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\LANITS.lnk'); ^
     $sc.TargetPath = '%~dp0dist\LANITS.exe'; ^
     $sc.WorkingDirectory = '%~dp0'; ^
     $sc.Description = 'LANITS - 局域网信息中转站'; ^
     $sc.Save(); ^
     Write-Host '  快捷方式已创建到桌面'"
if %errorlevel% neq 0 (
    echo   [WARN] 快捷方式创建失败（可忽略）
)

:: Start server
echo [2/2] 启动服务器...
start "" %EXE%

:: Open browser
timeout /t 2 /nobreak >nul
start http://127.0.0.1:9527

echo.
echo ========================================
echo   服务已启动！
echo   浏览器已打开：http://127.0.0.1:9527
echo   手机扫码即可连接
echo ========================================
echo.
pause
