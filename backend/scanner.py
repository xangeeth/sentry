import requests

def check_vulnerabilities(vendor: str, model: str, version: str):
    base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    
    # Define search patterns from most specific to most broad
    # This ensures if "Cisco ASA 5505 9.1" fails, it tries "Cisco ASA 9.1"
    patterns = [
        f"{vendor} {model} {version}",
        f"{vendor} {model}",
        f"{vendor} {version}"
    ]
    
    for query in patterns:
        print(f"[*] Trying NVD query: {query}")
        params = {"keywordSearch": query, "resultsPerPage": 10}
        
        try:
            response = requests.get(base_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                total = data.get("totalResults", 0)
                
                if total > 0:
                    # Successfully found results!
                    cve_items = data.get("vulnerabilities", [])
                    top_threats = [item["cve"]["id"] for item in cve_items[:5]]
                    
                    return {
                        "status": "Vulnerable",
                        "vulnerabilities_found": total,
                        "top_critical_threats": top_threats
                    }
        except Exception as e:
            print(f"[*] Query failed: {query}, error: {e}")
            continue

    # If we get here, no pattern worked
    return {
        "status": "Unverified / Unknown",
        "vulnerabilities_found": 0,
        "top_critical_threats": []
    }