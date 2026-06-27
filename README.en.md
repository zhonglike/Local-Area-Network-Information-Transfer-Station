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

1. Download [LANITS_Setup.exe]() and install
2. Run — the address `http://your-ip:9527` is shown
3. Open browser on any LAN device to connect

### Android

1. Download [LANITS.apk]()
2. Open — auto-scans for LANITS servers on your network
3. Tap to connect and start syncing

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
├── app.py                  # Core (Flask + WebSocket + dual mode)
├── tray.py                 # System tray
├── zeroconf_service.py     # mDNS auto-discovery
├── static/                 # Web frontend
├── templates/              # HTML templates
├── android/                # Android app source
└── installer/              # Windows installer script
```

## 📝 License

MIT
