import socket
import sys
import threading
import paramiko
import os
import json
import time
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Path references
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIGS_DIR = os.path.join(BASE_DIR, "configs")
KEY_FILE = os.path.join(BASE_DIR, "emulator_rsa.key")

# Ensure RSA Host Key exists
if not os.path.exists(KEY_FILE):
    rsa_key = paramiko.RSAKey.generate(2048)
    rsa_key.write_private_key_file(KEY_FILE)
else:
    rsa_key = paramiko.RSAKey(filename=KEY_FILE)

# ANSI Colors for terminal logging
COLOR_HEADER = "\033[95m"
COLOR_BLUE = "\033[94m"
COLOR_CYAN = "\033[96m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"

def log_event(target_ip, hostname, event_type, client_info, message):
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    if event_type in ["AUTH SUCCESS", "CONN", "RESTCONF"]:
        color = COLOR_GREEN
    elif event_type in ["AUTH FAILED", "ERR"]:
        color = COLOR_RED
    elif event_type == "CLI CMD":
        color = COLOR_CYAN
    else:
        color = COLOR_YELLOW

    badge = f"[{event_type}]"
    print(f"{COLOR_BOLD}{timestamp}{COLOR_RESET} {color}{badge:<22}{COLOR_RESET} [{COLOR_BLUE}Client {client_info} -> {target_ip}:2222{COLOR_RESET}] [{COLOR_HEADER}{hostname}{COLOR_RESET}] -> {message}")

class SwitchServerInterface(paramiko.ServerInterface):
    def __init__(self, target_ip, hostname, client_info, switch_config=None):
        self.target_ip = target_ip
        self.hostname = hostname
        self.client_info = client_info
        self.switch_config = switch_config or {}

    def check_channel_request(self, kind, chanid):
        if kind == 'session':
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        expected_user = self.switch_config.get("username", "admin")
        expected_pass = self.switch_config.get("password", "admin")

        if username == expected_user and password == expected_pass:
            log_event(self.target_ip, self.hostname, "AUTH SUCCESS", self.client_info, f"User '{username}' authenticated successfully.")
            return paramiko.AUTH_SUCCESSFUL
        else:
            log_event(self.target_ip, self.hostname, "AUTH FAILED", self.client_info, f"ACCESS DENIED for user '{username}' (expected: '{expected_user}').")
            return paramiko.AUTH_FAILED

    def check_channel_pty_request(self, channel, term, modes, height, width, pixelwidth, pixelheight):
        return True

    def check_channel_shell_request(self, channel):
        return True

def handle_switch_client(client_socket, client_addr, target_ip, switch_config):
    client_info = f"{client_addr[0]}:{client_addr[1]}"
    hostname = switch_config.get("hostname", "Switch")
    vendor = switch_config.get("vendor", "Cisco")
    model = switch_config.get("model", "Catalyst")
    version = switch_config.get("firmware_version", "15.0")
    running_config = switch_config.get("running_config", "!\nend")

    transport = paramiko.Transport(client_socket)
    transport.add_server_key(rsa_key)
    server = SwitchServerInterface(target_ip, hostname, client_info, switch_config)
    
    try:
        transport.start_server(server=server)
    except Exception as e:
        log_event(target_ip, hostname, "ERR", client_info, f"SSH Handshake failed: {e}")
        return

    channel = transport.accept(20)
    if channel is None:
        return

    log_event(target_ip, hostname, "CONN", client_info, f"SSH CLI Shell Active ({vendor} {model})")
    
    # Send banner and CLI prompt
    prompt = f"{hostname}#"
    
    channel.send(f"\r\nUser Access Verification ({vendor} {model})\r\n\r\n{prompt}".encode('utf-8'))

    buffer = ""
    while True:
        try:
            data = channel.recv(1024)
            if not data:
                break
            
            text = data.decode('utf-8', errors='ignore')
            for char in text:
                if char in ['\r', '\n']:
                    channel.send(b"\r\n")
                    cmd = buffer.strip()
                    buffer = ""

                    if cmd.lower() in ["exit", "quit"]:
                        log_event(target_ip, hostname, "DISC", client_info, "Client disconnected session")
                        channel.send(b"Logging out...\r\n")
                        break
                    elif "show version" in cmd.lower() or "sh ver" in cmd.lower():
                        log_event(target_ip, hostname, "CLI CMD", client_info, f"Executed 'show version' ({vendor} {model} v{version})")
                        version_str = f"\r\n{vendor} IOS Software, {model} Software, Version {version}, RELEASE SOFTWARE\r\nTechnical Support: http://www.cisco.com/techsupport\r\n{hostname} uptime is 12 weeks, 4 days\r\nSystem image file is \"flash:image.bin\"\r\n{vendor} {model} processor with 2097152K bytes of memory.\r\n"
                        channel.send(version_str.replace('\n', '\r\n').encode('utf-8'))
                    elif "show run" in cmd.lower() or "sh run" in cmd.lower():
                        log_event(target_ip, hostname, "CLI CMD", client_info, f"Executed 'show run' (Config length: {len(running_config)} chars)")
                        channel.send(running_config.replace('\n', '\r\n').encode('utf-8'))
                    elif "show ip int" in cmd.lower() or "sh ip int" in cmd.lower():
                        log_event(target_ip, hostname, "CLI CMD", client_info, "Executed 'show ip int brief'")
                        int_str = f"\r\nInterface                  IP-Address      OK? Method Status                Protocol\r\nGigabitEthernet0/0         {target_ip} YES NVRAM  up                    up\r\nGigabitEthernet0/1         unassigned      YES NVRAM  up                    up\r\n"
                        channel.send(int_str.replace('\n', '\r\n').encode('utf-8'))
                    elif cmd.lower() == "enable":
                        log_event(target_ip, hostname, "CLI CMD", client_info, "Executed 'enable'")
                        channel.send(b"Password: ")
                    elif cmd:
                        log_event(target_ip, hostname, "CLI CMD", client_info, f"Executed unknown command '{cmd}'")
                        channel.send(f"% Invalid command: '{cmd}'\r\n".encode('utf-8'))
                    
                    channel.send(f"{prompt}".encode('utf-8'))
                else:
                    buffer += char
                    channel.send(char.encode('utf-8'))
        except Exception:
            break

    try:
        channel.close()
    except Exception:
        pass
    
    try:
        transport.close()
    except Exception:
        pass
    log_event(target_ip, hostname, "DISC", client_info, "Connection closed gracefully.")

def start_single_switch_listener(ip_idx, port=2222):
    target_ip = f"127.0.0.{ip_idx}"
    fallback_port = 2200 + ip_idx
    config_file = os.path.join(CONFIGS_DIR, f"switch{ip_idx}.json")
    
    switch_config = None
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                switch_config = json.load(f)
        except Exception as e:
            print(f"  {COLOR_RED}• Warning: Could not parse {config_file}: {e}{COLOR_RESET}")

    if not switch_config:
        switch_config = {
            "hostname": f"Switch-{ip_idx}",
            "vendor": "Cisco",
            "model": "Catalyst 9300",
            "firmware_version": "16.12.4",
            "username": "admin",
            "password": "admin",
            "running_config": "!\nend"
        }

    hostname = switch_config.get("hostname", f"Switch-{ip_idx}")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    bound_ip = target_ip
    bound_port = port

    try:
        server_socket.bind((target_ip, port))
        server_socket.listen(10)
    except Exception:
        try:
            server_socket.bind(("127.0.0.1", fallback_port))
            server_socket.listen(10)
            bound_ip = "127.0.0.1"
            bound_port = fallback_port
        except Exception as e:
            print(f"  {COLOR_RED}• Node {ip_idx:2d} -> Failed to bind {target_ip}:{port} / 127.0.0.1:{fallback_port} -> {e}{COLOR_RESET}")
            return

    status_tag = f"{COLOR_GREEN}[SECURE]{COLOR_RESET}" if switch_config.get("security_status") == "Good" else f"{COLOR_RED}[AI-BAIT/VULN]{COLOR_RESET}"
    print(f"  {COLOR_BOLD}• Node {ip_idx:2d}{COLOR_RESET} -> {COLOR_BLUE}{bound_ip}:{bound_port}{COLOR_RESET} | {COLOR_HEADER}{hostname:<20}{COLOR_RESET} | {status_tag}")

    while True:
        try:
            client_socket, client_addr = server_socket.accept()
            client_thread = threading.Thread(
                target=handle_switch_client, 
                args=(client_socket, client_addr, target_ip, switch_config)
            )
            client_thread.daemon = True
            client_thread.start()
        except Exception:
            break

import base64

# --- RESTCONF HTTP SERVER (PORT 8080) ---
class RESTCONFRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress default HTTP logging to keep console clean
        return

    def do_GET(self):
        parsed = urlparse(self.path)
        client_info = f"{self.client_address[0]}:{self.client_address[1]}"
        
        if parsed.path.startswith("/restconf/data/native"):
            params = parse_qs(parsed.query)
            target_host = params.get("host", [self.headers.get("Host", "127.0.0.1")])[0]
            if ":" in target_host:
                target_host = target_host.split(":")[0]
            
            # Map target IP to switch index strictly (127.0.0.1 through 127.0.0.10)
            node_idx = -1
            if target_host.startswith("127.0.0."):
                try:
                    idx = int(target_host.split(".")[-1])
                    if 1 <= idx <= 10:
                        node_idx = idx
                except ValueError:
                    pass
            
            config_file = os.path.join(CONFIGS_DIR, f"switch{node_idx}.json") if node_idx != -1 else None
            if config_file and os.path.exists(config_file):
                with open(config_file, "r") as f:
                    switch_data = json.load(f)
            else:
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"{COLOR_BOLD}{timestamp}{COLOR_RESET} {COLOR_RED}[RESTCONF 404 NOT FOUND]{COLOR_RESET}   [{COLOR_BLUE}Client {client_info}{COLOR_RESET}] -> Switch IP '{target_host}' not found on network")
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Device {target_host} not found on network. Please verify target IP address."}).encode('utf-8'))
                return

            # Enforce HTTP Basic Authentication against switch_data expected credentials
            expected_user = switch_data.get("username", "admin")
            expected_pass = switch_data.get("password", "admin")

            auth_header = self.headers.get("Authorization")
            authenticated = False
            if auth_header and auth_header.startswith("Basic "):
                try:
                    auth_decoded = base64.b64decode(auth_header.split(" ")[1]).decode("utf-8")
                    if auth_decoded == f"{expected_user}:{expected_pass}":
                        authenticated = True
                except Exception:
                    pass

            if not authenticated:
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"{COLOR_BOLD}{timestamp}{COLOR_RESET} {COLOR_RED}[RESTCONF AUTH FAILED]{COLOR_RESET}     [{COLOR_BLUE}Client {client_info}{COLOR_RESET}] -> Invalid RESTCONF HTTP Credentials (Expected user '{expected_user}')")
                self.send_response(401)
                self.send_header("WWW-Authenticate", 'Basic realm="RESTCONF"')
                self.end_headers()
                self.wfile.write(b'{"error": "Unauthorized - Invalid RESTCONF Credentials"}')
                return

            payload = {
                "Cisco-IOS-XE-native:native": switch_data
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/yang-data+json")
            self.end_headers()
            self.wfile.write(json.dumps(payload, indent=2).encode('utf-8'))
            
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            hostname = switch_data.get("hostname", f"Switch-{node_idx}")
            vendor = switch_data.get("vendor", "Cisco")
            model = switch_data.get("model", "Catalyst")
            firmware = switch_data.get("firmware_version", "17.06.03")
            print(f"{COLOR_BOLD}{timestamp}{COLOR_RESET} {COLOR_GREEN}[RESTCONF HTTP GET 200]{COLOR_RESET}        [{COLOR_BLUE}Client {client_info} -> {target_host}:8080{COLOR_RESET}] [{COLOR_HEADER}{hostname}{COLOR_RESET}] -> Transmitted Cisco RFC 8040 YANG JSON payload ({vendor} {model} v{firmware})")
        else:
            self.send_response(404)
            self.end_headers()

def start_restconf_server(port=8080):
    try:
        httpd = HTTPServer(("0.0.0.0", port), RESTCONFRequestHandler)
        print(f"  {COLOR_BOLD}• RESTCONF HTTP Server{COLOR_RESET} -> {COLOR_BLUE}http://0.0.0.0:{port}/restconf/data/native{COLOR_RESET} | {COLOR_GREEN}[ACTIVE]{COLOR_RESET}")
        httpd.serve_forever()
    except Exception as e:
        print(f"  {COLOR_RED}• RESTCONF HTTP Server Failed on port {port}: {e}{COLOR_RESET}")

def main():
    print(f"\n{COLOR_BOLD}==========================================================================")
    print(f"[*] SENTRY DISSERTATION MULTI-NODE SWITCH EMULATOR (10 NODES + RESTCONF)")
    print(f"=========================================================================={COLOR_RESET}")
    print(f"Spawning 10 SSH Servers + 1 RESTCONF HTTP Server on Port 8080...\n")

    # Start RESTCONF Server thread
    restconf_thread = threading.Thread(target=start_restconf_server, args=(8080,))
    restconf_thread.daemon = True
    restconf_thread.start()

    # Start 10 SSH Switch Listener threads
    threads = []
    for i in range(1, 11):
        t = threading.Thread(target=start_single_switch_listener, args=(i, 2222))
        t.daemon = True
        t.start()
        threads.append(t)
        time.sleep(0.05)

    print(f"\n{COLOR_BOLD}==========================================================================")
    print(f"[+] All 10 SSH Switch Nodes Live & Listening on Port 2222")
    print(f"[+] RESTCONF HTTP Server Live on http://127.0.0.1:8080/restconf/data/native")
    print(f"   Strict Auth Enforcement : Username 'admin' | Password 'admin'")
    print(f"   Nodes 1-5  : SECURE / 'Good' Configs (SSH v2, AES, Encrypted Secrets)")
    print(f"   Nodes 6-10 : VULNERABLE / 'Bad' Configs (Plaintext Passwords, Telnet, HTTP)")
    print(f"=========================================================================={COLOR_RESET}\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{COLOR_YELLOW}[*] Shutting down multi-node switch emulator...{COLOR_RESET}")

if __name__ == "__main__":
    main()
