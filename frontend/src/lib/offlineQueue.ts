/**
 * Offline Action Queue System
 * 
 * Stores user actions in IndexedDB when offline and syncs when network returns.
 * Actions include: create event, update event, delete event, reschedule, etc.
 */

export type ActionType = 'create' | 'update' | 'delete' | 'reschedule' | 'book_resource' | 'cancel_booking';

export interface OfflineAction {
  id: string;
  type: ActionType;
  timestamp: number;
  data: any;
  synced: boolean;
  syncError?: string;
  retryCount: number;
}

const DB_NAME = 'GraftAIOffline';
const DB_VERSION = 1;
const STORE_NAME = 'actions';

class OfflineQueue {
  private db: IDBDatabase | null = null;
  private isOnline: boolean = navigator.onLine;
  private syncInProgress: boolean = false;
  private listeners: Set<() => void> = new Set();

  constructor() {
    this.init();
    this.setupNetworkListeners();
  }

  private async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          const store = db.createObjectStore(STORE_NAME, { keyPath: 'id' });
          store.createIndex('synced', 'synced', { unique: false });
          store.createIndex('timestamp', 'timestamp', { unique: false });
          store.createIndex('type', 'type', { unique: false });
        }
      };
    });
  }

  private setupNetworkListeners(): void {
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.notifyListeners();
      this.syncPendingActions();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
      this.notifyListeners();
    });
  }

  public getOnlineStatus(): boolean {
    return this.isOnline;
  }

  public subscribe(listener: () => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => listener());
  }

  public async addAction(type: ActionType, data: any): Promise<string> {
    if (!this.db) await this.init();

    const action: OfflineAction = {
      id: crypto.randomUUID(),
      type,
      timestamp: Date.now(),
      data,
      synced: false,
      retryCount: 0,
    };

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.add(action);

      request.onsuccess = () => {
        this.notifyListeners();
        if (this.isOnline && !this.syncInProgress) {
          this.syncPendingActions();
        }
        resolve(action.id);
      };
      request.onerror = () => reject(request.error);
    });
  }

  public async getPendingActions(): Promise<OfflineAction[]> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readonly');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.getAll();

      request.onsuccess = () => {
        const actions = (request.result as OfflineAction[])
          .filter(action => !action.synced)
          .sort((a, b) => a.timestamp - b.timestamp);
        resolve(actions);
      };
      request.onerror = () => reject(request.error);
    });
  }

  public async getActionCount(): Promise<number> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readonly');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.getAll();

      request.onsuccess = () => {
        const actions = request.result as OfflineAction[];
        const pendingCount = actions.filter(action => !action.synced).length;
        resolve(pendingCount);
      };
      request.onerror = () => reject(request.error);
    });
  }

  public async markActionSynced(actionId: string): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.get(actionId);

      request.onsuccess = () => {
        const action = request.result as OfflineAction;
        if (action) {
          action.synced = true;
          action.syncError = undefined;
          const updateRequest = store.put(action);
          updateRequest.onsuccess = () => {
            this.notifyListeners();
            resolve();
          };
          updateRequest.onerror = () => reject(updateRequest.error);
        } else {
          resolve();
        }
      };
      request.onerror = () => reject(request.error);
    });
  }

  public async markActionError(actionId: string, error: string): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.get(actionId);

      request.onsuccess = () => {
        const action = request.result as OfflineAction;
        if (action) {
          action.syncError = error;
          action.retryCount += 1;
          const updateRequest = store.put(action);
          updateRequest.onsuccess = () => {
            this.notifyListeners();
            resolve();
          };
          updateRequest.onerror = () => reject(updateRequest.error);
        } else {
          resolve();
        }
      };
      request.onerror = () => reject(request.error);
    });
  }

  public async deleteAction(actionId: string): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.delete(actionId);

      request.onsuccess = () => {
        this.notifyListeners();
        resolve();
      };
      request.onerror = () => reject(request.error);
    });
  }

  public async clearSyncedActions(): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const index = store.index('synced');
      const request = index.openCursor(IDBKeyRange.only(true));

      request.onsuccess = (event) => {
        const cursor = (event.target as IDBRequest).result;
        if (cursor) {
          cursor.delete();
          cursor.continue();
        } else {
          this.notifyListeners();
          resolve();
        }
      };
      request.onerror = () => reject(request.error);
    });
  }

  public async syncPendingActions(): Promise<void> {
    if (!this.isOnline || this.syncInProgress) return;

    this.syncInProgress = true;
    const actions = await this.getPendingActions();

    for (const action of actions) {
      // Skip actions with too many retries
      if (action.retryCount >= 5) {
        await this.markActionError(action.id, 'Max retries exceeded');
        continue;
      }

      try {
        await this.executeAction(action);
        await this.markActionSynced(action.id);
      } catch (error) {
        await this.markActionError(action.id, error instanceof Error ? error.message : 'Unknown error');
      }
    }

    // Clean up synced actions
    await this.clearSyncedActions();
    this.syncInProgress = false;
    this.notifyListeners();
  }

  private async executeAction(action: OfflineAction): Promise<void> {
    // SECURITY FIX: Use credentials:include instead of localStorage token
    // httpOnly cookies are sent automatically for auth
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    let endpoint = '';
    let method: 'POST' | 'PUT' | 'DELETE' = 'POST';

    switch (action.type) {
      case 'create':
        endpoint = '/api/v1/events';
        method = 'POST';
        break;
      case 'update':
        endpoint = `/api/v1/events/${action.data.id}`;
        method = 'PUT';
        break;
      case 'delete':
        endpoint = `/api/v1/events/${action.data.id}`;
        method = 'DELETE';
        break;
      case 'reschedule':
        endpoint = `/api/v1/events/${action.data.id}/reschedule`;
        method = 'POST';
        break;
      case 'book_resource':
        endpoint = '/api/v1/resources/bookings';
        method = 'POST';
        break;
      case 'cancel_booking':
        endpoint = `/api/v1/resources/bookings/${action.data.id}/cancel`;
        method = 'POST';
        break;
      default:
        throw new Error(`Unknown action type: ${action.type}`);
    }

    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}`, {
      method,
      headers,
      credentials: 'include', // Sends httpOnly cookies automatically
      body: method !== 'DELETE' ? JSON.stringify(action.data) : undefined,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(error || 'Sync failed');
    }

    return response.json();
  }

  public async getSyncStatus(): Promise<{
    isOnline: boolean;
    pendingCount: number;
    lastSyncTime: number | null;
  }> {
    const pendingCount = await this.getActionCount();
    
    // Get last sync time from localStorage
    const lastSyncTime = localStorage.getItem('last_sync_time')
      ? parseInt(localStorage.getItem('last_sync_time')!)
      : null;

    return {
      isOnline: this.isOnline,
      pendingCount,
      lastSyncTime,
    };
  }

  public async manualSync(): Promise<void> {
    if (!this.isOnline) {
      throw new Error('Cannot sync while offline');
    }

    await this.syncPendingActions();
    localStorage.setItem('last_sync_time', Date.now().toString());
    this.notifyListeners();
  }
}

// Singleton instance
export const offlineQueue = new OfflineQueue();
