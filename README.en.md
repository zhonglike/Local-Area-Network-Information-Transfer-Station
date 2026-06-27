<div align="right">
  <b>🌐 English</b> | <a href="README.md">🇨🇳 中文</a>
</div>

# ⚡ LANITS — Local Area Network Information Transfer Station

> Copy on PC, auto on phone. Copy on phone, auto on PC. 📋 Send images, videos, ZIP, DOCX at full LAN speed. 🔥

---

## ✨ Features

- **📋 Bi-directional Clipboard Sync** — Copy on any device, auto-pasted on all others
- **📁 Universal File Transfer** — Images, videos, ZIP, DOCX, PDF — no limits, no compression
- **🔄 Clipboard History** — Every text & image saved, browse & re-copy anytime
- **🌐 Zero Configuration** — mDNS auto-discovery, QR connect, no account needed
- **🔒 100% Local** — Data never leaves your LAN. Open source (MIT)

## 🚀 Quick Start

### Windows (Server)

**Option 1 (recommended)** — Double-click `一键启动.bat` to start the server, create desktop shortcut, and open browser
**Option 2** — Double-click `创建快捷方式.bat` to create a desktop shortcut for LANITS

Once started, the address `http://your-ip:9527` is shown — scan the QR code from any device.

### Android

Option 1: Scan QR → tap "Download APK" in the web UI
Option 2: Download [LANITS.apk]() and install

Open the app — it auto-scans for LANITS servers on your network. Tap to connect and start syncing.

### Multi-Device

| Scenario | How |
|----------|-----|
| 1 PC + multiple phones | PC runs server, phones connect via browser or app |
| 2 Windows PCs | PC-A runs server, PC-B: `LANITS.exe --mode client --connect http://PC-A:9527` |

## 🛠 Manual Run

```bash
pip install -r requirements.txt
python app.py                       # server mode
python app.py --mode client --connect http://192.168.1.100:9527   # client mode
```

## 📦 Structure

```
├── 一键启动.bat             # One-click start + desktop shortcut
├── 创建快捷方式.bat          # Create desktop shortcut only
├── app.py                  # Core (Flask + WebSocket + dual mode)
├── tray.py                 # System tray
├── zeroconf_service.py     # mDNS auto-discovery
├── static/                 # Web frontend (APK download included)
├── templates/              # HTML templates
├── android/                # Android app source
└── installer/              # Windows installer script
```

## 📝 License

MIT
