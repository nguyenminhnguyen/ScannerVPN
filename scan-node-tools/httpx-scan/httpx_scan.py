# modules/httpx_scan.py
import subprocess
import json

def scan(target):
    """
    Dùng httpx để quét HTTP:
      - ip, port, service, status-code, headers, protocol
    """
    # httpx đầu ra JSON, mỗi dòng là 1 object
    cmd = [
        'httpx',
        '-silent',
        '-json',
        '-u', target
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    lines = [l for l in proc.stdout.splitlines() if l.strip()]
    if not lines:
        return {}

    # chỉ lấy dòng đầu tiên
    data = json.loads(lines[0])
    return {
        'metadata': {
            'ip': data.get('ip'),
            'port': data.get('port'),
            'service': data.get('service'),
            'responseHeaders': data.get('headers', {}),
            'statusCode': data.get('status-code'),
            'protocol': data.get('http-protocol'),
        }
    }
