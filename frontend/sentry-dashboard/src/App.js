import React, { useState } from 'react';

function App() {
  const [ipAddress, setIpAddress] = useState('');
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin');
  
  const [status, setStatus] = useState('idle'); // idle, discovering, complete, error
  const [logs, setLogs] = useState([]);
  const [result, setResult] = useState(null);

  const handleDiscovery = async (e) => {
    e.preventDefault();
    if (!ipAddress) return;

    setStatus('discovering');
    setLogs(['Initiating secure SSH connection via Netmiko...']);
    setResult(null);

    try {
      // Hitting your Python FastAPI Backend
      const response = await fetch('http://127.0.0.1:8000/api/v1/discover', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ip_address: ipAddress,
          username: username,
          password: password
        })
      });

      const data = await response.json();

      if (data.status === 'success') {
        setLogs(prev => [...prev, 'Configuration extracted. AI Analysis complete.']);
        setStatus('complete');
        setResult(data);
      } else {
        setLogs(prev => [...prev, `Error: ${data.message}`]);
        setStatus('error');
      }

    } catch (error) {
      setLogs(prev => [...prev, 'Connection to Sentry API failed. Is Uvicorn running?']);
      setStatus('error');
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 p-8 text-slate-200 font-sans">
      <div className="max-w-5xl mx-auto space-y-8">
        
        {/* Header */}
        <header className="border-b border-slate-700 pb-6">
          <h1 className="text-3xl font-bold tracking-tight text-blue-400">PROJECT SENTRY</h1>
          <p className="text-slate-400 mt-1">Enterprise Switch Auditor & AI Analysis</p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          
          {/* Discovery Form Control Panel */}
          <div className="col-span-1 bg-slate-800 rounded-lg p-6 border border-slate-700 shadow-xl">
            <h2 className="text-xl font-semibold mb-6">Network Discovery</h2>
            
            <form onSubmit={handleDiscovery} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Target IP Address</label>
                <input 
                  type="text" 
                  value={ipAddress}
                  onChange={(e) => setIpAddress(e.target.value)}
                  placeholder="192.168.x.x" 
                  className="w-full bg-slate-900 border border-slate-600 rounded p-2 focus:border-blue-500 focus:outline-none"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-1">Username</label>
                  <input 
                    type="text" 
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-600 rounded p-2 focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-1">Password</label>
                  <input 
                    type="password" 
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-600 rounded p-2 focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              <button 
                type="submit" 
                disabled={status === 'discovering'}
                className="w-full mt-6 bg-blue-600 hover:bg-blue-500 text-white font-medium py-2 px-4 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {status === 'discovering' ? 'Auditing Network...' : 'Run Discovery'}
              </button>
            </form>

            {/* Pipeline Status Logs */}
            {status !== 'idle' && (
              <div className="mt-8 p-4 bg-slate-900 rounded border border-slate-700 font-mono text-sm">
                <div className="flex items-center gap-2 mb-2">
                  <span className={`h-2 w-2 rounded-full ${status === 'discovering' ? 'bg-yellow-400 animate-pulse' : status === 'complete' ? 'bg-green-500' : 'bg-red-500'}`}></span>
                  <span className="text-slate-400">System Logs</span>
                </div>
                <ul className="space-y-1 text-slate-300">
                  {logs.map((log, i) => (
                    <li key={i}>{log}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* AI Analysis Display Panel */}
          <div className="col-span-1 md:col-span-2 bg-slate-800 rounded-lg p-6 border border-slate-700 shadow-xl min-h-[500px]">
            {status === 'idle' && (
              <div className="h-full flex flex-col items-center justify-center text-slate-500">
                <svg className="w-16 h-16 mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
                <p>Awaiting network discovery...</p>
              </div>
            )}

            {status === 'discovering' && (
              <div className="h-full flex flex-col items-center justify-center text-blue-400 animate-pulse">
                <p className="text-lg">Analyzing Threat Intelligence...</p>
              </div>
            )}

            {status === 'complete' && result && (
              <div className="space-y-6">
                <div className="flex justify-between items-start border-b border-slate-700 pb-4">
                  <div>
                    <h2 className="text-2xl font-bold text-white">{result.message}</h2>
                    <p className="text-slate-400 mt-1">Audit complete. Results securely logged to Sentry Database.</p>
                  </div>
                  <div className={`px-4 py-2 rounded font-bold ${result.threats > 0 ? 'bg-red-500/20 text-red-400 border border-red-500/50' : 'bg-green-500/20 text-green-400 border border-green-500/50'}`}>
                    {result.threats} CVEs Found
                  </div>
                </div>

                <div className="prose prose-invert max-w-none">
                  <pre className="whitespace-pre-wrap font-sans text-slate-300 leading-relaxed bg-slate-900 p-4 rounded border border-slate-700">
                    {result.ai_summary}
                  </pre>
                </div>
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}

export default App;