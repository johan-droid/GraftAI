import Dexie, { type EntityTable } from 'dexie';

export interface LocalEvent {
  id: number | string;
  user_id: string;
  title: string;
  description?: string;
  category: "meeting" | "event" | "birthday" | "task";
  start_time: string;
  end_time: string;
  is_remote: boolean;
  status: string;
  meeting_platform?: string;
  meeting_link?: string;
  attendees?: string[];
  sync_status: 'synced' | 'pending' | 'failed';
  last_modified: string;
}

export interface LocalChat {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  metadata?: any;
  timestamp: string;
}

// Defining the database
class GraftAIDB extends Dexie {
  events!: EntityTable<LocalEvent, 'id'>;
  chats!: EntityTable<LocalChat, 'id'>;

  constructor() {
    super('GraftAIOfflineCache');
    this.version(2).stores({
      events: 'id, user_id, start_time, sync_status',
      chats: 'id, timestamp, metadata.intent'
    });
  }
}

export const db = new GraftAIDB();
