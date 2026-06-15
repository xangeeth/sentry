import os
import re
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
    Maps GNS3 vIOS to Real Enterprise Hardware for the NIST API and EoL DB.
    """
    print(f"[*] Translating virtual node hardware data...")
    
    # If the script detects a GNS3 vIOS switch, seamlessly map it to a Catalyst 9300
    if "vios" in version_text.lower() or "vios_l2" in version_text.lower():
        return "Cisco", "Catalyst 9300", "16.12.4"
        
    # Default fallback extraction using basic Regex if it's a real switch
    version_match = re.search(r'Version (\d+\.\d+)', version_text)
    firmware = version_match.group(1) if version_match else "Unknown"
    return "Cisco", "Unknown Model", firmware

def run_discovery(ip):
    """ SSH into the switch, pull data, and translate it. """
    print(f"\n[*] Initiating discovery on {ip}...")
    
    device = {
        'device_type': 'cisco_ios',
        'ip': ip,
        'username': SWITCH_USER,
        'password': SWITCH_PASS,
        'secret': SWITCH_SECRET,
        'timeout': 15, # Extended timeout to accommodate slower GNS3 VM responses
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
        hostname_match = re.search(r'hostname\s+(\S+)', running_config)
        hostname = hostname_match.group(1) if hostname_match else ip

        # 3. Disconnect gracefully
        connection.disconnect()

        # 4. Pass the raw data through the Translation Layer
        vendor, model, firmware = translate_hardware(hostname, version_output)

        # 5. Return structured data ready for FastAPI
        return {
            "hostname": hostname,
            "ip_address": ip,
            "vendor": vendor,
            "model": model,
            "firmware_version": firmware,
            "running_config": running_config
        }

    except Exception as e:
        print(f"[-] Discovery failed for {ip}: {e}")
        return None

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