'use client';

import { useState } from 'react';
import { format, parseISO } from 'date-fns';
import { formatInTimeZone } from 'date-fns-tz';
import { Button } from '@/components/ui/Button';

interface TimeSlot {
  start_time_utc: string; // Must be standard ISO Z (e.g. 2026-05-10T14:00:00Z)
  end_time_utc: string;
  is_available: boolean;
}

export function AvailabilityGrid({ 
  slots, 
  onSlotSelect 
}: { 
  slots: TimeSlot[], 
  onSlotSelect: (slot: TimeSlot) => void 
}) {
  const [selectedSlot, setSelectedSlot] = useState<string | null>(null);
  
  // 1. Automatically detect the user's local timezone
  const userTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  const handleSelect = (slot: TimeSlot) => {
    setSelectedSlot(slot.start_time_utc);
    onSlotSelect(slot); // Passes the raw UTC data back up to the booking form
  };

  if (!slots || slots.length === 0) {
    return (
      <div className="p-8 text-center bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-gray-500 font-medium">No availability on this date.</p>
        <p className="text-sm text-gray-400 mt-1">Please select another day from the calendar.</p>
      </div>
    );
  }

  return (
    <div className="w-full">
      <div className="mb-4 text-sm text-gray-600 flex items-center gap-2">
        <span>Times shown in:</span>
        <span className="font-semibold text-gray-900 bg-gray-100 px-2 py-1 rounded">
          {userTimezone.replace('_', ' ')}
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
        {slots.map((slot) => {
          // 2. Safely parse the UTC string
          const dateObj = parseISO(slot.start_time_utc);
          
          // 3. Format explicitly to the user's localized timezone
          const displayTime = formatInTimeZone(dateObj, userTimezone, 'h:mm a');
          const isSelected = selectedSlot === slot.start_time_utc;

          return (
            <button
              key={slot.start_time_utc}
              disabled={!slot.is_available}
              onClick={() => handleSelect(slot)}
              className={`
                relative py-3 px-4 rounded-md text-sm font-medium transition-all duration-200 border
                ${!slot.is_available 
                  ? 'bg-gray-50 text-gray-400 border-gray-100 cursor-not-allowed line-through' 
                  : isSelected
                    ? 'bg-blue-600 text-white border-blue-600 shadow-md transform scale-[1.02]'
                    : 'bg-white text-blue-600 border-blue-200 hover:border-blue-600 hover:bg-blue-50'
                }
              `}
            >
              {displayTime}
            </button>
          );
        })}
      </div>
    </div>
  );
}
