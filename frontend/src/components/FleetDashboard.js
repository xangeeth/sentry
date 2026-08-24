import React, { useState, useEffect } from 'react';
import { sentryAPI } from '../api';

const FleetDashboard = () => {
  const [switches, setSwitches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [aiAnalysisResult, setAiAnalysisResult] = useState('');
  
  // Discovery Modal State
  const [showDiscoveryModal, setShowDiscoveryModal] = useState(false);
  const [discoveryIP, setDiscoveryIP] = useState('127.0.0.1:2222');
  const [discoveryUser, setDiscoveryUser] = useState('admin');
  const [discoveryPass, setDiscoveryPass] = useState('admin');
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [discoveryNotice, setDiscoveryNotice] = useState('');

  const fetchInventory = async () => {
    setLoading(true);
    const data = await sentryAPI.getSwitches();
    if (data) {
      setSwitches(data);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchInventory();
  }, []);

  const getStatusColor = (threatCount) => {
    if (threatCount === null || threatCount === undefined || threatCount < 0) {
      return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20'; // Pending AI Audit
    }
    if (threatCount === 0) {
      return 'bg-green-500/10 text-green-500 border-green-500/20'; // Clean / Secure
    }
    return 'bg-red-500/10 text-red-500 border-red-500/20'; // Vulnerabilities Found
  };

  const handleAnalyze = (device) => {
    setSelectedDevice(device);
    setIsAnalyzing(false);
    setAiAnalysisResult('');
  };

  const triggerAI = async () => {
    if (!selectedDevice) return;
    setIsAnalyzing(true);
    setAiAnalysisResult('Connecting to Sentry AI Engine...');

    const res = await sentryAPI.analyzeConfig({
      vendor: selectedDevice.vendor,
      model: selectedDevice.model,
      firmware_version: selectedDevice.firmware_version || selectedDevice.firmware,
      running_config: selectedDevice.running_config || "N/A",
      threat_count: selectedDevice.threat_count || 0,
      hostname: selectedDevice.hostname,
      ip_address: selectedDevice.ip_address || selectedDevice.ip
    });

    setIsAnalyzing(false);
    if (res && res.ccie_ai_analysis) {
      setAiAnalysisResult(res.ccie_ai_analysis);
      if (res.threat_count !== undefined) {
        setSelectedDevice(prev => prev ? { ...prev, threat_count: res.threat_count } : null);
      }
      fetchInventory(); // Automatically update table with newly evaluated threat score
    } else {
      setAiAnalysisResult("⚠️ Error generating AI analysis. Please verify backend service.");
    }
  };

  const handleDiscoverSubmit = async (e) => {
    e.preventDefault();
    if (!discoveryIP) return;
    setIsDiscovering(true);
    setDiscoveryNotice('');

    const res = await sentryAPI.discoverSwitch(discoveryIP, discoveryUser, discoveryPass);
    setIsDiscovering(false);

    if (res && res.status === 'success') {
      setDiscoveryNotice(`Successfully discovered target device at ${discoveryIP}!`);
      fetchInventory();
      setTimeout(() => {
        setShowDiscoveryModal(false);
        setDiscoveryNotice('');
      }, 1500);
    } else {
      const errMsg = res?.message || res?.detail || 'Connection failed. Please verify the target IP address and credentials.';
      setDiscoveryNotice(`⚠️ Discovery Error: ${errMsg}`);
    }
  };

  const handleRescanAll = async () => {
    setLoading(true);
    await sentryAPI.rescanSwitches();
    await fetchInventory();
  };

  const handleRescanSingle = async (e, device) => {
    if (e && e.stopPropagation) e.stopPropagation();
    const ip = device.ip_address || device.ip;
    setLoading(true);
    await sentryAPI.rescanSwitches(ip);
    await fetchInventory();
  };

  const handleDelete = async (e, device) => {
    if (e && e.stopPropagation) e.stopPropagation();
    const identifier = device.id || device.ip_address || device.ip || device.hostname;
    if (window.confirm(`Are you sure you want to remove switch '${device.hostname}' from sentry.db inventory?`)) {
      setLoading(true);
      await sentryAPI.deleteSwitch(identifier);
      await fetchInventory();
    }
  };

  return (
    <div className="animate-fade-in relative">
      
      {/* Top Control Bar */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Fleet Dashboard</h1>
          <p className="text-gray-400">Enterprise Network Inventory & Threat Matrix</p>
        </div>
        <div className="flex space-x-3">
          <button 
            onClick={handleRescanAll}
            className="bg-gray-800 hover:bg-gray-700 text-gray-200 px-4 py-2 rounded-lg font-medium transition-colors border border-gray-700 flex items-center space-x-2 shadow-md"
            title="Re-probe live network switches over RESTCONF/SSH and update inventory"
          >
            <span>↻</span>
            <span>Refresh & Live Sync</span>
          </button>
          <a 
            href={sentryAPI.exportURL}
            target="_blank"
            rel="noopener noreferrer"
            className="bg-gray-800 hover:bg-gray-700 text-gray-200 px-4 py-2 rounded-lg font-medium transition-colors border border-gray-700 flex items-center space-x-2 shadow-md"
          >
            <span>📥</span>
            <span>Export CSV Report</span>
          </a>
          <button 
            onClick={() => setShowDiscoveryModal(true)}
            className="bg-primary hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium transition-colors shadow-lg shadow-primary/20 flex items-center space-x-2"
          >
            <span>📡</span>
            <span>Discover Network</span>
          </button>
        </div>
      </div>

      {/* The Data Table */}
      <div className="bg-surface rounded-xl border border-gray-800 overflow-hidden shadow-2xl">
        {loading ? (
          <div className="p-12 text-center text-gray-400 font-mono">
            <span className="animate-pulse">Probing & syncing live enterprise network switches...</span>
          </div>
        ) : switches.length === 0 ? (
          <div className="p-12 text-center text-gray-400">
            <p className="text-lg font-medium text-gray-300 mb-1">No network switches in inventory</p>
            <p className="text-sm text-gray-500 mb-4">Click "Discover Network" to scan and add switches dynamically.</p>
            <button 
              onClick={() => setShowDiscoveryModal(true)}
              className="bg-primary hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium text-sm transition-colors shadow-md inline-flex items-center space-x-2"
            >
              <span>📡</span>
              <span>Discover Network</span>
            </button>
          </div>
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-800/50 text-gray-400 uppercase text-xs tracking-wider border-b border-gray-800">
              <tr>
                <th className="px-6 py-4">Hostname</th>
                <th className="px-6 py-4">IP Address</th>
                <th className="px-6 py-4">Vendor & Model</th>
                <th className="px-6 py-4">Firmware</th>
                <th className="px-6 py-4">Threat Status</th>
                <th className="px-6 py-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {switches.map((device) => {
                const threatCount = device.threat_count;
                const isPending = threatCount === null || threatCount === undefined || threatCount < 0;
                return (
                  <tr key={device.id} className="hover:bg-gray-800/40 transition-colors">
                    <td className="px-6 py-4 font-medium text-white">{device.hostname}</td>
                    <td className="px-6 py-4 text-gray-400 font-mono">{device.ip_address || device.ip}</td>
                    <td className="px-6 py-4 text-gray-300">{device.vendor} {device.model}</td>
                    <td className="px-6 py-4 text-gray-400 font-mono text-xs">{device.firmware_version || 'v1.0'}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${getStatusColor(threatCount)}`}>
                        {isPending ? '⏳ Pending AI Audit' : (threatCount === 0 ? '🛡️ Clean / Secure' : `⚠️ ${threatCount} Vulnerabilities`)}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button 
                          onClick={(e) => handleRescanSingle(e, device)}
                          className="text-gray-300 hover:text-white font-medium text-xs bg-gray-800 hover:bg-gray-700 px-2 py-1 rounded border border-gray-700 transition-colors flex items-center space-x-1"
                          title="Re-probe live device and update configuration"
                        >
                          <span>↻</span>
                          <span>Re-sync</span>
                        </button>
                        <button 
                          onClick={() => handleAnalyze(device)}
                          className="text-primary hover:text-blue-400 font-medium text-sm transition-colors px-1"
                        >
                          Analyze &rarr;
                        </button>
                        <button 
                          onClick={(e) => handleDelete(e, device)}
                          className="text-red-400 hover:text-red-300 font-medium text-xs bg-red-500/10 hover:bg-red-500/20 px-2 py-1 rounded border border-red-500/30 transition-colors flex items-center space-x-1"
                          title="Delete switch record from sentry.db"
                        >
                          <span>🗑️</span>
                          <span>Delete</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {/* Discovery Modal */}
      {showDiscoveryModal && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-surface w-full max-w-md rounded-xl border border-gray-700 shadow-2xl overflow-hidden p-6 animate-fade-in">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-bold flex items-center space-x-2">
                <span>📡</span>
                <span>Network Switch Discovery</span>
              </h2>
              <button 
                onClick={() => setShowDiscoveryModal(false)}
                className="text-gray-400 hover:text-white text-xl"
              >
                &times;
              </button>
            </div>

            {discoveryNotice && (
              <div className="mb-4 bg-primary/10 border border-primary/30 text-blue-300 p-3 rounded-lg text-xs font-mono">
                {discoveryNotice}
              </div>
            )}

            <form onSubmit={handleDiscoverSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-400 uppercase mb-1">Target IP Address</label>
                <input 
                  type="text" 
                  value={discoveryIP}
                  onChange={(e) => setDiscoveryIP(e.target.value)}
                  placeholder="e.g. 192.168.222.129"
                  className="w-full bg-[#0f172a] border border-gray-700 rounded-lg px-4 py-2 text-white font-mono text-sm"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-400 uppercase mb-1">Username</label>
                <input 
                  type="text" 
                  value={discoveryUser}
                  onChange={(e) => setDiscoveryUser(e.target.value)}
                  placeholder="admin"
                  className="w-full bg-[#0f172a] border border-gray-700 rounded-lg px-4 py-2 text-white font-mono text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-400 uppercase mb-1">Password</label>
                <input 
                  type="password" 
                  value={discoveryPass}
                  onChange={(e) => setDiscoveryPass(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-[#0f172a] border border-gray-700 rounded-lg px-4 py-2 text-white font-mono text-sm"
                />
              </div>

              <div className="pt-2 flex justify-end space-x-3">
                <button 
                  type="button" 
                  onClick={() => setShowDiscoveryModal(false)}
                  className="px-4 py-2 rounded-lg text-sm text-gray-400 hover:text-white"
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  disabled={isDiscovering}
                  className="bg-primary hover:bg-blue-600 disabled:bg-blue-800 text-white px-6 py-2 rounded-lg font-bold text-sm transition-colors"
                >
                  {isDiscovering ? 'Scanning...' : 'Initiate Scan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* The AI Deep-Dive Modal */}
      {selectedDevice && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-surface w-full max-w-6xl h-[80vh] rounded-xl border border-gray-700 flex flex-col shadow-2xl overflow-hidden animate-fade-in">
            
            {/* Modal Header */}
            <div className="flex justify-between items-center p-6 border-b border-gray-800 bg-gray-800/30">
              <div>
                <h2 className="text-2xl font-bold text-white flex items-center space-x-3">
                  <span>Target: {selectedDevice.hostname}</span>
                  <span className="text-sm font-normal text-gray-400 font-mono bg-black/30 px-3 py-1 rounded-full">
                    {selectedDevice.ip_address || selectedDevice.ip}
                  </span>
                </h2>
              </div>
              <button 
                onClick={() => setSelectedDevice(null)}
                className="text-gray-400 hover:text-white transition-colors text-2xl"
              >
                &times;
              </button>
            </div>

            {/* Modal Body (Split Screen) */}
            <div className="flex-1 flex overflow-hidden">
              
              {/* Left Column: Device Details */}
              <div className="w-1/3 border-r border-gray-800 p-6 overflow-y-auto bg-gray-900/20 space-y-6">
                <div>
                  <h3 className="text-xs uppercase font-bold text-gray-400 mb-2">Hardware Details</h3>
                  <div className="bg-black/40 p-4 rounded-lg border border-gray-800 space-y-2 text-sm">
                    <p><strong className="text-gray-300">Vendor:</strong> {selectedDevice.vendor}</p>
                    <p><strong className="text-gray-300">Model:</strong> {selectedDevice.model}</p>
                    <p><strong className="text-gray-300">Firmware:</strong> {selectedDevice.firmware_version || '1.0'}</p>
                  </div>
                </div>

                <div>
                  <h3 className="text-xs uppercase font-bold text-gray-400 mb-2">Threat Assessment</h3>
                  <div className="bg-black/40 p-4 rounded-lg border border-gray-800 text-sm">
                    <p className="text-red-400 font-bold mb-1">
                      {selectedDevice.threat_count || 0} Reported Vulnerabilities
                    </p>
                    <p className="text-gray-400 text-xs">
                      Evaluated against NIST National Vulnerability Database (NVD).
                    </p>
                  </div>
                </div>

                <div>
                  <h3 className="text-xs uppercase font-bold text-gray-400 mb-2">Running Config Preview</h3>
                  <pre className="bg-black/80 p-3 rounded-lg border border-gray-800 text-xs font-mono text-green-400 max-h-48 overflow-y-auto whitespace-pre-wrap">
                    {selectedDevice.running_config || 'No running configuration loaded.'}
                  </pre>
                </div>
              </div>

              {/* Right Column: AI Terminal */}
              <div className="w-2/3 flex flex-col p-6 bg-[#0a0a0a]">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-bold text-primary flex items-center space-x-2">
                    <span>🤖</span>
                    <span>Remediation Engine</span>
                  </h3>
                  {!isAnalyzing && (
                    <button 
                      onClick={triggerAI}
                      className="bg-primary hover:bg-blue-600 text-white px-4 py-2 rounded shadow text-sm font-medium transition-colors"
                    >
                      Initialize AI Analysis
                    </button>
                  )}
                </div>

                <div className="flex-1 bg-black rounded-lg border border-gray-800 p-4 font-mono text-sm overflow-y-auto relative shadow-inner">
                  {!isAnalyzing && !aiAnalysisResult ? (
                    <div className="text-gray-500 flex flex-col items-center justify-center h-full space-y-4">
                      <span className="text-4xl">💻</span>
                      <p>System ready. Click 'Initialize AI Analysis' to process configuration.</p>
                    </div>
                  ) : isAnalyzing ? (
                    <div className="text-green-400 space-y-3">
                      <p className="text-gray-400">&gt; Connecting to Project Sentry AI Engine...</p>
                      <p className="text-gray-400">&gt; Evaluating {selectedDevice.vendor} {selectedDevice.model} configuration...</p>
                      <span className="animate-pulse">_</span>
                    </div>
                  ) : (
                    <div className="text-green-400 whitespace-pre-wrap">
                      {aiAnalysisResult}
                    </div>
                  )}
                </div>
              </div>

            </div>
          </div>
        </div>
      )}

    </div>
  );
};

export default FleetDashboard;