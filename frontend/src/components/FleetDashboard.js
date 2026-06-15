import React, { useState } from 'react';

const FleetDashboard = () => {
  // State for the Modal
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const mockSwitches = [
    { id: 1, hostname: 'Core-Switch', ip: '192.168.222.129', hardware: 'Cisco Catalyst 9300', eol: 'Secure', threats: 0 },
    { id: 2, hostname: 'Access-1', ip: '192.168.222.130', hardware: 'HP Aruba 2930F', eol: 'Warning', threats: 3 },
    { id: 3, hostname: 'Access-2', ip: '192.168.222.131', hardware: 'Juniper EX4300', eol: 'Critical', threats: 12 },
  ];

  // Mock CVE Data for the Modal
  const mockCVEs = [
    { id: 'CVE-2018-0171', score: 9.8, desc: 'Remote Code Execution via Smart Install Feature.' },
    { id: 'CVE-2017-3881', score: 8.5, desc: 'Authentication Bypass in Telnet.' },
    { id: 'CVE-2020-3209', score: 7.2, desc: 'Denial of Service in IPv6 Processing.' },
  ];

  const getStatusColor = (status) => {
    if (status === 'Secure') return 'bg-green-500/10 text-green-500 border-green-500/20';
    if (status === 'Warning') return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
    if (status === 'Critical') return 'bg-red-500/10 text-red-500 border-red-500/20';
    return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
  };

  const handleAnalyze = (device) => {
    setSelectedDevice(device);
    setIsAnalyzing(false);
  };

  const triggerAI = () => {
    setIsAnalyzing(true);
    // Future: Here is where we will call FastAPI /api/v1/analyze
  };

  return (
    <div className="animate-fade-in relative">
      
      {/* Top Control Bar */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold mb-2">Fleet Dashboard</h1>
          <p className="text-gray-400">Inventory and security auditing for your GNS3 infrastructure.</p>
        </div>
        <button className="bg-primary hover:bg-blue-600 text-white px-4 py-2 rounded-lg font-medium transition-colors shadow-lg shadow-primary/20 flex items-center space-x-2">
          <span>📡</span>
          <span>Discover Network</span>
        </button>
      </div>

      {/* The Data Table */}
      <div className="bg-surface rounded-xl border border-gray-800 overflow-hidden shadow-2xl">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-800/50 text-gray-400 uppercase text-xs tracking-wider border-b border-gray-800">
            <tr>
              <th className="px-6 py-4">Hostname</th>
              <th className="px-6 py-4">IP Address</th>
              <th className="px-6 py-4">Hardware Model</th>
              <th className="px-6 py-4">Lifecycle Status</th>
              <th className="px-6 py-4">Threat Count</th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {mockSwitches.map((device) => (
              <tr key={device.id} className="hover:bg-gray-800/40 transition-colors">
                <td className="px-6 py-4 font-medium text-white">{device.hostname}</td>
                <td className="px-6 py-4 text-gray-400 font-mono">{device.ip}</td>
                <td className="px-6 py-4 text-gray-300">{device.hardware}</td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${getStatusColor(device.eol)}`}>
                    {device.eol}
                  </span>
                </td>
                <td className="px-6 py-4">
                  {device.threats > 0 ? (
                    <span className="flex items-center space-x-1 text-red-400 font-bold">
                      <span>{device.threats}</span>
                      <span className="text-xs font-normal opacity-80">CVEs</span>
                    </span>
                  ) : (
                    <span className="text-green-500 font-medium">Clean</span>
                  )}
                </td>
                <td className="px-6 py-4 text-right">
                  <button 
                    onClick={() => handleAnalyze(device)}
                    className="text-primary hover:text-blue-400 font-medium text-sm transition-colors"
                  >
                    Analyze &rarr;
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

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
                    {selectedDevice.ip}
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
              
              {/* Left Column: Raw Threats */}
              <div className="w-1/3 border-r border-gray-800 p-6 overflow-y-auto bg-gray-900/20">
                <h3 className="text-lg font-bold text-red-400 mb-4 flex items-center space-x-2">
                  <span>⚠️</span>
                  <span>Active Vulnerabilities ({selectedDevice.threats})</span>
                </h3>
                
                {selectedDevice.threats > 0 ? (
                  <div className="space-y-4">
                    {mockCVEs.map((cve) => (
                      <div key={cve.id} className="bg-black/40 p-4 rounded-lg border border-red-500/20">
                        <div className="flex justify-between items-start mb-2">
                          <span className="font-mono text-red-400 font-bold text-sm">{cve.id}</span>
                          <span className="bg-red-500/20 text-red-500 text-xs px-2 py-0.5 rounded font-bold">
                            CVSS {cve.score}
                          </span>
                        </div>
                        <p className="text-sm text-gray-400">{cve.desc}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-green-500 font-medium bg-green-500/10 p-4 rounded-lg border border-green-500/20">
                    No active vulnerabilities found. Device is secure.
                  </p>
                )}
              </div>

              {/* Right Column: AI CCIE Terminal */}
              <div className="w-2/3 flex flex-col p-6 bg-[#0a0a0a]">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-bold text-primary flex items-center space-x-2">
                    <span>🤖</span>
                    <span>CCIE Remediation Engine</span>
                  </h3>
                  {!isAnalyzing && selectedDevice.threats > 0 && (
                    <button 
                      onClick={triggerAI}
                      className="bg-primary hover:bg-blue-600 text-white px-4 py-2 rounded shadow text-sm font-medium transition-colors"
                    >
                      Initialize AI Analysis
                    </button>
                  )}
                </div>

                <div className="flex-1 bg-black rounded-lg border border-gray-800 p-4 font-mono text-sm overflow-y-auto relative shadow-inner">
                  {!isAnalyzing ? (
                    <div className="text-gray-500 flex flex-col items-center justify-center h-full space-y-4">
                      <span className="text-4xl">💻</span>
                      <p>System ready. Awaiting command to stream localized LLM response.</p>
                    </div>
                  ) : (
                    <div className="text-green-400 space-y-3">
                      <p className="text-gray-400">&gt; Connecting to local Llama 3.1 model...</p>
                      <p className="text-gray-400">&gt; Parsing {selectedDevice.threats} vulnerabilities...</p>
                      <br/>
                      <p className="text-white font-bold">EXECUTIVE SUMMARY:</p>
                      <p>Critical RCE vulnerability detected via Smart Install (SMI). Immediate remediation required to prevent unauthenticated payload execution.</p>
                      <br/>
                      <p className="text-white font-bold">REMEDIATION COMMANDS:</p>
                      <pre className="text-blue-300 bg-blue-900/20 p-3 rounded border border-blue-900/50 mt-2">
                        Core-Switch# configure terminal<br/>
                        Core-Switch(config)# no vstack<br/>
                        Core-Switch(config)# exit<br/>
                        Core-Switch# write memory
                      </pre>
                      <span className="animate-pulse">_</span>
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