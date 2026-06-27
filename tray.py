"""System tray icon for LANITS server/client."""

import threading
import webbrowser
import os
import sys
import tempfile

def run_tray(mode='server', url='http://127.0.0.1:9527'):
    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError:
        print('[TRAY] pystray or Pillow not available')
        return

    icon_size = 64
    img = Image.new('RGBA', (icon_size, icon_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw a simple bolt icon
    bolt_points = [(32, 4), (16, 36), (28, 36), (24, 60), (48, 26), (34, 26), (38, 4)]
    draw.polygon(bolt_points, fill=(108, 92, 231, 255))

    def on_open(icon, item):
        webbrowser.open(url)

    def on_show_ip(icon, item):
        from app import get_local_ip
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, f'Server address: http://{get_local_ip()}:9527\n\nOpen this on your phone browser.', 'LANITS', 0)

    def on_exit(icon, item):
        icon.stop()
        os._exit(0)

    menu = pystray.Menu(
        pystray.MenuItem(f'🌐 Open Browser', on_open, default=True),
        pystray.MenuItem(f'📡 Show IP', on_show_ip),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(f'🚪 Exit', on_exit),
    )

    title = f'LANITS ({mode})' if mode != 'server' else 'LANITS'

    icon = pystray.Icon('LANITS', img, title, menu)
    icon.run()
