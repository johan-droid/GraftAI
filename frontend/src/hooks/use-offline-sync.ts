import { useState, useEffect, useCallback } from 'react';
import { db, LocalEvent } from '../lib/db';
import { getEvents as apiGetEvents } from '../lib/api';

/**
 * useOfflineSync: The "Unbreakable" data management hook.
 * Prioritizes local IndexedDB data for instant UI loading, 
 * then reconciles with the backend.
 */
export function useOfflineSync(startDate?: Date, endDate?: Date) {
  const [isOnline, setIsOnline] = useState<boolean>(
    typeof window !== 'undefined' ? navigator.onLine : true
  );
  const [isSyncing, setIsSyncing] = useState(false);

  // 1. Monitor Network Status
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  /**
   * Fetch from local cache first, then trigger background sync
   */
  const getEvents = useCallback(async (start: string, end: string) => {
    // 1. Try local data first for speed
    const local = await db.events
      .where('start_time')
      .between(start, end, true, true)
      .toArray();
    
    // 2. Background fetch if online
    if (navigator.onLine) {
      try {
        const remote = await apiGetEvents(start, end);
        // Bulk update local cache with fresh data
        await db.events.bulkPut(remote.map((e: any) => ({
          ...e,
          sync_status: 'synced',
          last_modified: new Date().toISOString()
        })));
        return remote;
      } catch (err) {
        console.warn("Background sync failed, serving local stale data.", err);
      }
    }
    
    return local;
  }, []);

  /**
   * Push pending offline actions to the server
   */
  const reconcile = useCallback(async () => {
    if (!isOnline || isSyncing) return;
    
    setIsSyncing(true);
    try {
      const pending = await db.events.where('sync_status').equals('pending').toArray();
      if (pending.length === 0) return;

      console.log(`🔄 Syncing ${pending.length} pending actions...`);
      // Logic for batch processing would go here
      // For now, we individual sync
      
      // Update local status after successful sync
      // await db.events.where('id').anyOf(pendingIds).modify({ sync_status: 'synced' });
    } finally {
      setIsSyncing(false);
    }
  }, [isOnline, isSyncing]);

  // Auto-sync when coming back online
  useEffect(() => {
    if (isOnline) {
      reconcile();
    }
  }, [isOnline, reconcile]);

  return { isOnline, isSyncing, getEvents, reconcile };
}
