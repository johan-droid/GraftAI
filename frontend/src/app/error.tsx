'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { AlertTriangle } from 'lucide-react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to your Sentry/Datadog instance here
    console.error("Global UI Crash:", error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4 text-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-4">
          <AlertTriangle className="w-8 h-8" />
        </div>
        <h2 className="text-xl font-bold text-gray-900 mb-2">Something went wrong</h2>
        <p className="text-sm text-gray-500 mb-6">
          Our interface encountered an unexpected issue while communicating with the AI. 
        </p>
        
        {/* Safe reset button */}
        <Button onClick={() => reset()} className="w-full">
          Reload Interface
        </Button>
      </div>
    </div>
  );
}
