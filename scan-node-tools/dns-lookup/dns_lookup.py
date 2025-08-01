# modules/dns_lookup.py
import socket

def scan(target):
    """
    Resolve domain → list IP.
    Nếu input đã là IP thì vẫn trả về chính nó.
    """
    try:
        ips = socket.gethostbyname_ex(target)[2]
    except socket.gaierror:
        ips = [target]
    return {'resolved_ips': ips}
