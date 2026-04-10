/**
 * Network Status Hook
 * 
 * Provides network connectivity status and sync state for offline mode.
 */

import { useState, useEffect } from 'react';
import { offlineQueue } from '@/lib/offlineQueue';

export type SyncStatus = 'synced' | 'syncing' | 'offline' | 'error';

export interface NetworkStatus {
  isOnline: boolean;
  syncStatus: SyncStatus;
  pendingCount: number;
  lastSyncTime: number | null;
}

export function useNetworkStatus(): NetworkStatus {
  const [status, setStatus] = useState<NetworkStatus>({
    isOnline: true,
    syncStatus: 'synced',
    pendingCount: 0,
    lastSyncTime: null,
  });

  useEffect(() => {
    let mounted = true;

    const updateStatus = async () => {
      if (!mounted) return;

      const syncStatus = await offlineQueue.getSyncStatus();
      
      setStatus(prev => ({
        isOnline: syncStatus.isOnline,
        syncStatus: syncStatus.isOnline 
          ? (syncStatus.pendingCount > 0 ? 'syncing' : 'synced')
          : 'offline',
        pendingCount: syncStatus.pendingCount,
        lastSyncTime: syncStatus.lastSyncTime,
      }));
    };

    // Initial status
    updateStatus();

    // Subscribe to offline queue changes
    const unsubscribe = offlineQueue.subscribe(updateStatus);

    // Periodic refresh
    const interval = setInterval(updateStatus, 5000);

    return () => {
      mounted = false;
      unsubscribe();
      clearInterval(interval);
    };
  }, []);

  return status;
}
