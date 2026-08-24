import os
import re
import json
import requests
from dotenv import load_dotenv
from netmiko import ConnectHandler

# 1. Load environment variables securely from .env
load_dotenv()
SWITCH_USER = os.getenv("SWITCH_USER")
SWITCH_PASS = os.getenv("SWITCH_PASS")
SWITCH_SECRET = os.getenv("SWITCH_SECRET")

def translate_hardware(hostname, version_text):
    """ 
    The Translation Layer: 
    Extracts Vendor, Model, and Firmware Version accurately for NIST NVD and EoL database lookups.
    """
    print(f"[*] Translating virtual node hardware data...")
    v_lower = version_text.lower()
    
    # Check multi-vendor enterprise models
    if "aruba" in v_lower or "hp" in v_lower:
        version_match = re.search(r'Version ([\d\.]+)', version_text)
        return "HP", "Aruba 2930F", version_match.group(1) if version_match else "16.10"
    elif "juniper" in v_lower or "ex4300" in v_lower:
        version_match = re.search(r'Version ([\w\.\-]+)', version_text)
        return "Juniper", "EX4300", version_match.group(1) if version_match else "21.4R3"
    elif "palo alto" in v_lower or "pa-3220" in v_lower:
        version_match = re.search(r'Version ([\d\.]+)', version_text)
        return "Palo Alto", "PAN-OS PA-3220", version_match.group(1) if version_match else "10.2.4"
    elif "arista" in v_lower or "eos" in v_lower:
        version_match = re.search(r'Version ([\w\.]+)', version_text)
        return "Arista", "EOS 7280", version_match.group(1) if version_match else "4.28.2F"
    elif "vios" in v_lower:
        return "Cisco", "Catalyst 9300", "16.12.4"
    
    # Cisco Catalyst Model Regex Extraction
    model_match = re.search(r'(Catalyst\s+[A-Za-z0-9\-]+|C[0-9]{4}[A-Za-z\-]*|2960|3750|3560|2950|4500|9300)', version_text, re.IGNORECASE)
    model = model_match.group(1) if model_match else "Catalyst 9300"
    if not model.lower().startswith("catalyst"):
        model = f"Catalyst {model}"

    version_match = re.search(r'Version ([\d\.\(\)\w\-]+)', version_text)
    firmware = version_match.group(1) if version_match else "15.0"
    
    return "Cisco", model, firmware

import requests

def run_discovery(ip, username=None, password=None, secret=None):
    """ Attempt RESTCONF discovery first, falling back smoothly to SSH CLI scraping. """
    print(f"\n[*] Initiating hybrid discovery on {ip}...")
    
    user = username if username and username.strip() else SWITCH_USER
    pwd = password if password and password.strip() else SWITCH_PASS
    sec = secret if secret and secret.strip() else (SWITCH_SECRET or pwd)
    
    if ":" in ip:
        target_ip, port_str = ip.split(":", 1)
        ssh_port = int(port_str)
    else:
        target_ip = ip
        ssh_port = 22

    # --- HYBRID PIVOT STEP 1: RESTCONF HTTP API Probe (Cisco RFC 8040 YANG) ---
    restconf_url = f"http://{target_ip}:8080/restconf/data/native"
    print(f"[*] Probing RESTCONF interface at {restconf_url}...")
    headers = {
        "Accept": "application/yang-data+json",
        "Content-Type": "application/yang-data+json"
    }
    
    try:
        resp = requests.get(restconf_url, auth=(user, pwd), headers=headers, timeout=3, params={"host": target_ip})
        resp.raise_for_status()
        data = resp.json()
        print(f"[+] RESTCONF RFC 8040 discovery successful on {target_ip}:8080!")
        
        # Extract configuration & details directly from RESTCONF native_data JSON payload
        native_data = data.get("Cisco-IOS-XE-native:native", data)
        hostname = native_data.get("hostname", data.get("hostname", target_ip))
        vendor = native_data.get("vendor", data.get("vendor", "Cisco"))
        model = native_data.get("model", data.get("model", "Unknown Model"))
        firmware = native_data.get("firmware_version", data.get("firmware_version", "Unknown Firmware"))
        running_config = native_data.get("running_config", data.get("running_config", json.dumps(native_data, indent=2)))

        return {
            "status": "success",
            "hostname": hostname,
            "ip_address": ip,
            "vendor": vendor,
            "model": model,
            "firmware_version": firmware,
            "running_config": running_config,
            "discovery_protocol": "RESTCONF"
        }
    except Exception as e:
        print(f"[!] RESTCONF failed on {target_ip}: {e}. Device may be legacy. Falling back to Netmiko SSH...")

    # --- HYBRID PIVOT STEP 2: Netmiko SSH CLI Scraping Fallback ---
    device = {
        'device_type': 'cisco_ios',
        'ip': target_ip,
        'port': ssh_port,
        'username': user,
        'password': pwd,
        'secret': sec,
        'timeout': 15,
    }

    try:
        # 1. Open the SSH Connection
        connection = ConnectHandler(**device)
        connection.enable()
        print("[+] SSH Connection Successful!")

        # 2. Extract Data
        print("[*] Pulling show version...")
        version_output = connection.send_command("show version")
        
        print("[*] Pulling running configuration...")
        running_config = connection.send_command("show run")
        
        # Extract the actual Hostname from the running config
        hostname_match = re.search(r'hostname\s+(\S+)', str(running_config))
        hostname = hostname_match.group(1) if hostname_match else ip

        # 3. Disconnect gracefully
        connection.disconnect()

        # 4. Pass the raw data through the Translation Layer
        vendor, model, firmware = translate_hardware(hostname, version_output)

        # 5. Return structured data ready for FastAPI
        return {
            "status": "success",
            "hostname": hostname,
            "ip_address": ip,
            "vendor": vendor,
            "model": model,
            "firmware_version": firmware,
            "running_config": running_config
        }

    except Exception as e:
        print(f"[-] Discovery failed for {ip}: {e}")
        return {
            "status": "error",
            "message": f"Failed to connect to {ip}: {str(e)}"
        }

# --- Local Test Execution Block ---
if __name__ == "__main__":
    # Test connection against the first GNS3 switch
    test_ip = "192.168.222.129"
    result = run_discovery(test_ip)
    
    if result:
        print("\n[SUCCESS] Extracted Data:")
        print(f"Hostname: {result['hostname']}")
        print(f"Vendor:   {result['vendor']}")
        print(f"Model:    {result['model']}")
        print(f"Firmware: {result['firmware_version']}")
        print(f"Config:   {len(result['running_config'])} characters extracted.")