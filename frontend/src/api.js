// src/api.js

const BASE_URL = "http://127.0.0.1:8000/api/v1";

export const sentryAPI = {
  // 1. Scanner Endpoint (Hits NIST NVD)
  scanHardware: async (vendor, model, version) => {
    try {
      const response = await fetch(`${BASE_URL}/scan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // We pass "N/A" for running_config just to satisfy the Pydantic model
        body: JSON.stringify({ 
          vendor: vendor, 
          model: model, 
          firmware_version: version,
          running_config: "N/A" 
        })
      });
      return await response.json();
    } catch (error) {
      console.error("Scanner Error:", error);
      return null;
    }
  },

  // 2. AI Assistant Endpoint (Hits local Llama 3.1)
  askAssistant: async (message) => {
    try {
      const response = await fetch(`${BASE_URL}/assistant`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: message })
      });
      return await response.json();
    } catch (error) {
      console.error("AI Error:", error);
      return null;
    }
  }
};