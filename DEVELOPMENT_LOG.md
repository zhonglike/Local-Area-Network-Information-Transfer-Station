# LANITS 开发日志

## 2026-06-27

### [1/9] 项目初始化 + 日志系统 ✅
### [2/9] app.py 重构 — WebSocket + 双模式 ✅
### [3/9] clipboard_monitor ✅
### [4/9] tray.py + zeroconf_service.py ✅
### [5/9] 前端重构 ✅
### [6/9] Android App ✅
### [7/9] 前端增强 ✅
### [8/9] 打包分发 ✅
### [9/9] 文档 + 开源 ✅

## 2026-06-28

### 打包问题排查
- Python 3.14 (全局) 的 pip install 卡死（疑似 Windows 内核挂起 pip 线程）
- PyInstaller 已通过 pip list 安装但模块无法 import（`ModuleNotFoundError: No module named 'PyInstaller'`）
- 从 PyPI 手动下载 whl 并解压到 site-packages，仍无法导入
- 已下载 Python 3.12.10 并安装到 `%LOCALAPPDATA%\Programs\Python\Python312`
- Python 3.12 缺少 pip（`No module named pip`）
- 已下载 `get-pip.py` 到 `%TEMP%\get-pip.py`，但尚未确认 pip 是否安装成功
- 用户即将重启电脑

### 重启后待办
1. 确认 Python 3.12 pip 可用：`python3.12 -m pip --version`
2. 安装依赖：`python3.12 -m pip install pyinstaller flask flask-socketio simple-websocket pystray Pillow zeroconf qrcode[pil]`
3. 执行 build.bat 或手动运行 pyinstaller 打包
4. 若 pyinstaller 打包成功，将 `dist/LANITS.exe` 交给用户

### 项目文件清单（37 files）
```
E:\Information_transfer_station\
├── app.py                     # 主程序 (Flask + WebSocket + 双模式)
├── tray.py                    # 系统托盘
├── zeroconf_service.py        # mDNS 广播
├── build.bat                  # PyInstaller 打包脚本
├── requirements.txt           # Python 依赖
├── .gitignore
├── LICENSE (MIT)
├── README.md / README.en.md
├── DEVELOPMENT_LOG.md
├── icon.png
├── static/
│   ├── css/style.css
│   └── js/main.js
├── templates/index.html
├── uploads/.gitkeep
├── clipboard_files/.gitkeep
├── installer/setup.nsi        # NSIS 安装包脚本
└── android/                   # Android App 源码 (9 files)
    ├── build.gradle.kts
    ├── settings.gradle.kts
    ├── gradle.properties
    ├── gradle/wrapper/gradle-wrapper.properties
    └── app/
        ├── build.gradle.kts
        ├── proguard-rules.pro
        └── src/main/
            ├── AndroidManifest.xml
            ├── java/com/lants/app/
            │   ├── MainActivity.java
            │   ├── DiscoveryActivity.java
            │   └── ClipboardSyncService.java
            └── res/
                ├── drawable/ (ic_launcher_foreground/background)
                ├── mipmap-anydpi-v26/ic_launcher.xml
                ├── layout/activity_main.xml, activity_discovery.xml
                └── values/colors.xml, strings.xml, themes.xml
```
