import requests
import urllib.parse

def check_vulnerabilities(query: str):
    """ Queries NIST NVD REST API v2.0 for live CVEs matching the free-text query. """
    base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    
    clean_query = (query or "").strip()
    
    if not clean_query:
        return {
            "status": "Clean / Verified",
            "vulnerabilities_found": 0,
            "top_critical_threats": [],
            "query_used": clean_query
        }
        
    print(f"[*] Querying NIST NVD API v2.0: '{clean_query}'...")
    encoded_query = urllib.parse.quote(clean_query)
    params = f"keywordSearch={encoded_query}&resultsPerPage=5"
    url = f"{base_url}?{params}"
    
    try:
        # NVD can be slow, giving 10s timeout
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            total = data.get("totalResults", 0)
            
            if total > 0:
                cve_items = data.get("vulnerabilities", [])
                top_threats = []
                for item in cve_items[:5]:
                    cve = item.get("cve", {})
                    cve_id = cve.get("id")
                    if cve_id:
                        # Extract description
                        desc = "No description available"
                        descriptions = cve.get("descriptions", [])
                        for d in descriptions:
                            if d.get("lang") == "en":
                                desc = d.get("value")
                                break
                        
                        # Extract CVSS Score (try V3.1, then V3.0, then V2)
                        cvss_score = ""
                        metrics = cve.get("metrics", {})
                        if "cvssMetricV31" in metrics:
                            cvss_score = metrics["cvssMetricV31"][0].get("cvssData", {}).get("baseScore", "")
                        elif "cvssMetricV30" in metrics:
                            cvss_score = metrics["cvssMetricV30"][0].get("cvssData", {}).get("baseScore", "")
                        elif "cvssMetricV2" in metrics:
                            cvss_score = metrics["cvssMetricV2"][0].get("cvssData", {}).get("baseScore", "")
                        
                        if cvss_score:
                            threat_str = f"{cve_id} (CVSS {cvss_score}): {desc}"
                        else:
                            threat_str = f"{cve_id}: {desc}"
                            
                        top_threats.append(threat_str)
                
                print(f"[+] NIST NVD API returned {total} CVE records for '{clean_query}'!")
                return {
                    "status": "Vulnerable",
                    "vulnerabilities_found": total,
                    "top_critical_threats": top_threats,
                    "query_used": clean_query
                }
            else:
                # 200 OK but 0 results
                return {
                    "status": "Clean / Verified",
                    "vulnerabilities_found": 0,
                    "top_critical_threats": [],
                    "query_used": clean_query
                }
        else:
            print(f"[!] NIST NVD API returned status code {response.status_code}")
            return {
                "status": "API Error",
                "vulnerabilities_found": 0,
                "top_critical_threats": [],
                "query_used": clean_query,
                "error_details": f"API returned HTTP {response.status_code}"
            }
            
    except requests.exceptions.RequestException as e:
        print(f"[!] NIST NVD API query attempt timed out or failed: {e}")
        return {
            "status": "API Timeout",
            "vulnerabilities_found": 0,
            "top_critical_threats": [],
            "query_used": clean_query,
            "error_details": str(e)
        }