"use client";

import { useState } from "react";
import { Bot, X, Sparkles } from "lucide-react";
import ChatPanel from "./ChatPanel";

export function CopilotFloatingButton() {
  const [isOpen, setIsOpen] = useState(false);
  const [hasUnread, setHasUnread] = useState(true); // Hook this up to your real state

  const toggleCopilot = () => {
    setIsOpen(!isOpen);
    if (!isOpen) setHasUnread(false);
  };

  return (
    <>
      {/* 1. The Omni-present Floating Button */}
      <button
        onClick={toggleCopilot}
        className={`fixed bottom-6 right-6 p-4 rounded-full shadow-2xl transition-all duration-300 z-50 flex items-center justify-center
          ${isOpen ? 'bg-gray-800 hover:bg-gray-900' : 'bg-blue-600 hover:bg-blue-700 hover:scale-105'}`}
        aria-label="Toggle AI Copilot"
      >
        {isOpen ? (
          <X className="w-6 h-6 text-white" />
        ) : (
          <div className="relative">
            <Bot className="w-6 h-6 text-white" />
            {hasUnread && (
              <span className="absolute -top-1 -right-1 flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500 border-2 border-blue-600"></span>
              </span>
            )}
          </div>
        )}
      </button>

      {/* 2. The Slide-Over Chat Interface */}
      <div 
        className={`fixed top-0 right-0 h-full w-full sm:w-[400px] bg-white shadow-[-10px_0_30px_rgba(0,0,0,0.1)] transform transition-transform duration-300 ease-in-out z-40 flex flex-col border-l border-gray-100
          ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}
      >
        <div className="p-4 border-b border-gray-100 bg-gray-50 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-blue-600" />
          <h2 className="font-semibold text-gray-800">GraftAI Copilot</h2>
        </div>
        
        {/* Render your actual chat interface here */}
        <div className="flex-1 overflow-hidden">
          {isOpen && <ChatPanel isOpen={isOpen} onClose={() => setIsOpen(false)} />} 
        </div>
      </div>
    </>
  );
}

// Export as default for backward compatibility
export default CopilotFloatingButton;
