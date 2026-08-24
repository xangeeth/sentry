import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import FleetDashboard from './components/FleetDashboard';
import UniversalScanner from './components/UniversalScanner';
import AIAssistant from './components/AIAssistant';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="min-h-screen bg-background text-white flex font-sans">
      
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 p-10 overflow-y-auto">
        
        {activeTab === 'dashboard' && <FleetDashboard />}
        {activeTab === 'scanner' && <UniversalScanner />}
        {activeTab === 'assistant' && <AIAssistant />}

      </main>
    </div>
  );
}

export default App;