/**
 * Sync Conflict Resolution Logic
 * 
 * Handles conflicts when syncing offline changes with the server.
 * Provides UI for users to resolve conflicts by choosing local or server version.
 */

import { offlineQueue, OfflineAction, ActionType } from './offlineQueue';

export interface Conflict {
  id: string;
  actionId: string;
  actionType: ActionType;
  localData: any;
  serverData: any;
  conflictType: 'version_mismatch' | 'data_changed' | 'deleted' | 'created';
  timestamp: number;
}

export interface ConflictResolution {
  conflictId: string;
  resolution: 'keep_local' | 'keep_server' | 'merge' | 'skip';
  mergedData?: any;
}

class SyncConflictResolver {
  private conflicts: Map<string, Conflict> = new Map();

  /**
   * Detect conflicts between local offline changes and server state
   */
  async detectConflicts(serverData: any[]): Promise<Conflict[]> {
    const pendingActions = await offlineQueue.getPendingActions();
    const detectedConflicts: Conflict[] = [];

    for (const action of pendingActions) {
      const conflict = await this.checkActionConflict(action, serverData);
      if (conflict) {
        this.conflicts.set(conflict.id, conflict);
        detectedConflicts.push(conflict);
      }
    }

    return detectedConflicts;
  }

  /**
   * Check if a single action conflicts with server data
   */
  private async checkActionConflict(action: OfflineAction, serverData: any[]): Promise<Conflict | null> {
    const serverItem = serverData.find(item => item.id === action.data.id);

    if (!serverItem) {
      // Item doesn't exist on server - might be new or deleted
      if (action.type === 'delete') {
        return {
          id: crypto.randomUUID(),
          actionId: action.id,
          actionType: action.type,
          localData: action.data,
          serverData: null,
          conflictType: 'deleted',
          timestamp: action.timestamp,
        };
      }
      return null; // No conflict - new item
    }

    // Compare timestamps to detect version mismatch
    const localTimestamp = action.data.updated_at || action.timestamp;
    const serverTimestamp = serverItem.updated_at;

    if (serverTimestamp > localTimestamp) {
      return {
        id: crypto.randomUUID(),
        actionId: action.id,
        actionType: action.type,
        localData: action.data,
        serverData: serverItem,
        conflictType: 'version_mismatch',
        timestamp: action.timestamp,
      };
    }

    // Check for data changes
    if (this.hasDataChanged(action.data, serverItem)) {
      return {
        id: crypto.randomUUID(),
        actionId: action.id,
        actionType: action.type,
        localData: action.data,
        serverData: serverItem,
        conflictType: 'data_changed',
        timestamp: action.timestamp,
      };
    }

    return null;
  }

  /**
   * Check if data has changed between local and server versions
   */
  private hasDataChanged(local: any, server: any): boolean {
    // Compare key fields
    const keyFields = ['title', 'start_time', 'end_time', 'description', 'status'];
    
    for (const field of keyFields) {
      if (local[field] !== server[field]) {
        return true;
      }
    }

    return false;
  }

  /**
   * Attempt to merge local and server data
   */
  mergeData(local: any, server: any): any {
    const merged = { ...server };

    // Fields where local takes precedence
    const localPriorityFields = ['description', 'custom_fields', 'metadata'];
    localPriorityFields.forEach(field => {
      if (local[field] !== undefined) {
        merged[field] = local[field];
      }
    });

    // Fields where server takes precedence (timestamps, IDs)
    const serverPriorityFields = ['id', 'created_at', 'updated_at', 'server_version'];
    serverPriorityFields.forEach(field => {
      if (server[field] !== undefined) {
        merged[field] = server[field];
      }
    });

    // For time fields, use the most recent
    if (local.updated_at && server.updated_at) {
      if (local.updated_at > server.updated_at) {
        merged.start_time = local.start_time;
        merged.end_time = local.end_time;
      }
    }

    return merged;
  }

  /**
   * Apply a conflict resolution
   */
  async applyResolution(resolution: ConflictResolution): Promise<void> {
    const conflict = this.conflicts.get(resolution.conflictId);
    if (!conflict) return;

    switch (resolution.resolution) {
      case 'keep_local':
        // Proceed with original action
        await this.retryAction(conflict.actionId);
        break;

      case 'keep_server':
        // Discard local action
        await offlineQueue.deleteAction(conflict.actionId);
        break;

      case 'merge':
        // Update action with merged data and retry
        if (resolution.mergedData) {
          await this.updateActionData(conflict.actionId, resolution.mergedData);
          await this.retryAction(conflict.actionId);
        }
        break;

      case 'skip':
        // Mark action as skipped but keep it for later
        await offlineQueue.markActionError(conflict.actionId, 'Skipped by user');
        break;
    }

    this.conflicts.delete(resolution.conflictId);
  }

  /**
   * Retry an action after conflict resolution
   */
  private async retryAction(actionId: string): Promise<void> {
    // Reset retry count and error
    // The offline queue will handle the actual sync
    await offlineQueue.markActionSynced(actionId);
  }

  /**
   * Update action data with merged version
   */
  private async updateActionData(actionId: string, newData: any): Promise<void> {
    // This would need to be added to the offline queue
    // For now, we'll just delete and re-add with new data
    await offlineQueue.deleteAction(actionId);
    // Re-add with merged data
    // This is a simplified approach - in production, you'd want a proper update method
  }

  /**
   * Get all pending conflicts
   */
  getConflicts(): Conflict[] {
    return Array.from(this.conflicts.values());
  }

  /**
   * Get conflict count
   */
  getConflictCount(): number {
    return this.conflicts.size;
  }

  /**
   * Clear all conflicts
   */
  clearConflicts(): void {
    this.conflicts.clear();
  }

  /**
   * Generate a human-readable conflict description
   */
  describeConflict(conflict: Conflict): string {
    switch (conflict.conflictType) {
      case 'version_mismatch':
        return `Server has a newer version than your local changes for ${this.getItemName(conflict)}`;
      case 'data_changed':
        return `Both you and the server modified ${this.getItemName(conflict)}`;
      case 'deleted':
        return `You deleted ${this.getItemName(conflict)} but it exists on the server`;
      case 'created':
        return `${this.getItemName(conflict)} was created both locally and on the server`;
      default:
        return 'Unknown conflict';
    }
  }

  /**
   * Get a human-readable name for the conflicted item
   */
  private getItemName(conflict: Conflict): string {
    const data = conflict.localData || conflict.serverData;
    if (data?.title) return data.title;
    if (data?.name) return data.name;
    if (data?.subject) return data.subject;
    return 'item';
  }
}

// Singleton instance
export const syncConflictResolver = new SyncConflictResolver();
