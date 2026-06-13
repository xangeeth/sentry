import requests

def check_vulnerabilities(vendor, model, version):
    # The official NIST NVD API v2 endpoint
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
    
    # We combine the switch details into a single search query
    search_query = f"{vendor} {model} {version}"
    
    # We set our API parameters. We only request a few results to keep it fast.
    params = {
        "keywordSearch": search_query,
        "resultsPerPage": 3 
    }

    try:
        # Send the HTTP GET request to the database with a 10-second timeout
        response = requests.get(url, params=params, timeout=10)
        
        # If the API rate-limits us or goes down, fail gracefully
        if response.status_code != 200:
            return {"error": f"NIST API unavailable. Status Code: {response.status_code}"}
            
        # Parse the JSON response
        data = response.json()
        total_results = data.get("totalResults", 0)
        
        return {
            "query": search_query,
            "vulnerabilities_found": total_results,
            "status": "Vulnerable" if total_results > 0 else "Secure"
        }
        
    except Exception as e:
        return {"error": f"Connection failed: {str(e)}"}

# A built-in test loop so we can verify the script works by itself
if __name__ == "__main__":
    print("Establishing Comm-Link to NIST NVD...")
    result = check_vulnerabilities("Cisco", "Catalyst", "16.12.4")
    print(f"Response: {result}")