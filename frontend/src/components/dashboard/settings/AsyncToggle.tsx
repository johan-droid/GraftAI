'use client';
import { useState } from 'react';
import { Loader2 } from 'lucide-react';

interface AsyncToggleProps {
  settingKey: string;
  label: string;
  description: string;
  initialValue: boolean;
  onUpdate?: (value: boolean) => void;
}

export function AsyncToggle({ settingKey, label, description, initialValue, onUpdate }: AsyncToggleProps) {
  const [isEnabled, setIsEnabled] = useState(initialValue);
  const [isUpdating, setIsUpdating] = useState(false);

  const handleToggle = async () => {
    if (isUpdating) return;
    
    const newValue = !isEnabled;
    setIsUpdating(true);
    
    // Optimistic UI update (feels instantly responsive)
    setIsEnabled(newValue);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/user/preferences`, {
        method: 'PATCH',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [settingKey]: newValue })
      });

      if (!response.ok) throw new Error("Failed to sync setting.");
      
      // Note: Toast notification requires toast hook - for now just log
      console.log("Settings Saved: Your preferences have been updated.");
      
      if (onUpdate) {
        onUpdate(newValue);
      }
    } catch (error) {
      // THE FIX: Revert the UI if the server rejects it to prevent state desync
      setIsEnabled(!newValue);
      console.error("Sync Error: Could not save setting. Reverted to previous state.");
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-lg shadow-sm">
      <div className="pr-4 flex-1">
        <h4 className="text-sm font-semibold text-gray-900">{label}</h4>
        <p className="text-xs text-gray-500 mt-1">{description}</p>
      </div>
      
      <button 
        onClick={handleToggle}
        disabled={isUpdating}
        className={`
          relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-600 focus:ring-offset-2
          ${isEnabled ? 'bg-blue-600' : 'bg-gray-200'}
          ${isUpdating ? 'opacity-70 cursor-not-allowed' : ''}
        `}
      >
        <span className="sr-only">Toggle {label}</span>
        <span
          className={`
            pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out flex items-center justify-center
            ${isEnabled ? 'translate-x-5' : 'translate-x-0'}
          `}
        >
           {/* Spinner inside the toggle knob when syncing */}
           {isUpdating && <Loader2 className="w-3 h-3 text-blue-600 animate-spin" />}
        </span>
      </button>
    </div>
  );
}
