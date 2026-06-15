import requests
import re
from netmiko import ConnectHandler

# --- 1. SENTRY CONFIGURATION ---
SENTRY_API_URL = "http://127.0.0.1:8000/api/v1"

def translate_hardware(hostname, version_text):
    """ The Translation Layer """
    print(f"[*] Translating virtual node: {hostname}")
    version_match = re.search(r'Version (\d+\.\d+)', version_text)
    firmware = version_match.group(1) if version_match else "15.2"

    if "Core" in hostname or "R1" in hostname:
        return {"vendor": "Cisco", "model": "Catalyst 9500", "firmware": firmware}
    elif "Access-1" in hostname:
        return {"vendor": "Cisco", "model": "Catalyst 9300", "firmware": firmware}
    elif "Access-2" in hostname:
        return {"vendor": "HP", "model": "Aruba 2930F", "firmware": firmware}
    else:
        return {"vendor": "Cisco", "model": "IOS Switch", "firmware": firmware}

# UPGRADE: Now it accepts variables from the web!
def run_discovery(ip, username, password):
    switch_auth = {
        'device_type': 'cisco_ios',
        'ip': ip,
        'username': username,
        'password': password,
        'secret': password,
    }

    try:
        print(f"[*] Initiating Netmiko SSH connection to {ip}...")
        connection = ConnectHandler(**switch_auth)
        connection.enable()
        
        raw_hostname = connection.base_prompt
        print(f"[+] Connected successfully to: {raw_hostname}")

        print("[*] Pulling show version and running-config...")
        version_out = connection.send_command("show version")
        config_out = connection.send_command("show run")
        connection.disconnect()

        hardware = translate_hardware(raw_hostname, version_out)
        
        payload = {
            "vendor": hardware["vendor"],
            "model": hardware["model"],
            "firmware_version": hardware["firmware"],
            "running_config": config_out,
            "threat_count": 0
        }

        print(f"[*] Sending {hardware['model']} to Sentry API...")
        
        # Hit Endpoint 1: The Scanner
        scan_resp = requests.post(f"{SENTRY_API_URL}/scan", json=payload)
        threats = scan_resp.json().get("security_scan", {}).get("vulnerabilities_found", 0)
        payload["threat_count"] = threats
        
        # Hit Endpoint 2: The AI & Database
        ai_resp = requests.post(f"{SENTRY_API_URL}/analyze", json=payload)
        
        if ai_resp.status_code == 200:
            # UPGRADE: Return the data so the Web UI can display it
            return {
                "status": "success",
                "message": f"Successfully onboarded {raw_hostname}",
                "threats": threats,
                "ai_summary": ai_resp.json().get("ccie_ai_analysis")
            }
        else:
            return {"status": "error", "message": "API Error during AI Analysis."}

    except Exception as e:
        return {"status": "error", "message": str(e)}