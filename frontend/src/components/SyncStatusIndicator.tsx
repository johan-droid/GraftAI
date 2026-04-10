/**
 * Sync Status Indicator Component
 * 
 * Visual indicator showing sync status (Synced, Syncing, Offline, Error)
 * with pending action count and manual sync trigger.
 */

'use client';

import { useNetworkStatus, SyncStatus } from '@/hooks/useNetworkStatus';
import { useState } from 'react';
import { offlineQueue } from '@/lib/offlineQueue';

export default function SyncStatusIndicator() {
  const status = useNetworkStatus();
  const [isSyncing, setIsSyncing] = useState(false);

  const handleManualSync = async () => {
    if (isSyncing || !status.isOnline) return;
    
    setIsSyncing(true);
    try {
      await offlineQueue.manualSync();
    } catch (error) {
      console.error('Manual sync failed:', error);
    } finally {
      setIsSyncing(false);
    }
  };

  const getStatusConfig = (syncStatus: SyncStatus) => {
    switch (syncStatus) {
      case 'synced':
        return {
          icon: '✓',
          color: 'text-green-500',
          bgColor: 'bg-green-500/10',
          borderColor: 'border-green-500/30',
          label: 'Synced',
          showPending: false,
        };
      case 'syncing':
        return {
          icon: '⟳',
          color: 'text-blue-500',
          bgColor: 'bg-blue-500/10',
          borderColor: 'border-blue-500/30',
          label: 'Syncing',
          showPending: true,
          animate: true,
        };
      case 'offline':
        return {
          icon: '⚡',
          color: 'text-amber-500',
          bgColor: 'bg-amber-500/10',
          borderColor: 'border-amber-500/30',
          label: 'Offline',
          showPending: true,
        };
      case 'error':
        return {
          icon: '⚠',
          color: 'text-red-500',
          bgColor: 'bg-red-500/10',
          borderColor: 'border-red-500/30',
          label: 'Sync Error',
          showPending: true,
        };
    }
  };

  const config = getStatusConfig(status.syncStatus);

  const formatLastSync = (timestamp: number | null) => {
    if (!timestamp) return 'Never';
    const diff = Date.now() - timestamp;
    const minutes = Math.floor(diff / 60000);
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  return (
    <div className={`fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-2 rounded-lg border backdrop-blur-sm transition-all duration-300 ${config.bgColor} ${config.borderColor} ${config.color}`}>
      {/* Status Icon */}
      <span className={`text-lg ${config.animate ? 'animate-spin' : ''}`}>
        {config.icon}
      </span>

      {/* Status Label */}
      <span className="text-sm font-medium">{config.label}</span>

      {/* Pending Count */}
      {config.showPending && status.pendingCount > 0 && (
        <span className="px-2 py-0.5 text-xs font-bold rounded-full bg-current text-white">
          {status.pendingCount}
        </span>
      )}

      {/* Last Sync Time */}
      {status.isOnline && status.lastSyncTime && (
        <span className="text-xs opacity-70 ml-2 hidden sm:inline">
          Last: {formatLastSync(status.lastSyncTime)}
        </span>
      )}

      {/* Manual Sync Button */}
      {status.isOnline && status.pendingCount > 0 && (
        <button
          onClick={handleManualSync}
          disabled={isSyncing}
          className="ml-2 px-2 py-1 text-xs font-medium rounded bg-current text-white hover:opacity-80 disabled:opacity-50 transition-opacity"
        >
          {isSyncing ? 'Syncing...' : 'Sync Now'}
        </button>
      )}

      {/* Offline Indicator */}
      {!status.isOnline && (
        <span className="text-xs opacity-70 ml-2 hidden sm:inline">
          Working offline
        </span>
      )}
    </div>
  );
}
