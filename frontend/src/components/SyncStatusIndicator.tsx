'use client';

import { useEffect, useState } from 'react';
import { AlertTriangle, RefreshCcw, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { apiClient } from '@/lib/api-client';

type SyncStatus = 'healthy' | 'disconnected' | 'syncing';

export function SyncStatusIndicator() {
  const [status, setStatus] = useState<SyncStatus>('syncing');

  useEffect(() => {
    const checkSyncHealth = async () => {
      try {
        const data = await apiClient.get<any>('/integrations/health');
        
        if (data.google_calendar_status === 'disconnected') {
          setStatus('disconnected');
        } else {
          setStatus('healthy');
        }
      } catch (error) {
        setStatus('disconnected');
      }
    };

    checkSyncHealth();
    // Poll every 5 minutes while the dashboard is open
    const interval = setInterval(checkSyncHealth, 300000); 
    return () => clearInterval(interval);
  }, []);

  if (status === 'healthy') {
    return (
      <div className="flex items-center gap-2 text-xs text-green-600 bg-green-50 px-3 py-1.5 rounded-full border border-green-100">
        <CheckCircle className="w-3.5 h-3.5" />
        <span>Calendar Synced</span>
      </div>
    );
  }

  if (status === 'disconnected') {
    return (
      <div className="flex items-center gap-3 text-sm text-red-700 bg-red-50 p-3 rounded-lg border border-red-200 w-full mb-6 shadow-sm">
        <AlertTriangle className="w-5 h-5 flex-shrink-0 animate-pulse" />
        <div className="flex-1">
          <p className="font-bold">Calendar Disconnected</p>
          <p className="text-xs text-red-600 mt-0.5">Your booking pages are temporarily disabled. Please reconnect your Google Calendar.</p>
        </div>
        <Button 
          variant="destructive" 
          size="sm"
          onClick={() => {
            window.location.href = '/dashboard/settings/integrations';
          }}
        >
          Fix Connection
        </Button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-xs text-gray-500">
      <RefreshCcw className="w-3.5 h-3.5 animate-spin" />
      <span>Checking sync...</span>
    </div>
  );
}

// Export as default for backward compatibility
export default SyncStatusIndicator;
