import requests

def check_vulnerabilities(vendor, model, version):
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    search_query = f"{vendor} {model} {version}"
    
    params = {
        "keywordSearch": search_query,
        "resultsPerPage": 20 # Increased slightly to pull a good sample size
    }

    try:
        response = requests.get(url, params=params, timeout=15)
        if response.status_code != 200:
            return {"error": f"NIST API unavailable. Status Code: {response.status_code}"}
            
        data = response.json()
        total_results = data.get("totalResults", 0)
        vulnerabilities_list = data.get("vulnerabilities", [])
        
        # Extract the specific details for the Frontend to use later
        extracted_cves = []
        for vuln in vulnerabilities_list:
            cve_data = vuln.get("cve", {})
            cve_id = cve_data.get("id", "Unknown ID")
            
            # 1. Get the English Description
            desc = "No description available"
            for d in cve_data.get("descriptions", []):
                if d.get("lang") == "en":
                    desc = d.get("value")
                    break
                    
            # 2. Get the CVSS Score (Checking V3.1, V3.0, or V2.0)
            score = 0.0
            metrics = cve_data.get("metrics", {})
            if "cvssMetricV31" in metrics:
                score = metrics["cvssMetricV31"][0]["cvssData"].get("baseScore", 0.0)
            elif "cvssMetricV30" in metrics:
                score = metrics["cvssMetricV30"][0]["cvssData"].get("baseScore", 0.0)
            elif "cvssMetricV2" in metrics:
                score = metrics["cvssMetricV2"][0]["cvssData"].get("baseScore", 0.0)
                
            extracted_cves.append({
                "id": cve_id,
                "cvss_score": score,
                "description": desc
            })
            
        # Sort the CVEs by their CVSS score (highest to lowest)
        extracted_cves = sorted(extracted_cves, key=lambda x: x["cvss_score"], reverse=True)
        
        return {
            "query": search_query,
            "vulnerabilities_found": total_results,
            "status": "Vulnerable" if total_results > 0 else "Secure",
            "top_threats": extracted_cves[:5] # We only return the Top 5 to the JSON payload
        }
        
    except Exception as e:
        return {"error": f"Connection failed: {str(e)}"}

# Local test loop
if __name__ == "__main__":
    print("Fetching advanced threat intelligence...")
    result = check_vulnerabilities("Cisco", "IOS", "15.2")
    import json
    print(json.dumps(result, indent=2))