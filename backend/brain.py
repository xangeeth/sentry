import requests

def analyze_config(vendor, model, running_config, vulnerabilities_found=0):
    url = "http://127.0.0.1:11434/api/generate"
    
    # 1. Threat Context
    if vulnerabilities_found > 0:
        threat_context = f"CRITICAL WARNING: The NIST National Vulnerability Database reports {vulnerabilities_found} known firmware vulnerabilities. You MUST explicitly mention this severe risk."
    else:
        threat_context = "GOOD NEWS: The NIST National Vulnerability Database reports 0 known vulnerabilities. Briefly acknowledge the firmware is secure."

    # 2. Dynamic Config Logic (Stops Hallucinations)
    if not running_config or running_config.strip() == "NOT_PROVIDED":
        config_instructions = "The user did NOT provide a running-configuration. DO NOT hallucinate or invent one. Simply write a 2-sentence executive summary advising the user on the firmware's safety based on the vulnerability count."
        running_config = "[NO CONFIGURATION PROVIDED]"
    else:
        config_instructions = "Review the provided running-configuration below. Identify security bad practices and provide 2-3 specific, defensive CLI commands to harden the switch."

    # 3. The Defensive Mandate (Bypasses the Safety Filter)
    system_prompt = f"""
    Generate an objective, third-person executive security brief for a {vendor} {model} switch. 
    NEVER use first-person pronouns (I, me, my, we). Do not greet the user.
    
    {threat_context}
    
    {config_instructions}
    
    Configuration:
    {running_config}
    
    Provide a comprehensive but standard-length technical analysis (3 to 5 sentences). Include the exact CLI commands required for mitigation if applicable.
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



def ask_assistant(user_prompt: str):
    """
    Dedicated conversational AI endpoint for plain-English to CLI translation.
    """
    print(f"[*] Sending prompt to AI Assistant...")
    url = "http://127.0.0.1:11434/api/generate"
    
    # The STRICT System Prompt to prevent non-networking questions
    system_prompt = (
        "You are a strict, elite CCIE Network Security Engineer. "
        "You ONLY answer questions related to network configuration, switch infrastructure, and cybersecurity. "
        "If a user asks a non-networking question, you MUST reply exactly with: "
        "'I am a network security assistant. I cannot assist with that.' "
        "Provide your answers in clean, readable formats. If providing CLI commands, format them clearly."
    )

    payload = {
        "model": "llama3.1",
        "system": system_prompt,
        "prompt": user_prompt,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "Error: No response generated.")
    except Exception as e:
        print(f"[-] AI Assistant communication failed: {e}")
        return f"Error connecting to local AI: {e}"