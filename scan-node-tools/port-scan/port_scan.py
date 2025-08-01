# modules/port_scan.py
import subprocess, tempfile, os, xml.etree.ElementTree as ET

def scan(target):
    """
    Dùng nmap SYN scan top 1000 ports.
    Trả về {'open_ports': [port,…]}
    """
    # Thử SYN scan trước, nếu fail thì fallback sang TCP connect scan
    temp_fd, temp_path = tempfile.mkstemp(suffix='.xml')
    os.close(temp_fd)
    
    try:
        # Thử SYN scan (cần root)
        cmd = ['nmap', '-sS', '--top-ports', '1000', '-oX', temp_path, target]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        # Fallback sang TCP connect scan (không cần root)
        cmd = ['nmap', '-sT', '--top-ports', '1000', '-oX', temp_path, target]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # parse XML
    tree = ET.parse(temp_path)
    os.remove(temp_path)
    ports = []
    for p in tree.findall(".//port"):
        if p.find('state').attrib.get('state') == 'open':
            ports.append(int(p.attrib['portid']))
    return {'open_ports': ports}
