const HOST = typeof window !== "undefined" && window.location.hostname ? window.location.hostname : "127.0.0.1";
const BASE_URL = `http://${HOST}:8000/api/v1`;

export const sentryAPI = {
  // 1. Get Inventory Switches
  getSwitches: async () => {
    try {
      const response = await fetch(`${BASE_URL}/switches`);
      if (!response.ok) throw new Error("Failed to fetch switches");
      return await response.json();
    } catch (error) {
      console.error("Get Switches Error:", error);
      return null;
    }
  },

  // 1b. Delete Switch from Inventory
  deleteSwitch: async (device) => {
    try {
      const payload = typeof device === "object" ? {
        id: device.id,
        ip_address: device.ip_address || device.ip,
        hostname: device.hostname
      } : {
        ip_address: String(device)
      };

      const response = await fetch(`${BASE_URL}/switches/delete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      return await response.json();
    } catch (error) {
      console.error("Delete Switch Error:", error);
      return null;
    }
  },

  // 1c. Live Re-Scan & Sync Switches via RESTCONF/SSH
  rescanSwitches: async (ipAddress = null) => {
    try {
      const response = await fetch(`${BASE_URL}/switches/rescan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip_address: ipAddress })
      });
      return await response.json();
    } catch (error) {
      console.error("Rescan Switches Error:", error);
      return null;
    }
  },

  // 2. Discover Switch via SSH or Network Probe
  discoverSwitch: async (ipAddress, username = null, password = null) => {
    try {
      const response = await fetch(`${BASE_URL}/discover`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          ip_address: ipAddress,
          username: username,
          password: password
        })
      });
      return await response.json();
    } catch (error) {
      console.error("Discovery Error:", error);
      return { status: "error", message: error.message };
    }
  },

  // 3. Scanner Endpoint (Hits NIST NVD)
  scanHardware: async (query) => {
    try {
      const response = await fetch(`${BASE_URL}/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: query })
      });
      return await response.json();
    } catch (error) {
      console.error("Scanner Error:", error);
      return null;
    }
  },

  // 4. AI Deep-Dive Analysis
  analyzeConfig: async (switchData) => {
    try {
      const response = await fetch(`${BASE_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vendor: switchData.vendor,
          model: switchData.model,
          firmware_version: switchData.firmware_version || switchData.firmware || "1.0",
          running_config: switchData.running_config || "N/A",
          threat_count: switchData.threat_count || switchData.threats || 0,
          hostname: switchData.hostname || "Unknown",
          ip_address: switchData.ip_address || switchData.ip || "127.0.0.1"
        })
      });
      return await response.json();
    } catch (error) {
      console.error("AI Analysis Error:", error);
      return null;
    }
  },

  // 5. Query Hardware Lifecycle (EoL/EoS)
  getLifecycle: async (vendor = "", model = "") => {
    try {
      const params = new URLSearchParams();
      if (vendor) params.append("vendor", vendor);
      if (model) params.append("model", model);
      const response = await fetch(`${BASE_URL}/lifecycle?${params.toString()}`);
      return await response.json();
    } catch (error) {
      console.error("Lifecycle Fetch Error:", error);
      return [];
    }
  },

  // 6. AI Assistant Endpoint (Plain English to CLI)
  askAssistant: async (prompt) => {
    try {
      const response = await fetch(`${BASE_URL}/assistant`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt })
      });
      return await response.json();
    } catch (error) {
      console.error("AI Assistant Error:", error);
      return null;
    }
  },

  // 7. CSV Export URL
  exportURL: `${BASE_URL}/export`
};