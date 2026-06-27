// ── State ──
let serverInfo = null;
let latestClipboardId = null;
let historyOffset = 0;
let historyType = 'all';
let isLoadingHistory = false;
let isDarkTheme = true;
let socket = null;
let qrCodeInstance = null;

// ── Init ──
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initDropZone();
    initPaste();
    initServerInfo();
    initWebSocket();
    initAutoRefresh();
    initFilterButtons();
    loadTheme();
});

// ── Server Info ──
function initServerInfo() {
    fetch('/api/info').then(r=>r.json()).then(res => {
        if (res.ok) {
            serverInfo = res.data;
            const addr = `${serverInfo.server_ip}:${serverInfo.port}`;
            document.getElementById('serverAddress').textContent = addr;
            document.title = `LANITS - ${addr}`;
            generateQR(`http://${addr}`);
            if (res.data.apk_size > 0) {
                document.getElementById('apkDownloadBtn').style.display = '';
            }
        }
    }).catch(() => {
        document.getElementById('serverAddress').textContent = '无法连接';
    });
}

function copyServerAddress() {
    const addr = document.getElementById('serverAddress').textContent;
    if (addr && addr !== '连接中...' && addr !== '无法连接') {
        navigator.clipboard.writeText(`http://${addr}`).then(() => toast('已复制地址', 'success'));
    }
}

// ── WebSocket ──
function initWebSocket() {
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${proto}//${window.location.host}`;
    try {
        socket = io(wsUrl, { path: '/socket.io', transports: ['websocket', 'polling'] });

        socket.on('connect', () => {
            console.log('[WS] Connected');
            document.getElementById('statusDot').className = 'status-dot connected';
            socket.emit('join', { room: 'broadcast' }, '/ws');
        });

        socket.on('disconnect', () => {
            console.log('[WS] Disconnected');
            document.getElementById('statusDot').className = 'status-dot';
        });

        socket.on('clipboard_update', (data) => {
            console.log('[WS] Clipboard update:', data?.type);
            if (data) {
                displayLatestClipboard(data);
                // Auto-copy text to system clipboard
                if (data.type === 'text' && data.content) {
                    copyToClipboard(data.content);
                }
            }
        });

        socket.on('file_uploaded', (data) => {
            console.log('[WS] File uploaded:', data?.original_name);
            if (document.getElementById('tab-files').classList.contains('active')) {
                refreshFiles();
            }
            toast(`📁 ${data?.original_name || 'File'} uploaded`, 'success');
        });

        socket.on('connect_error', (err) => {
            console.log('[WS] Error:', err.message);
        });
    } catch (e) {
        console.log('[WS] Init error:', e);
    }
}

function copyToClipboard(text) {
    if (!text) return;
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).catch(() => {});
    }
}

// ── QR Code ──
function generateQR(url) {
    const container = document.getElementById('qrcode');
    if (!container) return;
    container.innerHTML = '';
    try {
        qrCodeInstance = new QRCode(container, {
            text: url,
            width: 180,
            height: 180,
            colorDark: '#6c5ce7',
            colorLight: '#ffffff',
            correctLevel: QRCode.CorrectLevel.H
        });
    } catch(e) { console.log('[QR] Error:', e); }
}

function showQR() {
    const modal = document.getElementById('qrModal');
    modal.classList.add('active');
    const addr = document.getElementById('serverAddress').textContent;
    document.getElementById('qrAddress').textContent = `http://${addr}`;
    if (qrCodeInstance) {
        qrCodeInstance.clear();
        qrCodeInstance.makeCode(`http://${addr}`);
    }
}

function closeQR() {
    document.getElementById('qrModal').classList.remove('active');
}

// ── Tabs ──
function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            btn.classList.add('active');
            const tab = btn.dataset.tab;
            document.getElementById(`tab-${tab}`).classList.add('active');
            if (tab === 'files') refreshFiles();
            if (tab === 'history') refreshHistory();
        });
    });
}

// ── Drop Zone ──
function initDropZone() {
    const zone = document.getElementById('dropZone');
    const input = document.getElementById('fileInput');
    zone.addEventListener('click', () => input.click());
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag-over'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
    zone.addEventListener('drop', e => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files);
    });
}

// ── Paste ──
function initPaste() {
    document.getElementById('textInput').addEventListener('paste', (e) => {
        for (const item of e.clipboardData.items) {
            if (item.type.startsWith('image/')) {
                e.preventDefault();
                const file = item.getAsFile();
                if (file) sendImageFile(file);
                return;
            }
        }
    });
}

// ── Auto Refresh ──
function initAutoRefresh() {
    refreshLatest();
    setInterval(refreshLatest, 3000);
}

// ── Filters ──
function initFilterButtons() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            historyType = btn.dataset.filter;
            historyOffset = 0;
            refreshHistory();
        });
    });
}

// ── Toast ──
function toast(msg, type='info') {
    const c = document.getElementById('toastContainer');
    const icons = { success:'check-circle', error:'times-circle', warning:'exclamation-circle', info:'info-circle' };
    const t = document.createElement('div');
    t.className = `toast ${type}`;
    t.innerHTML = `<i class="fas fa-${icons[type]||icons.info}"></i> ${msg}`;
    c.appendChild(t);
    setTimeout(() => { t.classList.add('removing'); setTimeout(() => t.remove(), 300); }, 2500);
}

// ── API ──
async function api(path, opts={}) {
    try {
        const r = await fetch(path, { headers:{'Accept':'application/json'}, ...opts });
        return await r.json();
    } catch(e) { toast(`网络错误: ${e.message}`, 'error'); return null; }
}

// ══════════ Clipboard ══════════
function sendText() {
    const input = document.getElementById('textInput');
    const text = input.value.trim();
    if (!text) { toast('请输入文字', 'warning'); return; }
    const expire = parseInt(document.getElementById('clipExpire').value);
    api('/api/clipboard', { method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({ type:'text', content:text, expire_hours:expire })
    }).then(res => {
        if (res && res.ok) { toast('已发送', 'success'); input.value = ''; }
    });
}

function sendImage(event) {
    const file = event.target.files[0];
    if (file) sendImageFile(file);
    event.target.value = '';
}

function sendImageFile(file) {
    if (!file.type.startsWith('image/')) { toast('请选择图片', 'warning'); return; }
    const reader = new FileReader();
    reader.onload = function(e) {
        const expire = parseInt(document.getElementById('clipExpire').value);
        api('/api/clipboard', { method:'POST', headers:{'Content-Type':'application/json'},
            body:JSON.stringify({ type:'image', content:e.target.result, expire_hours:expire })
        }).then(res => { if (res && res.ok) toast('图片已发送', 'success'); });
    };
    reader.readAsDataURL(file);
}

async function refreshLatest() {
    const res = await api('/api/clipboard/latest');
    if (res && res.ok && res.data) {
        displayLatestClipboard(res.data);
    }
}

function displayLatestClipboard(item) {
    const container = document.getElementById('latestClipboard');
    latestClipboardId = item.id;
    let html = '';
    if (item.type === 'text') {
        html = `<div class="clipboard-display">
            <p>${escHtml(item.content)}</p>
            <div class="clipboard-meta"><span>文字</span><span>${fmtTime(item.created_at)}</span></div>
            <div class="clipboard-actions">
                <button class="btn btn-sm" onclick="copyToClipboard('${escHtml(item.content).replace(/'/g,"\\'")}');toast('已复制','success')"><i class="fas fa-copy"></i> 复制</button>
                <button class="btn btn-sm btn-danger" onclick="delClip('${item.id}')"><i class="fas fa-trash-alt"></i></button>
            </div>
        </div>`;
    } else if (item.type === 'image') {
        const url = `/api/clipboard/file/${item.id}`;
        html = `<div class="clipboard-display">
            <img src="${url}" class="clipboard-image" onclick="previewImage('${url}')">
            <div class="clipboard-meta"><span>图片</span><span>${fmtSize(item.file_size)}</span><span>${fmtTime(item.created_at)}</span></div>
            <div class="clipboard-actions">
                <button class="btn btn-sm" onclick="previewImage('${url}')"><i class="fas fa-eye"></i></button>
                <button class="btn btn-sm" onclick="window.open('${url}')"><i class="fas fa-download"></i></button>
                <button class="btn btn-sm btn-danger" onclick="delClip('${item.id}')"><i class="fas fa-trash-alt"></i></button>
            </div>
        </div>`;
    }
    container.innerHTML = html || '<div class="empty-state"><i class="fas fa-inbox"></i><p>暂无内容</p></div>';
}

function copyLatestText() {
    const p = document.querySelector('#latestClipboard p');
    if (p) { copyToClipboard(p.textContent); toast('已复制', 'success'); }
    else toast('没有可复制的文字', 'warning');
}

function downloadLatestImage() {
    if (latestClipboardId) window.open(`/api/clipboard/file/${latestClipboardId}`);
    else toast('没有可下载的图片', 'warning');
}

function delClip(id) {
    api(`/api/clipboard/${id}`, { method:'DELETE' }).then(r => { if(r&&r.ok) { toast('已删除','success'); refreshLatest(); }});
}

function clearClipboard() {
    if (!confirm('确定清空所有剪贴板内容？')) return;
    api('/api/clipboard', { method:'DELETE' }).then(r => { if(r&&r.ok) { toast('已清空','success'); refreshLatest(); }});
}

// ══════════ Files ══════════
function uploadFiles(event) {
    if (event.target.files.length) handleFiles(event.target.files);
    event.target.value = '';
}

function handleFiles(files) {
    const expire = parseInt(document.getElementById('fileExpire').value);
    const progress = document.getElementById('uploadProgress');
    const fill = document.getElementById('progressFill');
    const txt = document.getElementById('progressText');
    progress.style.display = 'flex';
    let done = 0;
    Array.from(files).forEach((file) => {
        const fd = new FormData();
        fd.append('file', file);
        fd.append('expire_hours', expire);
        const xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/upload', true);
        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                fill.style.width = (e.loaded/e.total*100)+'%';
                txt.textContent = `${file.name}: ${Math.round(e.loaded/e.total*100)}%`;
            }
        };
        xhr.onload = () => {
            done++;
            if (xhr.status === 200) {
                const res = JSON.parse(xhr.responseText);
                if (res.ok) toast(`${file.name} 上传成功`, 'success');
                else toast(`${file.name} 失败: ${res.msg}`, 'error');
            } else toast(`${file.name} 失败 (${xhr.status})`, 'error');
            if (done === files.length) {
                setTimeout(() => { progress.style.display='none'; fill.style.width='0%'; }, 1000);
                refreshFiles();
            }
        };
        xhr.onerror = () => toast(`${file.name} 网络错误`, 'error');
        xhr.send(fd);
    });
}

async function refreshFiles() {
    const container = document.getElementById('fileList');
    const res = await api('/api/files');
    if (!res || !res.ok) return;
    if (!res.data || !res.data.length) {
        container.innerHTML = '<div class="empty-state"><i class="fas fa-folder-open"></i><p>暂无文件</p></div>';
        return;
    }
    let html = '';
    res.data.forEach(f => {
        const ic = fileIcon(f.mime_type, f.original_name);
        const isVideo = f.mime_type && f.mime_type.startsWith('video/');
        html += `<div class="file-item">
            <div class="file-icon ${ic.cls}"><i class="${ic.icon}"></i></div>
            <div class="file-info">
                <div class="file-name" title="${escHtml(f.original_name)}">${escHtml(f.original_name)}</div>
                <div class="file-meta">
                    <span>${fmtSize(f.size)}</span>
                    <span>${fmtTime(f.created_at)}</span>
                    <span>↓${f.download_count||0}</span>
                    ${f.expires_at ? `<span>${fmtTime(f.expires_at)} 过期</span>` : '<span>永久</span>'}
                </div>
            </div>
            <div class="file-actions">
                ${isVideo ? `<button class="btn btn-sm" onclick="previewVideo('/api/files/${f.id}/download','${escHtml(f.original_name)}')" title="预览"><i class="fas fa-play"></i></button>` : ''}
                <button class="btn btn-sm" onclick="window.open('/api/files/${f.id}/download')" title="下载"><i class="fas fa-download"></i></button>
                <button class="btn btn-sm btn-danger" onclick="delFile('${f.id}')" title="删除"><i class="fas fa-trash-alt"></i></button>
            </div>
        </div>`;
    });
    container.innerHTML = html;
}

function delFile(id) {
    if (!confirm('确定删除此文件？')) return;
    api(`/api/files/${id}`, { method:'DELETE' }).then(r => { if(r&&r.ok) { toast('已删除','success'); refreshFiles(); }});
}

function clearFiles() {
    if (!confirm('确定清空所有文件？')) return;
    api('/api/files', { method:'DELETE' }).then(r => { if(r&&r.ok) { toast('已清空','success'); refreshFiles(); }});
}

// ══════════ History ══════════
async function refreshHistory() { historyOffset=0; await loadHistory(true); }
function loadMoreHistory() { loadHistory(false); }

async function loadHistory(reset=true) {
    if (isLoadingHistory) return;
    isLoadingHistory = true;
    const container = document.getElementById('historyList');
    const footer = document.getElementById('historyFooter');
    if (reset) container.innerHTML = '<div style="text-align:center;padding:20px"><i class="fas fa-spinner fa-spin" style="font-size:24px;color:var(--text-muted)"></i></div>';

    let url = `/api/clipboard/history?limit=30&offset=${historyOffset}`;
    if (historyType !== 'all') url += `&type=${historyType}`;
    const res = await api(url);
    isLoadingHistory = false;
    if (!res || !res.ok) { if(reset) container.innerHTML='<div class="empty-state"><i class="fas fa-history"></i><p>加载失败</p></div>'; return; }
    if (reset) container.innerHTML = '';
    if (!res.data || !res.data.length) {
        if (reset) container.innerHTML = '<div class="empty-state"><i class="fas fa-history"></i><p>暂无历史记录</p></div>';
        footer.style.display = 'none'; return;
    }
    res.data.forEach(item => {
        const div = document.createElement('div'); div.className = 'history-item';
        const label = item.type === 'text' ? '文字' : '图片';
        let preview = '';
        if (item.type === 'text') preview = `<div class="history-preview">${escHtml(item.content||'').substring(0,200)}</div>`;
        else preview = `<div class="history-preview"><img src="/api/clipboard/file/${item.id}"></div>`;
        div.innerHTML = `<div class="history-header"><span class="history-type ${item.type}">${label}</span><span class="history-time">${fmtTime(item.created_at)}</span></div>${preview}
            <div class="history-actions">
                ${item.type==='text'?`<button class="btn btn-sm" onclick="copyToClipboard('${escHtml(item.content||'').replace(/'/g,"\\'")}');toast('已复制','success')"><i class="fas fa-copy"></i></button>`:''}
                ${item.file_path?`<button class="btn btn-sm" onclick="window.open('/api/clipboard/file/${item.id}')"><i class="fas fa-download"></i></button>`:''}
                <button class="btn btn-sm btn-danger" onclick="delClip('${item.id}')"><i class="fas fa-trash-alt"></i></button>
            </div>`;
        container.appendChild(div);
    });
    footer.style.display = res.data.length >= 30 ? 'block' : 'none';
    historyOffset += res.data.length;
}

// ══════════ Preview ══════════
function previewImage(url) {
    document.getElementById('previewContent').innerHTML = `<img src="${url}" style="max-width:100%;max-height:80vh;display:block">`;
    document.getElementById('previewModal').classList.add('active');
}

function previewVideo(url, name) {
    document.getElementById('previewContent').innerHTML = `<video controls autoplay style="max-width:100%;max-height:80vh;display:block">
        <source src="${url}"><p>您的浏览器不支持视频播放</p></video>`;
    document.getElementById('previewModal').classList.add('active');
}

function closePreview() {
    document.getElementById('previewModal').classList.remove('active');
    document.getElementById('previewContent').innerHTML = '';
}

// ══════════ Theme ══════════
function toggleTheme() {
    isDarkTheme = !isDarkTheme;
    const root = document.documentElement;
    const icon = document.querySelector('#themeToggle i');
    if (!isDarkTheme) {
        root.style.setProperty('--bg-primary','#f0f2f5'); root.style.setProperty('--bg-secondary','#ffffff');
        root.style.setProperty('--bg-card','#ffffff'); root.style.setProperty('--bg-card-hover','#f5f6fa');
        root.style.setProperty('--text-primary','#1a1a2e'); root.style.setProperty('--text-secondary','#4a4a6a');
        root.style.setProperty('--text-muted','#8e8ea0'); root.style.setProperty('--border','#e0e0e8');
        root.style.setProperty('--accent','#6c5ce7');
        icon.className = 'fas fa-sun';
    } else {
        root.style.setProperty('--bg-primary','#0f0f1a'); root.style.setProperty('--bg-secondary','#1a1a2e');
        root.style.setProperty('--bg-card','#1e1e36'); root.style.setProperty('--bg-card-hover','#252545');
        root.style.setProperty('--text-primary','#e8e8f0'); root.style.setProperty('--text-secondary','#a0a0b8');
        root.style.setProperty('--text-muted','#6e6e8a'); root.style.setProperty('--border','#2d2d4a');
        root.style.setProperty('--accent','#6c5ce7');
        icon.className = 'fas fa-moon';
    }
    localStorage.setItem('lanits_theme', isDarkTheme?'dark':'light');
}

function loadTheme() {
    if (localStorage.getItem('lanits_theme') === 'light') { isDarkTheme=false; toggleTheme(); }
}

// ══════════ Utils ══════════
function escHtml(t) { if(!t)return''; const d=document.createElement('div'); d.textContent=t; return d.innerHTML; }

function fmtSize(b) {
    if (!b||b===0) return '0 B';
    const u=['B','KB','MB','GB','TB']; const i=Math.floor(Math.log(b)/Math.log(1024));
    return (b/Math.pow(1024,i)).toFixed(i>0?1:0)+' '+u[i];
}

function fmtTime(ts) {
    if (!ts) return '';
    const d=new Date(ts*1000), n=new Date(), diff=n-d;
    const m=Math.floor(diff/60000);
    if (m<1) return '刚刚';
    if (m<60) return `${m}分钟前`;
    const h=Math.floor(m/60);
    if (h<24) return `${h}小时前`;
    const day=Math.floor(h/24);
    if (day<7) return `${day}天前`;
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
}

function fileIcon(mime, name) {
    if (!mime && !name) return {cls:'default',icon:'fas fa-file'};
    if (mime) {
        if (mime.startsWith('image/')) return {cls:'image',icon:'fas fa-image'};
        if (mime.startsWith('video/')) return {cls:'video',icon:'fas fa-video'};
        if (mime.startsWith('audio/')) return {cls:'audio',icon:'fas fa-music'};
    }
    if (name) {
        const e=name.split('.').pop().toLowerCase();
        if (['zip','rar','7z','tar','gz','bz2','xz'].includes(e)) return {cls:'archive',icon:'fas fa-file-archive'};
        if (['pdf'].includes(e)) return {cls:'pdf',icon:'fas fa-file-pdf'};
        if (['doc','docx'].includes(e)) return {cls:'pdf',icon:'fas fa-file-word'};
        if (['xls','xlsx'].includes(e)) return {cls:'pdf',icon:'fas fa-file-excel'};
        if (['js','ts','py','java','c','cpp','h','html','css','json','xml','yaml','yml','go','rs','rb','php','sh','bat','ps1','sql'].includes(e)) return {cls:'code',icon:'fas fa-code'};
    }
    return {cls:'default',icon:'fas fa-file'};
}

// ── Keyboard ──
document.addEventListener('keydown', e => { if (e.key === 'Escape') { closePreview(); closeQR(); } });
document.getElementById('textInput').addEventListener('keydown', e => {
    if (e.ctrlKey && e.key === 'Enter') { e.preventDefault(); sendText(); }
});
