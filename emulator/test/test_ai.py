import json
import urllib.request
import time

url = "http://127.0.0.1:11434/api/generate"
payload = {
    "model": "llama3.1",
    "prompt": "Hello! Please reply with a short sentence to verify you are online",
    "stream": False
}

print(f"[*] Sending warm-up prompt to {url}...")
start_time = time.time()

try:
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    with urllib.request.urlopen(req, timeout=300) as response:
        print(f"[+] Status Code: {response.status}")
        result = json.loads(response.read().decode('utf-8'))
        print(f"[+] AI Response: {result.get('response', 'No response generated.')}")
        
    end_time = time.time()
    print(f"[*] Finished in {end_time - start_time:.2f} seconds.")
    
except Exception as e:
    print(f"[-] Error testing AI: {e}")
