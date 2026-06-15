import React, { useState } from 'react';
import { sentryAPI } from '../api';

const UniversalScanner = () => {
  const [vendor, setVendor] = useState('');
  const [model, setModel] = useState('');
  const [version, setVersion] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [results, setResults] = useState(null);
  const [formError, setFormError] = useState(''); 

  // The Local Heuristics Dictionary for Auto-Suggest
  const commonVendors = ['Cisco', 'Juniper', 'Aruba', 'Palo Alto', 'Fortinet'];
  const commonModels = {
    'cisco': ['ios', 'ios_xe', 'asa', 'nexus', 'catalyst'],
    'juniper': ['junos', 'ex4300', 'srx'],
    'aruba': ['arubaos', 'clearpass'],
    'palo alto': ['pan-os'],
    'fortinet': ['fortios']
  };

  const handleScan = async (e) => {
    e.preventDefault();
    
    if (!vendor || !model || !version) {
      setFormError('⚠️ All fields (Vendor, Model, OS/Firmware) are required to query the NIST database.');
      return;
    }
    
    setFormError('');
    setIsScanning(true);
    setResults(null);

    const response = await sentryAPI.scanHardware(vendor, model, version);
    
    setIsScanning(false);

    if (response && response.security_scan) {
      const scanData = response.security_scan;
      
      // THE NEW VERIFICATION LOGIC
      let displayStatus = 'Secure';
      if (scanData.vulnerabilities_found > 0) {
        displayStatus = 'Vulnerable';
      } else {
        // If 0 vulnerabilities, we mark it Yellow/Unverified instead of Secure
        displayStatus = 'Unverified / Unknown';
      }

      setResults({
        status: displayStatus,
        threatCount: scanData.vulnerabilities_found || 0,
        eolStatus: 'Check Local DB',
        targetName: `${vendor.toUpperCase()} ${model.toUpperCase()} (v${version})`,
        topThreat: scanData.top_critical_threats && scanData.top_critical_threats.length > 0 
          ? scanData.top_critical_threats[0] 
          : 'No active CVE records verified in the NVD for this specific hardware string.'
      });
    } else {
      setResults({
        status: 'API Error',
        threatCount: '?',
        eolStatus: 'Offline',
        targetName: `${vendor.toUpperCase()} ${model.toUpperCase()}`,
        topThreat: 'Failed to communicate with Project Sentry Engine or NVD.'
      });
    }
  };

  // Helper to dynamically load model suggestions based on what Vendor they typed
  const getModelSuggestions = () => {
    const normalizedVendor = vendor.toLowerCase().trim();
    return commonModels[normalizedVendor] || [];
  };

  return (
    <div className="animate-fade-in flex flex-col items-center justify-center min-h-[80vh]">
      
      <div className="text-center mb-10">
        <h1 className="text-4xl font-bold mb-3 flex items-center justify-center space-x-3">
          <span>🔍</span>
          <span>Universal Scanner</span>
        </h1>
        <p className="text-gray-400 max-w-lg">
          Query the NIST National Vulnerability Database (NVD) and local EoL records for any network hardware.
        </p>
      </div>

      <div className="bg-surface p-8 rounded-xl border border-gray-800 shadow-2xl w-full max-w-4xl">
        
        {formError && (
          <div className="mb-6 bg-red-500/10 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg text-sm font-medium flex items-center justify-center animate-fade-in">
            {formError}
          </div>
        )}

        <form onSubmit={handleScan} className="flex space-x-4">
          <div className="flex-1">
            <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Vendor</label>
            <input 
              type="text" 
              list="vendor-suggestions"
              placeholder="e.g. Cisco" 
              value={vendor}
              onChange={(e) => setVendor(e.target.value)}
              className="w-full bg-[#0f172a] border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-primary transition-colors"
            />
            {/* The Hidden Suggestions Dictionary */}
            <datalist id="vendor-suggestions">
              {commonVendors.map((v, idx) => <option key={idx} value={v} />)}
            </datalist>
          </div>

          <div className="flex-1">
            <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Hardware Model</label>
            <input 
              type="text" 
              list="model-suggestions"
              placeholder="e.g. IOS" 
              value={model}
              onChange={(e) => setModel(e.target.value)}
              className="w-full bg-[#0f172a] border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-primary transition-colors"
            />
            <datalist id="model-suggestions">
              {getModelSuggestions().map((m, idx) => <option key={idx} value={m} />)}
            </datalist>
          </div>

          <div className="flex-1">
            <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">OS / Firmware</label>
            <input 
              type="text" 
              placeholder="e.g. 15.2" 
              value={version}
              onChange={(e) => setVersion(e.target.value)}
              className="w-full bg-[#0f172a] border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-primary transition-colors"
            />
          </div>

          <div className="flex items-end">
            <button 
              type="submit"
              disabled={isScanning}
              className="bg-primary hover:bg-blue-600 disabled:bg-blue-800 text-white px-8 py-3 rounded-lg font-bold transition-colors shadow-lg shadow-primary/20 h-[50px] w-[140px] flex items-center justify-center"
            >
              {isScanning ? <span className="animate-pulse">Scanning...</span> : 'Search'}
            </button>
          </div>
        </form>

        {results && (
          <div className="mt-8 p-6 bg-[#0f172a] border border-gray-800 rounded-lg animate-fade-in">
            <div className="flex justify-between items-start mb-6 border-b border-gray-800 pb-4">
              <div>
                <h3 className="text-xl font-bold">Threat Intelligence Report</h3>
                <p className="text-sm text-primary font-mono mt-1 opacity-80">
                  TARGET: {results.targetName}
                </p>
              </div>
              
              {/* Dynamic Badging Logic */}
              <span className={`px-3 py-1 rounded-full text-sm font-bold border ${
                results.status === 'Vulnerable' 
                  ? 'bg-red-500/10 text-red-500 border-red-500/20' 
                  : results.status === 'Unverified / Unknown'
                    ? 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
                    : 'bg-green-500/10 text-green-500 border-green-500/20'
              }`}>
                {results.status}
              </span>
            </div>
            
            <div className="grid grid-cols-3 gap-6">
              <div className="bg-surface p-4 rounded border border-gray-700">
                <p className="text-gray-400 text-xs uppercase font-bold mb-1">Active CVEs</p>
                <p className={`text-3xl font-bold ${results.threatCount > 0 ? 'text-red-400' : 'text-gray-400'}`}>
                  {results.threatCount}
                </p>
              </div>
              <div className="bg-surface p-4 rounded border border-gray-700">
                <p className="text-gray-400 text-xs uppercase font-bold mb-1">Lifecycle Status</p>
                <p className="text-xl font-bold text-gray-400 mt-1">{results.eolStatus}</p>
              </div>
              <div className="bg-surface p-4 rounded border border-gray-700 col-span-3">
                <p className="text-gray-400 text-xs uppercase font-bold mb-1">Top Critical Threat</p>
                <p className="text-white font-mono text-sm mt-1">{results.topThreat}</p>
              </div>
            </div>
          </div>
        )}
      </div>

    </div>
  );
};

export default UniversalScanner;