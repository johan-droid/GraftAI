/**
 * Floating AI Assistant Button
 * 
- Glassmorphism design matching existing theme
- Smooth animations
- Badge for unread notifications
 */

'use client';

import { useState } from 'react';
import { MessageCircle, Sparkles, X } from 'lucide-react';
import ChatPanel from './ChatPanel';

export default function FloatingAIButton() {
  const [isOpen, setIsOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  return (
    <>
      {/* Floating Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className={`fixed bottom-6 right-6 z-50 w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-300 ${
          isOpen
            ? 'bg-slate-800 rotate-45 shadow-lg'
            : 'bg-gradient-to-br from-blue-600 to-purple-600 shadow-xl hover:shadow-2xl hover:scale-110'
        } ${isHovered && !isOpen ? 'scale-110' : ''}`}
      >
        {isOpen ? (
          <X className="w-6 h-6 text-white" />
        ) : (
          <div className="relative">
            <MessageCircle className="w-6 h-6 text-white" />
            <Sparkles className="w-3 h-3 text-yellow-300 absolute -top-1 -right-1" />
          </div>
        )}
      </button>

      {/* Chat Panel */}
      <ChatPanel isOpen={isOpen} onClose={() => setIsOpen(false)} />

      {/* Ripple Effect */}
      {!isOpen && (
        <div className="fixed bottom-6 right-6 w-14 h-14 rounded-2xl bg-blue-500/30 animate-ping z-40" />
      )}
    </>
  );
}
