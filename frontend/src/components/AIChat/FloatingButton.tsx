"use client";

import { useState } from "react";
import { MessageCircle, Sparkles, X } from "lucide-react";
import ChatPanel from "./ChatPanel";

export default function FloatingAIButton() {
  const [isOpen, setIsOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  return (
    <>
      {/* Floating Action Button (Material 3 Style) */}
      <button
        type="button"
        aria-label={isOpen ? "Close AI chat" : "Open AI chat"}
        onClick={() => setIsOpen(!isOpen)}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className={`fixed bottom-6 right-6 z-50 w-14 h-14 rounded-[18px] flex items-center justify-center transition-all duration-300 ${isHovered && !isOpen ? "shadow-2xl" : ""}`}
        style={isOpen ? { background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', color: 'var(--text-secondary)', transform: 'rotate(90deg)' } : { background: 'var(--primary)', color: '#fff' }}
      >
        {isOpen ? (
          <X className="w-6 h-6" />
        ) : (
          <div className="relative">
            <MessageCircle className="w-6 h-6" />
            <Sparkles className="w-3 h-3 text-yellow-200 absolute -top-1 -right-1" />
          </div>
        )}
      </button>

      {/* Slide-out Chat Panel */}
      <ChatPanel isOpen={isOpen} onClose={() => setIsOpen(false)} />
    </>
  );
}
