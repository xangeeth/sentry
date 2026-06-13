import requests

# Notice the new parameter added to the end of this line!
def analyze_config(vendor, model, running_config, vulnerabilities_found=0):
    url = "http://127.0.0.1:11434/api/generate"
    
    # Dynamic Prompt Injection based on the NIST NVD results
    if vulnerabilities_found > 0:
        threat_context = f"CRITICAL WARNING: The NIST National Vulnerability Database reports {vulnerabilities_found} known firmware vulnerabilities for this specific switch. You MUST explicitly mention this severe risk in your opening sentence."
    else:
        threat_context = "GOOD NEWS: The NIST National Vulnerability Database reports 0 known vulnerabilities for this firmware version. Briefly acknowledge that the firmware baseline is secure before moving on to the configuration."

    system_prompt = f"""
    You are an elite, CCIE-certified Network Security Engineer. 
    Review the following running-configuration for a {vendor} {model} switch.
    
    {threat_context}
    
    Identify any security vulnerabilities, bad practices, or missing standard configurations in the text.
    Provide 2-3 specific, actionable CLI commands to fix the issues. Keep your response professional and concise.
    
    Configuration:
    {running_config}
    """
    
    payload = {
        "model": "llama3.1", 
        "prompt": system_prompt,
        "stream": False 
    }
    
    try:
        response = requests.post(url, json=payload, timeout=300)
        if response.status_code == 200:
            return response.json().get("response", "No response generated.")
        return f"Ollama API Error: {response.status_code}"
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to Ollama. Is the Ollama app running?"
    except requests.exceptions.Timeout:
        return "Error: The AI took too long to respond. The model might be loading."