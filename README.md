<div align="right">
  <a href="README.en.md">🌐 English</a> | <b>🇨🇳 中文</b>
</div>

# ⚡ LANITS — 局域网信息中转站

> **L**ocal **A**rea **N**etwork **I**nformation **T**ransfer **S**tation

在电脑上复制 → 手机自动收到 📋 在手机上复制 → 电脑自动获取 🔥 发送图片、视频、ZIP、DOCX，局域网满速不压缩。

---

## ✨ 功能

- **📋 双向剪贴板同步** — 任一设备复制，其他设备实时同步
- **📁 全类型文件传输** — 图片 / 视频 / ZIP / DOCX / PDF，不压缩不限速
- **🔄 剪贴板历史** — 所有文字图片自动保存，可回溯
- **🌐 零配置** — mDNS 自动发现，扫码即连，无需账号
- **🔒 完全本地** — 数据不出局域网，MIT 开源协议

## 🚀 快速开始

### Windows 服务端

**方式一（推荐）** — 双击 `一键启动.bat`，自动启动服务 + 创建桌面快捷方式 + 打开浏览器
**方式二** — 双击 `创建快捷方式.bat`，在桌面生成 LANITS 快捷方式

启动后，地址栏显示 `http://你的IP:9527`，手机扫码即连。

### Android 手机

方式一：扫码打开网页 → 点「下载 APK」直接安装
方式二：下载 [LANITS.apk]() 并安装

打开 App，自动扫描局域网内的 LANITS 服务器，连接后即可同步剪贴板和传输文件。

### 多设备场景

| 场景 | 方法 |
|------|------|
| 一台 PC + 多台手机 | PC 运行服务端，手机连接即可 |
| 两台 Windows PC | PC-A 运行服务端，PC-B 运行 `LANITS.exe --mode client --connect http://PC-A:9527` |

## 🛠 手动运行

```bash
pip install -r requirements.txt
python app.py                       # 服务端模式
python app.py --mode client --connect http://192.168.1.100:9527   # 客户端模式
```

## 📦 项目结构

```
├── 一键启动.bat             # Windows 一键启动 + 创建快捷方式
├── 创建快捷方式.bat          # 单独创建桌面快捷方式
├── app.py                  # 主程序（Flask + WebSocket + 双模式）
├── tray.py                 # 系统托盘
├── zeroconf_service.py     # mDNS 自动发现
├── static/                 # Web 前端（含 APK 下载）
├── templates/              # HTML 模板
├── android/                # Android App 源码
└── installer/              # Windows 安装包脚本
```

## 📝 开源协议

MIT License
