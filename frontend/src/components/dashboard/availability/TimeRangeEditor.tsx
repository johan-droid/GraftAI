'use client';
import { useState, useEffect } from 'react';
import { Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';

// Utility to generate 15-min interval strings (e.g., "09:00", "09:15")
const generateTimeSlots = () => {
  const slots = [];
  for (let i = 0; i < 24; i++) {
    for (let j = 0; j < 60; j += 15) {
      const h = i.toString().padStart(2, '0');
      const m = j.toString().padStart(2, '0');
      slots.push(`${h}:${m}`);
    }
  }
  return slots;
};

const TIME_SLOTS = generateTimeSlots();

export interface TimeRange {
  start: string;
  end: string;
}

export function TimeRangeEditor({ dayName, initialRanges, onChange }: { dayName: string, initialRanges: TimeRange[], onChange: (ranges: TimeRange[]) => void }) {
  const [ranges, setRanges] = useState<TimeRange[]>(initialRanges);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setRanges(initialRanges);
  }, [initialRanges]);

  const validateAndSetRanges = (newRanges: TimeRange[]) => {
    setError(null);
    
    for (const range of newRanges) {
      // 1. Prevent End Time before Start Time
      if (range.start >= range.end) {
        setError("End time must be after start time.");
        return;
      }
    }
    
    // 2. (Optional) Add overlap detection logic here if you want to be extra strict
    
    setRanges(newRanges);
    onChange(newRanges);
  };

  const updateRange = (index: number, field: 'start' | 'end', value: string) => {
    const updated = [...ranges];
    const updatedRange = { ...updated[index], [field]: value };
    updated[index] = updatedRange;
    validateAndSetRanges(updated);
  };

  const addRange = () => validateAndSetRanges([...ranges, { start: "09:00", end: "17:00" }]);
  
  const removeRange = (index: number) => {
    const updated = ranges.filter((_, i) => i !== index);
    validateAndSetRanges(updated);
  };

  const isAvailable = ranges.length > 0;

  return (
    <div className="flex items-start gap-4 py-3 border-b border-gray-100 last:border-0">
      {/* Day Toggle */}
      <div className="w-28 flex items-center gap-3 pt-1">
        <input 
          type="checkbox" 
          checked={isAvailable}
          onChange={(e) => validateAndSetRanges(e.target.checked ? [{ start: "09:00", end: "17:00" }] : [])}
          className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
        />
        <span className={`text-sm font-medium ${isAvailable ? 'text-gray-900' : 'text-gray-400'}`}>
          {dayName}
        </span>
      </div>

      {/* Time Selectors */}
      <div className="flex-1 space-y-2">
        {!isAvailable ? (
          <div className="text-sm text-gray-400 pt-1">Unavailable</div>
        ) : (
          ranges.map((range, index) => (
            <div key={index} className="flex items-center gap-2">
              <select 
                value={range.start} 
                onChange={(e) => updateRange(index, 'start', e.target.value)}
                className="border-gray-200 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500 p-1.5"
              >
                {TIME_SLOTS.map(time => <option key={`start-${time}`} value={time}>{time}</option>)}
              </select>
              <span className="text-gray-400">-</span>
              <select 
                value={range.end} 
                onChange={(e) => updateRange(index, 'end', e.target.value)}
                className="border-gray-200 rounded-md text-sm focus:ring-blue-500 focus:border-blue-500 p-1.5"
              >
                {TIME_SLOTS.map(time => <option key={`end-${time}`} value={time}>{time}</option>)}
              </select>
              
              <button onClick={() => removeRange(index)} className="p-1.5 text-gray-400 hover:text-red-500 transition-colors">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))
        )}
        
        {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
        
        {isAvailable && (
          <button onClick={addRange} className="flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700 mt-2">
            <Plus className="w-3 h-3" /> Add hours
          </button>
        )}
      </div>
    </div>
  );
}
