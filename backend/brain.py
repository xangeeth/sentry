import requests
import json

def get_fallback_analysis(vendor, model, firmware_version, running_config, cve_list, vulnerabilities_found):
    cve_str = ", ".join(cve_list) if cve_list else "None identified"
    config_text = (running_config or "").lower()
    
    flaws = []
    cli_remediation = []
    
    v_prefix = (vendor or "Cisco").split()[0]
    
    if "enable password" in config_text:
        flaws.append("Plaintext enable password used instead of hashed secret")
        cli_remediation.append("enable secret <STRONG_HASHED_SECRET>\nno enable password")
    if "transport input telnet" in config_text:
        flaws.append("Insecure Telnet protocol enabled on VTY lines")
        cli_remediation.append("line vty 0 15\n transport input ssh\n login local")
    if "ip http server" in config_text and "no ip http server" not in config_text:
        flaws.append("Unencrypted HTTP web management server enabled")
        cli_remediation.append("no ip http server\nip http secure-server")
    if "snmp-server community public" in config_text:
        flaws.append("Default 'public' SNMP community string exposed")
        cli_remediation.append("no snmp-server community public\nsnmp-server community <SECURE_STRING> RO")
    if "vstack" in config_text and "no vstack" not in config_text:
        flaws.append("Smart Install (vStack) protocol enabled (CVE-2018-0171 target)")
        cli_remediation.append("no vstack")
        
    if not flaws and vulnerabilities_found == 0:
        return (
            f"EXECUTIVE SECURITY BRIEF ({vendor} {model} - Firmware {firmware_version}):\n"
            f"✅ CLEAN AUDIT: 0 active vulnerabilities reported in NIST NVD for this firmware build.\n"
            f"No critical security misconfigurations detected in running-config.\n\n"
            f"RECOMMENDED DEFENSIVE POSTURE:\n"
            f"Maintain standard hardening ({v_prefix}# ip ssh version 2, AAA authentication, disable CDP/LLDP on edge interfaces)."
        )

    flaw_summary = "\n".join([f"  • {f}" for f in flaws]) if flaws else "  • Firmware-level vulnerability exposure."
    cli_code = "\n".join(cli_remediation) if cli_remediation else "configure terminal\nip ssh version 2\nno service tcp-small-servers\nend"

    return (
        f"EXECUTIVE SECURITY BRIEF ({vendor} {model} - Firmware {firmware_version}):\n"
        f"⚠️ CRITICAL WARNING: Sentry identified {vulnerabilities_found} security threats (NIST NVD CVEs & Config Flaws).\n\n"
        f"IDENTIFIED NIST NVD CVEs:\n  • {cve_str}\n\n"
        f"CONFIGURATION SECURITY AUDIT:\n{flaw_summary}\n\n"
        f"TAILORED CLI REMEDIATION SCRIPT:\n"
        f"{v_prefix}# configure terminal\n"
        f"{cli_code}\n"
        f"{v_prefix}# write memory"
    )

def analyze_config(vendor, model, firmware_version, running_config, cve_list=None, vulnerabilities_found=0):
    url = "http://127.0.0.1:11434/api/generate"
    cve_list = cve_list or []
    
    if vulnerabilities_found > 0:
        cve_text = f"NIST NVD CVEs: {', '.join(cve_list)}" if cve_list else "Firmware vulnerabilities present"
        threat_context = f"CRITICAL WARNING: Sentry identified {vulnerabilities_found} security risks. {cve_text}. You MUST explicitly cite these CVE IDs."
    else:
        threat_context = "GOOD NEWS: 0 known vulnerabilities. Briefly confirm the device configuration and firmware are secure."

    system_prompt = f"""
    Generate an objective executive security brief for a {vendor} {model} (Firmware {firmware_version}).
    NEVER use first-person pronouns (I, me, my, we). Do not greet the user.
    
    {threat_context}
    
    Configuration:
    {running_config}
    
    Provide a technical analysis and exact CLI remediation code for {vendor} {model}.
    """
    
    payload = {
        "model": "llama3.1", 
        "prompt": system_prompt,
        "stream": False 
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json().get("response", "No response generated.")
        return get_fallback_analysis(vendor, model, firmware_version, running_config, cve_list, vulnerabilities_found)
    except Exception:
        return get_fallback_analysis(vendor, model, firmware_version, running_config, cve_list, vulnerabilities_found)

def ask_assistant(user_prompt: str):
    """ Dedicated conversational AI endpoint for plain-English to CLI translation. """
    print(f"[*] Sending prompt to AI Assistant...")
    url = "http://127.0.0.1:11434/api/generate"
    
    system_prompt = (
        "You are a strict, elite Network Security Engineer. "
        "You ONLY answer questions related to network configuration, switch infrastructure, and cybersecurity. "
        "If a user asks a non-networking question, you MUST reply exactly with: "
        "'I am a network security assistant. I cannot assist with that.' "
        "Provide your answers in clean, readable formats. If providing CLI commands, format them clearly in plain text."
    )

    payload = {
        "model": "llama3.1",
        "system": system_prompt,
        "prompt": user_prompt,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "Error: No response generated.")
    except Exception:
        prompt_lower = user_prompt.lower()
        if "vlan" in prompt_lower:
            return "CLI Translation:\nconfigure terminal\nvlan 10\n name HARDENED_NET\nexit\ninterface Gig0/1\n switchport mode access\n switchport access vlan 10\nend\nwrite memory"
        elif "ssh" in prompt_lower or "crypto" in prompt_lower:
            return "CLI Translation:\nconfigure terminal\nip domain-name sentry.local\ncrypto key generate rsa modulus 2048\nip ssh version 2\nline vty 0 4\n transport input ssh\n login local\nend"
        return f"SENTRY AI ASSISTANT (Offline Fallback Mode):\nProcessed instruction: '{user_prompt}'\n\nRecommendation:\nVerify interface security, enforce IEEE 802.1X/MACsec, disable unused ports, and restrict administrative access via VTY ACLs."
