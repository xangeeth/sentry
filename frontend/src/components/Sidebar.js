import React from 'react';

const Sidebar = ({ activeTab, setActiveTab }) => {
  const menuItems = [
    { id: 'dashboard', label: 'Fleet Dashboard', icon: '📊' },
    { id: 'scanner', label: 'Universal Scanner', icon: '🔍' },
    { id: 'assistant', label: 'AI Assistant', icon: '🤖' },
  ];

  return (
    <div className="w-64 bg-surface h-screen border-r border-gray-700 flex flex-col">
      <div className="p-6 border-b border-gray-800">
        <h2 className="text-2xl font-bold text-primary tracking-wider">SENTRY</h2>
        <p className="text-xs text-gray-400 mt-1">v1.0.0-Enterprise</p>
      </div>
      
      <nav className="flex-1 px-4 space-y-2 mt-6">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setActiveTab(item.id)}
            className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 ${
              activeTab === item.id
                ? 'bg-primary/10 text-primary border border-primary/20 shadow-sm'
                : 'text-gray-400 hover:bg-gray-800 hover:text-white'
            }`}
          >
            <span className="text-xl">{item.icon}</span>
            <span className="font-medium tracking-wide">{item.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
};

export default Sidebar;