"""mDNS/Zeroconf service for LANITS auto-discovery."""

import socket
import threading
import time

def start_zeroconf(port=9527):
    """Register LANITS service via mDNS so Android/iOS can auto-discover."""
    try:
        from zeroconf import Zeroconf, ServiceInfo
    except ImportError:
        print('[ZEROCONF] zeroconf not available; install with: pip install zeroconf')
        return

    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]; s.close(); return ip
        except:
            return '127.0.0.1'

    hostname = socket.gethostname()
    local_ip = get_local_ip()

    info = ServiceInfo(
        type_='_lants._tcp.local.',
        name=f'LANITS-{hostname}._lants._tcp.local.',
        addresses=[socket.inet_aton(local_ip)],
        port=port,
        properties={'version': '1.0', 'hostname': hostname},
        server=f'{hostname}.local.',
    )

    zeroconf = Zeroconf()
    zeroconf.register_service(info)
    print(f'[ZEROCONF] Registered _lants._tcp at {local_ip}:{port}')

    return zeroconf
