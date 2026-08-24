import React, { useState } from 'react';
import { sentryAPI } from '../api';

const AIAssistant = () => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState([
    { role: 'system', content: 'System initialized. Security Engine online. Awaiting network configuration queries.' }
  ]);
  const [isTyping, setIsTyping] = useState(false);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userText = input; // Save the text before clearing the input

    // 1. Add user message to chat and reset UI
    const newMessages = [...messages, { role: 'user', content: userText }];
    setMessages(newMessages);
    setInput('');
    setIsTyping(true);

    try {
      // 2. Reach out to the real FastAPI backend via sentryAPI
      const data = await sentryAPI.askAssistant(userText);

      // 3. Append response to the chat
      setMessages((prev) => [
        ...prev,
        { 
          role: 'ai', 
          content: data?.ai_response || "Command processed successfully."
        }
      ]);

    } catch (error) {
      console.error("Failed to reach the AI:", error);
      setMessages((prev) => [
        ...prev,
        { role: 'ai', content: "⚠️ SYSTEM ERROR: Connection to Project Sentry backend failed." }
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="animate-fade-in flex flex-col h-[85vh] max-w-5xl mx-auto">
      
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2 flex items-center space-x-3">
          <span>🤖</span>
          <span>AI Configuration Assistant</span>
        </h1>
        <p className="text-gray-400">
          Enter plain-English instructions to generate vendor-specific CLI syntax.
        </p>
      </div>

      {/* The Chat/Terminal Window */}
      <div className="flex-1 bg-[#0a0a0a] rounded-t-xl border border-gray-700 shadow-2xl p-6 overflow-y-auto font-mono text-sm flex flex-col space-y-6">
        {messages.map((msg, index) => (
          <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] p-4 rounded-lg border ${
              msg.role === 'user' 
                ? 'bg-primary/20 border-primary/30 text-white' 
                : msg.role === 'system'
                  ? 'bg-gray-800/50 border-gray-700 text-gray-500 w-full text-center'
                  : 'bg-black border-gray-800 text-green-400 w-full shadow-inner'
            }`}>
              {msg.role === 'user' ? (
                <p>{msg.content}</p>
              ) : (
                <pre className="whitespace-pre-wrap font-mono">{msg.content}</pre>
              )}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-black border border-gray-800 text-green-400 max-w-[80%] p-4 rounded-lg shadow-inner w-full">
              <span className="animate-pulse">Processing request...</span>
            </div>
          </div>
        )}
      </div>

      {/* The Input Area */}
      <div className="bg-surface p-4 rounded-b-xl border-x border-b border-gray-700 shadow-xl">
        <form onSubmit={handleSend} className="flex space-x-4">
          <input 
            type="text" 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="e.g., Create VLAN 10 named HR and assign to port Gig0/1..." 
            className="flex-1 bg-[#0f172a] border border-gray-600 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-primary transition-colors font-mono text-sm"
          />
          <button 
            type="submit"
            disabled={isTyping}
            className="bg-primary hover:bg-blue-600 disabled:bg-blue-800 text-white px-8 py-3 rounded-lg font-bold transition-colors shadow-lg shadow-primary/20 flex items-center space-x-2"
          >
            <span>Execute</span>
            <span>&rarr;</span>
          </button>
        </form>
      </div>

    </div>
  );
};

export default AIAssistant;