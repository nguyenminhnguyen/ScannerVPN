# modules/dns_lookup.py
import socket
import os
import sys
import json
import requests

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

if __name__ == "__main__":
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
                        "job_id": job_id
                    }
                }
                print(f"Sending result to Controller: {payload}")
                response = requests.post(f"{controller_url}/api/scan_results", json=payload)
                print(f"Controller response: {response.status_code}")
        except Exception as e:
            print(f"Error sending results to Controller: {e}")
    
    print("DNS Lookup scan completed")
