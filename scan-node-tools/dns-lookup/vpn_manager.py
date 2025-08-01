import requests
import random
import subprocess
import os
import time
import sys

class VPNManager:
    def __init__(self, proxy_node="http://10.102.199.36:8000"):
        self.proxy_node = proxy_node
        self.vpn_process = None
        
    def fetch_vpns(self):
        """Lấy danh sách VPN từ proxy server"""
        try:
            response = requests.get(f"{self.proxy_node}/vpns", timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[!] Lỗi khi fetch VPN list: {e}")
            return []
    
    def download_vpn(self, filename):
        """Download VPN config file"""
        try:
            r = requests.get(f"{self.proxy_node}/vpn/{filename}", timeout=30)
            r.raise_for_status()
            vpn_path = f"/tmp/{filename}"
            with open(vpn_path, "wb") as f:
                f.write(r.content)
            return vpn_path
        except Exception as e:
            print(f"[!] Lỗi khi download VPN {filename}: {e}")
            return None
    
    def connect_vpn(self, vpn_file):
        """Kết nối VPN"""
        print(f"[+] Kết nối VPN: {vpn_file}")
        try:
            self.vpn_process = subprocess.Popen([
                "openvpn", "--config", vpn_file,
                "--data-ciphers", "AES-256-GCM:AES-128-GCM:CHACHA20-POLY1305:AES-128-CBC",
                "--verb", "1"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Đợi VPN kết nối (tối đa 30 giây)
            for i in range(30):
                if self.is_vpn_connected():
                    print("[+] VPN đã kết nối thành công!")
                    
                    # Đợi thêm 5 giây cho routing tables update
                    print("[*] Đợi routing tables cập nhật...")
                    time.sleep(5)
                    
                    return True
                time.sleep(1)
                
            print("[!] VPN không thể kết nối trong 30 giây")
            self.disconnect_vpn()
            return False
            
        except Exception as e:
            print(f"[!] Lỗi khi kết nối VPN: {e}")
            return False
    
    def is_vpn_connected(self):
        """Kiểm tra VPN đã kết nối chưa"""
        try:
            # Kiểm tra interface tun
            result = subprocess.run(['ip', 'addr', 'show', 'tun0'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def disconnect_vpn(self):
        """Ngắt kết nối VPN"""
        if self.vpn_process and self.vpn_process.poll() is None:
            print("[*] Ngắt kết nối VPN...")
            self.vpn_process.terminate()
            try:
                self.vpn_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.vpn_process.kill()
            self.vpn_process = None
    
    def setup_random_vpn(self):
        """Setup VPN ngẫu nhiên"""
        # Lấy IP ban đầu
        original_ip = self.get_current_ip()
        print(f"[*] IP ban đầu: {original_ip}")
        
        vpns = self.fetch_vpns()
        if not vpns:
            print("[!] Không có VPN nào available")
            return False
            
        # Thử tối đa 3 VPN ngẫu nhiên
        for attempt in range(3):
            chosen_vpn = random.choice(vpns)
            print(f"[+] Thử VPN: {chosen_vpn} (lần {attempt + 1})")
            
            vpn_path = self.download_vpn(chosen_vpn)
            if vpn_path and self.connect_vpn(vpn_path):
                # Kiểm tra IP sau khi kết nối
                new_ip = self.get_current_ip()
                print(f"[+] IP sau VPN: {new_ip}")
                
                # Kiểm tra VPN có hoạt động không
                if self.is_vpn_working():
                    print(f"[+] VPN hoạt động tốt! IP: {original_ip} -> {new_ip}")
                    return True
                else:
                    print(f"[!] VPN chưa hoạt động đúng, thử tiếp...")
                    self.disconnect_vpn()
                    continue
                
        print("[!] Không thể kết nối VPN nào")
        return False
    
    def is_vpn_working(self):
        """Kiểm tra VPN có thực sự hoạt động không"""
        checks = []
        
        # 1. Kiểm tra TUN interface
        tun_ok = self.is_vpn_connected()
        checks.append(f"TUN interface: {'✓' if tun_ok else '✗'}")
        
        # 2. Kiểm tra có default route qua VPN không
        try:
            result = subprocess.run(['ip', 'route', 'show', 'default'], 
                                  capture_output=True, text=True)
            route_ok = 'tun' in result.stdout
            checks.append(f"VPN routing: {'✓' if route_ok else '✗'}")
        except:
            route_ok = False
            checks.append("VPN routing: ✗")
        
        # 3. Test DNS resolution qua VPN
        try:
            result = subprocess.run(['nslookup', 'google.com'], 
                                  capture_output=True, text=True, timeout=5)
            dns_ok = result.returncode == 0
            checks.append(f"DNS test: {'✓' if dns_ok else '✗'}")
        except:
            dns_ok = False
            checks.append("DNS test: ✗")
            
        print(f"[*] VPN Health Check: {' | '.join(checks)}")
        
        # VPN được coi là hoạt động nếu có TUN interface và ít nhất 1 test khác pass
        return tun_ok and (route_ok or dns_ok)
    
    def get_current_ip(self):
        """Lấy IP hiện tại - thử nhiều method"""
        methods = [
            ['curl', '-s', '--max-time', '5', 'https://api.ipify.org'],
            ['curl', '-s', '--max-time', '5', 'http://ipinfo.io/ip'],
            ['curl', '-s', '--max-time', '5', 'http://checkip.amazonaws.com'],
            ['wget', '-qO-', '--timeout=5', 'https://api.ipify.org']
        ]
        
        for method in methods:
            try:
                result = subprocess.run(method, capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and result.stdout.strip():
                    ip = result.stdout.strip()
                    # Validate IP format
                    if self._is_valid_ip(ip):
                        return ip
            except:
                continue
                
        # Fallback: check local interface IPs
        try:
            result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
            if result.returncode == 0:
                ips = result.stdout.strip().split()
                for ip in ips:
                    if self._is_valid_ip(ip) and not ip.startswith('127.'):
                        return ip
        except:
            pass
            
        return "Unknown"
    
    def _is_valid_ip(self, ip):
        """Kiểm tra IP hợp lệ"""
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except:
            return False
    
    def get_network_info(self):
        """Lấy thông tin network chi tiết"""
        info = {
            "public_ip": self.get_current_ip(),
            "tun_interface": False,
            "local_ip": None,
            "default_route": None
        }
        
        try:
            # Kiểm tra tun interface
            result = subprocess.run(['ip', 'addr', 'show', 'tun0'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                info["tun_interface"] = True
                # Extract local IP từ tun0
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'inet ' in line and 'scope global' in line:
                        info["local_ip"] = line.split()[1].split('/')[0]
            
            # Kiểm tra default route
            result = subprocess.run(['ip', 'route', 'show', 'default'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                info["default_route"] = result.stdout.strip()
                
        except Exception as e:
            print(f"[!] Error getting network info: {e}")
            
        return info
    
    def print_vpn_status(self):
        """In trạng thái VPN hiện tại"""
        info = self.get_network_info()
        print(f"[*] === VPN Status ===")
        print(f"[*] Public IP: {info['public_ip']}")
        print(f"[*] TUN Interface: {'✓' if info['tun_interface'] else '✗'}")
        print(f"[*] Local VPN IP: {info['local_ip'] or 'N/A'}")
        print(f"[*] Default Route: {info['default_route'] or 'N/A'}")
        print(f"[*] VPN Process: {'Running' if self.vpn_process and self.vpn_process.poll() is None else 'Stopped'}")
        return info
