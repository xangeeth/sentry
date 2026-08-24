import React, { useState } from 'react';
import { sentryAPI } from '../api';

const UniversalScanner = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [results, setResults] = useState(null);
  const [formError, setFormError] = useState(''); 

  const handleScan = async (e) => {
    e.preventDefault();
    
    if (!searchQuery.trim()) {
      setFormError('⚠️ Please enter a search query.');
      return;
    }
    
    setFormError('');
    setIsScanning(true);
    setResults(null);

    const scanRes = await sentryAPI.scanHardware(searchQuery);

    setIsScanning(false);

    if (scanRes && scanRes.security_scan) {
      const scanData = scanRes.security_scan;
      
      let displayStatus = 'Secure';
      if (scanData.status === 'API Timeout' || scanData.status === 'API Error') {
        displayStatus = scanData.status;
      } else if (scanData.vulnerabilities_found > 0) {
        displayStatus = 'Vulnerable';
      } else {
        displayStatus = 'Clean / Verified';
      }

      setResults({
        status: displayStatus,
        threatCount: scanData.vulnerabilities_found || 0,
        targetName: scanData.query_used || searchQuery,
        topThreat: scanData.top_critical_threats && scanData.top_critical_threats.length > 0 
          ? scanData.top_critical_threats[0] 
          : (displayStatus.includes('API') ? 'NVD API Error: Could not verify vulnerabilities.' : 'No active CVE records verified in NVD for this specific query.')
      });
    } else {
      setResults({
        status: 'API Error',
        threatCount: '?',
        targetName: searchQuery,
        topThreat: 'Failed to communicate with Project Sentry Engine.'
      });
    }
  };

  return (
    <div className="animate-fade-in flex flex-col items-center justify-center min-h-[80vh]">
      
      <div className="text-center mb-10">
        <h1 className="text-4xl font-bold mb-3 flex items-center justify-center space-x-3">
          <span>🔍</span>
          <span>Universal Scanner</span>
        </h1>
        <p className="text-gray-400 max-w-lg">
          Query the NIST NVD Database for network hardware vulnerabilities.
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
            <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Search Query</label>
            <input 
              type="text" 
              placeholder="e.g. Juniper EX4300 18.2 or CVE-2023-20198" 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
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
                  TARGET: {results.targetName.toUpperCase()}
                </p>
              </div>
              
              {/* Dynamic Badging Logic */}
              <span className={`px-3 py-1 rounded-full text-sm font-bold border ${
                results.status === 'Vulnerable' 
                  ? 'bg-red-500/10 text-red-500 border-red-500/20' 
                  : results.status.includes('API')
                    ? 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20'
                    : 'bg-green-500/10 text-green-500 border-green-500/20'
              }`}>
                {results.status}
              </span>
            </div>
            
            <div className="flex flex-col gap-6">
              <div className="bg-surface p-4 rounded border border-gray-700 w-1/3">
                <p className="text-gray-400 text-xs uppercase font-bold mb-1">Active CVEs</p>
                <p className={`text-3xl font-bold ${results.threatCount > 0 ? 'text-red-400' : 'text-gray-400'}`}>
                  {results.threatCount}
                </p>
              </div>
              <div className="bg-surface p-4 rounded border border-gray-700 w-full">
                <p className="text-gray-400 text-xs uppercase font-bold mb-2">Top Critical Threat</p>
                <p className="text-white font-mono text-sm leading-relaxed">{results.topThreat}</p>
              </div>
            </div>
          </div>
        )}
      </div>

    </div>
  );
};

export default UniversalScanner;