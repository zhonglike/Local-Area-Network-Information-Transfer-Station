import os, sys, json, sqlite3, time, uuid, base64, mimetypes, socket, argparse, threading, ctypes, ctypes.wintypes, io, struct, queue
from datetime import datetime, timedelta
from pathlib import Path

import flask
from flask import Flask, request, jsonify, render_template, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room
from werkzeug.utils import secure_filename
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
CLIPBOARD_FOLDER = os.path.join(BASE_DIR, 'clipboard_files')
DATABASE = os.path.join(BASE_DIR, 'data.db')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CLIPBOARD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lanits-secret-key'
sio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

# ── Database ──────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS clipboard (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL CHECK(type IN ('text','image','file')),
            content TEXT,
            file_path TEXT,
            file_name TEXT,
            file_size INTEGER DEFAULT 0,
            mime_type TEXT,
            created_at REAL NOT NULL,
            expires_at REAL
        );
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY,
            original_name TEXT NOT NULL,
            stored_name TEXT NOT NULL,
            size INTEGER NOT NULL,
            mime_type TEXT,
            created_at REAL NOT NULL,
            expires_at REAL,
            download_count INTEGER DEFAULT 0
        );
    ''')
    conn.commit(); conn.close()
init_db()

# ── Helpers ────────────────────────────────────────────────────────
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]; s.close(); return ip
    except: return '127.0.0.1'

def clean_expired():
    conn = get_db(); now = time.time()
    for row in conn.execute('SELECT id, file_path FROM clipboard WHERE expires_at IS NOT NULL AND expires_at < ?', (now,)):
        if row['file_path'] and os.path.exists(row['file_path']):
            try: os.remove(row['file_path'])
            except: pass
    conn.execute('DELETE FROM clipboard WHERE expires_at IS NOT NULL AND expires_at < ?', (now,))
    for row in conn.execute('SELECT stored_name FROM files WHERE expires_at IS NOT NULL AND expires_at < ?', (now,)):
        fp = os.path.join(UPLOAD_FOLDER, row['stored_name'])
        if os.path.exists(fp):
            try: os.remove(fp)
            except: pass
    conn.execute('DELETE FROM files WHERE expires_at IS NOT NULL AND expires_at < ?', (now,))
    conn.commit(); conn.close()
clean_expired()

def api_ok(data=None, msg=''):
    return jsonify({'ok': True, 'data': data, 'msg': msg})

def api_err(msg, code=400):
    return jsonify({'ok': False, 'msg': msg}), code

# ── WebSocket ──────────────────────────────────────────────────────
@sio.on('connect', namespace='/ws')
def ws_connect(auth=None):
    print(f'[WS] client connected: {request.sid}')

@sio.on('disconnect', namespace='/ws')
def ws_disconnect():
    print(f'[WS] client disconnected: {request.sid}')

@sio.on('join', namespace='/ws')
def ws_join(data):
    room = data.get('room', 'broadcast')
    join_room(room)
    print(f'[WS] {request.sid} joined room {room}')

def broadcast_clipboard(item):
    """Broadcast clipboard update to all WebSocket clients."""
    data = dict(item) if item else None
    sio.emit('clipboard_update', data, namespace='/ws')

def broadcast_file_upload(file_info):
    sio.emit('file_uploaded', file_info, namespace='/ws')

# ── Clipboard Monitor (ctypes) ────────────────────────────────────
CF_UNICODETEXT = 13

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Set proper argtypes for clipboard functions
user32.OpenClipboard.argtypes = [ctypes.c_void_p]
user32.OpenClipboard.restype = ctypes.c_int
user32.CloseClipboard.argtypes = []
user32.CloseClipboard.restype = ctypes.c_int
user32.EmptyClipboard.argtypes = []
user32.EmptyClipboard.restype = ctypes.c_int
user32.GetClipboardData.argtypes = [ctypes.c_uint]
user32.GetClipboardData.restype = ctypes.c_void_p
user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
user32.SetClipboardData.restype = ctypes.c_void_p
kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = ctypes.c_void_p
kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
kernel32.GlobalUnlock.restype = ctypes.c_int
kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
kernel32.GlobalFree.restype = ctypes.c_void_p

def read_clipboard_text():
    if not user32.OpenClipboard(0):
        return None
    try:
        handle = user32.GetClipboardData(CF_UNICODETEXT)
        if not handle:
            return None
        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            return None
        try:
            return ctypes.wstring_at(ptr)
        finally:
            kernel32.GlobalUnlock(handle)
    except:
        return None
    finally:
        user32.CloseClipboard()

def write_clipboard_text(text):
    if not user32.OpenClipboard(0):
        return False
    try:
        user32.EmptyClipboard()
        buffer = (text + '\0').encode('utf-16-le')
        handle = kernel32.GlobalAlloc(0x42, len(buffer))
        if not handle:
            return False
        ptr = kernel32.GlobalLock(handle)
        if not ptr:
            kernel32.GlobalFree(handle)
            return False
        try:
            ctypes.memmove(ptr, buffer, len(buffer))
        finally:
            kernel32.GlobalUnlock(handle)
        user32.SetClipboardData(CF_UNICODETEXT, handle)
        return True
    except:
        return False
    finally:
        user32.CloseClipboard()

_monitor_running = False
_last_clipboard_text = None

def start_clipboard_monitor(callback):
    """Poll-based clipboard monitor - simple, reliable, no Win32 window needed."""
    global _monitor_running, _clipboard_thread
    if _monitor_running:
        return
    _monitor_running = True

    def _poll():
        global _last_clipboard_text
        while _monitor_running:
            try:
                text = read_clipboard_text()
                if text is not None and text != _last_clipboard_text:
                    _last_clipboard_text = text
                    callback(text)
            except:
                pass
            time.sleep(0.5)

    _clipboard_thread = threading.Thread(target=_poll, daemon=True)
    _clipboard_thread.start()

def stop_clipboard_monitor():
    global _monitor_running
    _monitor_running = False

# ── REST API Routes ──────────────────────────────────────────────
@app.route('/')
def index():
    ip = get_local_ip()
    return render_template('index.html', server_ip=ip, port=9527)

@app.route('/api/info')
def api_info():
    return api_ok({
        'server_ip': get_local_ip(),
        'port': 9527,
        'server_name': socket.gethostname(),
        'uptime': time.time()
    })

@app.route('/api/clipboard', methods=['POST'])
def add_clipboard():
    try:
        data = request.get_json()
        if not data: return api_err('Invalid request')
        clip_type = data.get('type', 'text')
        content = data.get('content', '')
        expire_hours = data.get('expire_hours', 24)
        clip_id = str(uuid.uuid4())
        now = time.time()
        expires_at = now + (expire_hours * 3600) if expire_hours > 0 else None
        file_path = file_name = mime_type = None
        file_size = 0

        if clip_type == 'image' and content:
            try:
                header, encoded = content.split(',', 1)
                mime_type = header.split(';')[0].split(':')[1] if ':' in header else 'image/png'
                ext = { 'image/jpeg': '.jpg', 'image/gif': '.gif', 'image/webp': '.webp', 'image/png': '.png' }.get(mime_type, '.png')
                file_name = f'clip_{clip_id}{ext}'
                file_path = os.path.join(CLIPBOARD_FOLDER, file_name)
                with open(file_path, 'wb') as f: f.write(base64.b64decode(encoded))
                file_size = os.path.getsize(file_path)
                content = None
            except Exception as e:
                return api_err(f'Image decode failed: {str(e)}')

        conn = get_db()
        conn.execute('INSERT INTO clipboard (id,type,content,file_path,file_name,file_size,mime_type,created_at,expires_at) VALUES (?,?,?,?,?,?,?,?,?)',
                     (clip_id, clip_type, content, file_path, file_name, file_size, mime_type, now, expires_at))
        conn.commit()
        row = conn.execute('SELECT * FROM clipboard WHERE id=?', (clip_id,)).fetchone()
        conn.close()

        broadcast_clipboard(dict(row))
        # Also write to local clipboard if text
        if clip_type == 'text' and content:
            try: write_clipboard_text(content)
            except: pass
        return api_ok({'id': clip_id, 'type': clip_type})
    except Exception as e:
        return api_err(str(e), 500)

@app.route('/api/clipboard/latest')
def get_latest_clipboard():
    clean_expired()
    conn = get_db()
    row = conn.execute('SELECT * FROM clipboard ORDER BY created_at DESC LIMIT 1').fetchone()
    conn.close()
    return api_ok(dict(row) if row else None)

@app.route('/api/clipboard/history')
def get_clipboard_history():
    clean_expired()
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    t = request.args.get('type')
    conn = get_db()
    if t: rows = conn.execute('SELECT * FROM clipboard WHERE type=? ORDER BY created_at DESC LIMIT ? OFFSET ?', (t, limit, offset)).fetchall()
    else: rows = conn.execute('SELECT * FROM clipboard ORDER BY created_at DESC LIMIT ? OFFSET ?', (limit, offset)).fetchall()
    conn.close()
    return api_ok([dict(r) for r in rows])

@app.route('/api/clipboard/<clip_id>', methods=['GET','DELETE'])
def handle_clipboard_item(clip_id):
    conn = get_db()
    if request.method == 'DELETE':
        row = conn.execute('SELECT * FROM clipboard WHERE id=?', (clip_id,)).fetchone()
        if not row: conn.close(); return api_err('Not found', 404)
        if row['file_path'] and os.path.exists(row['file_path']):
            try: os.remove(row['file_path'])
            except: pass
        conn.execute('DELETE FROM clipboard WHERE id=?', (clip_id,))
        conn.commit(); conn.close()
        return api_ok(msg='Deleted')
    row = conn.execute('SELECT * FROM clipboard WHERE id=?', (clip_id,)).fetchone()
    conn.close()
    if not row: return api_err('Not found', 404)
    return api_ok(dict(row))

@app.route('/api/clipboard', methods=['DELETE'])
def clear_clipboard():
    conn = get_db()
    for r in conn.execute('SELECT file_path FROM clipboard WHERE file_path IS NOT NULL'):
        if r['file_path'] and os.path.exists(r['file_path']):
            try: os.remove(r['file_path'])
            except: pass
    conn.execute('DELETE FROM clipboard')
    conn.commit(); conn.close()
    return api_ok(msg='Cleared')

@app.route('/api/clipboard/file/<clip_id>')
def get_clipboard_file(clip_id):
    conn = get_db()
    row = conn.execute('SELECT * FROM clipboard WHERE id=?', (clip_id,)).fetchone()
    conn.close()
    if not row or not row['file_path']: return api_err('Not found', 404)
    return send_file(row['file_path'], mimetype=row['mime_type'] or 'application/octet-stream')

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files: return api_err('No file')
    f = request.files['file']
    if f.filename == '': return api_err('No file selected')
    expire_hours = request.form.get('expire_hours', 24, type=int)
    original_name = secure_filename(f.filename) or f.filename
    file_id = str(uuid.uuid4())
    ext = os.path.splitext(original_name)[1] or '.bin'
    stored_name = f'{file_id}{ext}'
    f.save(os.path.join(UPLOAD_FOLDER, stored_name))
    file_size = os.path.getsize(os.path.join(UPLOAD_FOLDER, stored_name))
    mime_type, _ = mimetypes.guess_type(original_name)
    now = time.time()
    expires_at = now + (expire_hours * 3600) if expire_hours > 0 else None
    conn = get_db()
    conn.execute('INSERT INTO files (id,original_name,stored_name,size,mime_type,created_at,expires_at) VALUES (?,?,?,?,?,?,?)',
                 (file_id, original_name, stored_name, file_size, mime_type, now, expires_at))
    conn.commit(); conn.close()
    info = {'id': file_id, 'original_name': original_name, 'size': file_size, 'mime_type': mime_type, 'expires_at': expires_at}
    broadcast_file_upload(info)
    return api_ok(info)

@app.route('/api/files')
def list_files():
    clean_expired()
    conn = get_db()
    rows = conn.execute('SELECT * FROM files ORDER BY created_at DESC').fetchall()
    conn.close()
    return api_ok([dict(r) for r in rows])

@app.route('/api/files/<file_id>', methods=['GET'])
def get_file_info(file_id):
    conn = get_db()
    row = conn.execute('SELECT * FROM files WHERE id=?', (file_id,)).fetchone()
    conn.close()
    if not row: return api_err('Not found', 404)
    return api_ok(dict(row))

@app.route('/api/files/<file_id>/download')
def download_file(file_id):
    conn = get_db()
    row = conn.execute('SELECT * FROM files WHERE id=?', (file_id,)).fetchone()
    if not row: conn.close(); return api_err('Not found', 404)
    conn.execute('UPDATE files SET download_count=download_count+1 WHERE id=?', (file_id,))
    conn.commit(); conn.close()
    fp = os.path.join(UPLOAD_FOLDER, row['stored_name'])
    if not os.path.exists(fp): return api_err('File not on disk', 404)
    return send_file(fp, mimetype=row['mime_type'] or 'application/octet-stream', as_attachment=True, download_name=row['original_name'])

@app.route('/api/files/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    conn = get_db()
    row = conn.execute('SELECT * FROM files WHERE id=?', (file_id,)).fetchone()
    if not row: conn.close(); return api_err('Not found', 404)
    fp = os.path.join(UPLOAD_FOLDER, row['stored_name'])
    if os.path.exists(fp): os.remove(fp)
    conn.execute('DELETE FROM files WHERE id=?', (file_id,))
    conn.commit(); conn.close()
    return api_ok(msg='Deleted')

@app.route('/api/files', methods=['DELETE'])
def clear_files():
    conn = get_db()
    for r in conn.execute('SELECT stored_name FROM files'):
        fp = os.path.join(UPLOAD_FOLDER, r['stored_name'])
        if os.path.exists(fp): os.remove(fp)
    conn.execute('DELETE FROM files')
    conn.commit(); conn.close()
    return api_ok(msg='All files cleared')

# ── Clipboard Monitor Callback ─────────────────────────────────────
_last_clipboard_text = None

def _on_clipboard_changed(text):
    print(f'[CLIP] Detected: {text[:80]}...')
    # Save to DB and broadcast
    clip_id = str(uuid.uuid4())
    now = time.time()
    conn = get_db()
    conn.execute('INSERT INTO clipboard (id,type,content,created_at,expires_at) VALUES (?,?,?,?,?)',
                 (clip_id, 'text', text, now, None))
    conn.commit()
    row = conn.execute('SELECT * FROM clipboard WHERE id=?', (clip_id,)).fetchone()
    conn.close()
    broadcast_clipboard(dict(row))

# ── Server Mode ────────────────────────────────────────────────────
def run_server(port=9527, with_tray=True, with_monitor=True):
    """Start in server mode: Flask + WebSocket + optional clipboard monitor + tray."""
    if with_monitor:
        print('[CLIP] Starting clipboard monitor...')
        start_clipboard_monitor(_on_clipboard_changed)

    if with_tray:
        try:
            from tray import run_tray
            threading.Thread(target=run_tray, args=('server', f'http://{get_local_ip()}:{port}'), daemon=True).start()
        except ImportError:
            print('[TRAY] tray.py not found, skipping')

    banner = f'''
    ╔══════════════════════════════════════════════════╗
    ║       LANITS — Local Area Network Info Transfer  ║
    ║                                                  ║
    ║   Server:  http://{get_local_ip()}:{port}                 ║
    ║   Local:   http://127.0.0.1:{port}                     ║
    ║                                                  ║
    ║   Open browser on any device to connect          ║
    ╚══════════════════════════════════════════════════╝
    '''
    print(banner)
    sio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)

# ── Client Mode ────────────────────────────────────────────────────
def run_client(server_url):
    """Start in client mode: connect to remote server, monitor local clipboard."""
    import socketio as sio_client_lib

    print(f'[CLIENT] Connecting to server: {server_url}')
    ws_url = server_url.replace('http://', 'http://').replace('https://', 'https://')

    def _write_to_pc_clipboard(text):
        try:
            write_clipboard_text(text)
            print(f'[CLIENT] Written to local clipboard: {text[:50]}...')
        except Exception as e:
            print(f'[CLIENT] Write clipboard error: {e}')

    def _on_remote_clipboard(data):
        if data and data.get('type') == 'text':
            _write_to_pc_clipboard(data['content'])

    sio_client = sio_client_lib.Client()
    sio_client.on('clipboard_update', _on_remote_clipboard)

    connected = threading.Event()

    @sio_client.on('connect')
    def on_connect():
        print(f'[CLIENT] Connected to server')
        connected.set()

    @sio_client.on('disconnect')
    def on_disconnect():
        print(f'[CLIENT] Disconnected')
        connected.clear()

    def _local_clipboard_cb():
        text = read_clipboard_text()
        if text:
            # Send to server via REST API
            import urllib.request
            data = json.dumps({'type': 'text', 'content': text, 'expire_hours': 24}).encode()
            try:
                req = urllib.request.Request(f'{server_url}/api/clipboard', data=data,
                    headers={'Content-Type': 'application/json'}, method='POST')
                urllib.request.urlopen(req, timeout=5)
            except:
                pass

    def _connect_and_wait():
        try:
            sio_client.connect(ws_url, wait_timeout=10)
        except Exception as e:
            print(f'[CLIENT] Connection failed: {e}')
            connected.set()  # don't block

    threading.Thread(target=_connect_and_wait, daemon=True).start()
    connected.wait(timeout=10)

    start_clipboard_monitor(_local_clipboard_cb)

    try:
        from tray import run_tray
        threading.Thread(target=run_tray, args=('client', server_url), daemon=True).start()
    except ImportError:
        pass

    print(f'[CLIENT] LANITS client running. Connected to {server_url}')
    print('[CLIENT] Press Ctrl+C to exit.')

    # Keep alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('[CLIENT] Shutting down...')
        sio_client.disconnect()
        stop_clipboard_monitor()

# ── Entry Point ────────────────────────────────────────────────────
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='LANITS — Local Area Network Information Transfer Station')
    parser.add_argument('--mode', choices=['server', 'client'], default='server', help='Run mode')
    parser.add_argument('--connect', default=None, help='Server URL for client mode (e.g. http://192.168.1.100:9527)')
    parser.add_argument('--port', type=int, default=9527, help='Server port (default: 9527)')
    parser.add_argument('--no-tray', action='store_true', help='Disable system tray')
    parser.add_argument('--no-monitor', action='store_true', help='Disable clipboard monitor')
    args = parser.parse_args()

    if args.mode == 'server':
        run_server(port=args.port, with_tray=not args.no_tray, with_monitor=not args.no_monitor)
    else:
        if not args.connect:
            print('[ERROR] Client mode requires --connect <server_url>')
            sys.exit(1)
        run_client(args.connect)
