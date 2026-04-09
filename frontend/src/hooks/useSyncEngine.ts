import { useEffect, useState } from 'react';
import { db } from '@/lib/db';
import { sendAiChat } from '@/lib/api';
import { toast } from 'sonner';

export function useSyncEngine() {
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);

  useEffect(() => {
    // Initial check
    setIsOnline(navigator.onLine);

    const setOnline = () => {
      setIsOnline(true);
      toast.success('Back online. Syncing offline changes...');
      syncOfflineData();
    };
    
    const setOffline = () => {
      setIsOnline(false);
      toast.warning('You are offline. AI Chat will use template mode.');
    };

    window.addEventListener('online', setOnline);
    window.addEventListener('offline', setOffline);

    return () => {
      window.removeEventListener('online', setOnline);
      window.removeEventListener('offline', setOffline);
    };
  }, []);

  const syncOfflineData = async () => {
    if (isSyncing || !navigator.onLine) return;
    
    try {
      setIsSyncing(true);
      
      // Drain the offline intents (chats) from Dexie
      const pendingIntents = await db.chats.where('metadata.intent').equals('offline_schedule').toArray();
      
      if (pendingIntents.length === 0) {
        setIsSyncing(false);
        return;
      }

      for (const intent of pendingIntents) {
        // Build the prompt for the backend API
        try {
          const promptPayload = `[OFFLINE SYNC] Schedule the following: ${JSON.stringify(intent.metadata.payload)}`;
          await sendAiChat(promptPayload, Intl.DateTimeFormat().resolvedOptions().timeZone);
          
          // Mark as synced or delete from local DB
          await db.chats.delete(intent.id);
        } catch (error) {
          console.error('Failed to sync intent:', intent, error);
        }
      }
      
      toast.success(`Successfully synced ${pendingIntents.length} offline meetings.`);
    } catch (error) {
      console.error('Sync process failed', error);
      toast.error('Sync failed. Will retry later.');
    } finally {
      setIsSyncing(false);
    }
  };

  return { isOnline, isSyncing, syncOfflineData };
}
