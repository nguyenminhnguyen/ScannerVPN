# modules/dns_lookup.py
import socket
import os
import sys
import json
import requests
from vpn_manager import VPNManager

def scan(target):
    """
    Resolve domain → list IP.
    Nếu input đã là IP thì vẫn trả về chính nó.
    """
    try:
        # Thử resolve domain name với Python socket
        ips = socket.gethostbyname_ex(target)[2]
        print(f"[+] Resolved {target} to: {ips}")
        return {'resolved_ips': ips}
    except socket.gaierror as e:
        print(f"[!] Socket resolution failed for {target}: {e}")
        
        # Fallback: thử dùng nslookup command
        try:
            import subprocess
            result = subprocess.run(['nslookup', target], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Parse nslookup output
                lines = result.stdout.split('\n')
                ips = []
                for line in lines:
                    if 'Address:' in line and not 'server' in line.lower():
                        ip = line.split('Address:')[1].strip()
                        if ip and not ip.startswith('#'):
                            ips.append(ip)
                
                if ips:
                    print(f"[+] nslookup resolved {target} to: {ips}")
                    return {'resolved_ips': ips}
        except Exception as lookup_error:
            print(f"[!] nslookup failed: {lookup_error}")
        
        # Check if target is already an IP
        try:
            socket.inet_aton(target)
            print(f"[+] {target} is already an IP address")
            return {'resolved_ips': [target]}
        except socket.error:
            # Không phải IP và không resolve được
            print(f"[!] Cannot resolve {target} - returning original")
            return {'resolved_ips': [target]}  # Return original target

if __name__ == "__main__":
    print("[*] Starting DNS Lookup scan with VPN...")
    
    # Setup VPN trước khi scan
    vpn_manager = VPNManager()
    vpn_connected = False
    network_info = {}
    
    # Thử setup VPN (optional - có thể skip nếu proxy server không available)
    try:
        print("[*] Checking initial network status...")
        initial_info = vpn_manager.get_network_info()
        print(f"[*] Initial IP: {initial_info['public_ip']}")
        
        if vpn_manager.setup_random_vpn():
            print("[+] VPN setup completed!")
            vpn_manager.print_vpn_status()
            network_info = vpn_manager.get_network_info()
            vpn_connected = True
        else:
            print("[!] VPN connection failed, continuing without VPN...")
    except Exception as e:
        print(f"[!] VPN setup error: {e}, continuing without VPN...")
    
    try:
        # Đọc targets từ environment variable hoặc command line
        targets = os.getenv("TARGETS", "").split(",") if os.getenv("TARGETS") else sys.argv[1:]
        controller_url = os.getenv("CONTROLLER_CALLBACK_URL")
        job_id = os.getenv("JOB_ID")
        
        print(f"DNS Lookup scan starting for targets: {targets}")
        
        # Scan từng target
        all_results = []
        for target in targets:
            if target.strip():
                print(f"Scanning {target.strip()}...")
                result = scan(target.strip())
                print(f"Result for {target.strip()}: {result}")
                all_results.append({
                    "target": target.strip(),
                    "resolved_ips": result.get("resolved_ips", [])
                })
        
        # Gửi kết quả về Controller nếu có callback URL
        if controller_url and all_results:
            try:
                for result in all_results:
                    payload = {
                        "target": result["target"],
                        "resolved_ips": result["resolved_ips"],
                        "open_ports": [],
                        "scan_metadata": {
                            "tool": "dns-lookup",
                            "job_id": job_id,
                            "vpn_used": vpn_connected,
                            "scan_ip": network_info.get("public_ip", "Unknown"),
                            "vpn_local_ip": network_info.get("local_ip"),
                            "tun_interface": network_info.get("tun_interface", False)
                        }
                    }
                    print(f"Sending result to Controller: {payload}")
                    response = requests.post(f"{controller_url}/api/scan_results", json=payload)
                    print(f"Controller response: {response.status_code}")
            except Exception as e:
                print(f"Error sending results to Controller: {e}")
        
        print("DNS Lookup scan completed")
        
    finally:
        # Cleanup VPN
        if vpn_connected:
            print("[*] Disconnecting VPN...")
            vpn_manager.disconnect_vpn()
