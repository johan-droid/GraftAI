# 🚀 GraftAI Developer Guide

> **API-First** | **Type-Safe** | **Production-Ready** | **Developer-Friendly**

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Core Architecture](#core-architecture)
3. [API Integration](#api-integration)
4. [Feature Implementation](#feature-implementation)
5. [Advanced Patterns](#advanced-patterns)
6. [Testing & Debugging](#testing--debugging)

---

## 🚀 Quick Start

### Prerequisites

```bash
# Node.js 18+
node --version

# Python 3.11+
python --version

# PostgreSQL 14+
psql --version
```

### Project Setup

```bash
# Clone repository
git clone https://github.com/your-org/graftai.git
cd graftai

# Backend setup
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials

# Frontend setup
cd ../frontend
npm install
# or
yarn install
```

### Environment Configuration

```env
# Backend (.env)
DATABASE_URL=postgresql://user:pass@localhost/graftai
REDIS_URL=redis://localhost:6379
GROQ_API_KEY=your_groq_key
STRIPE_SECRET_KEY=sk_test_...
JWT_SECRET=your_jwt_secret

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Running Locally

```bash
# Start backend
cd backend
uvicorn api.main:app --reload --port 8000

# Start frontend (new terminal)
cd frontend
npm run dev

# Access application
open http://localhost:3000
```

---

## 🏗️ Core Architecture

### System Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend API   │────▶│   Database      │
│   (Next.js)     │◀────│   (FastAPI)     │◀────│   (PostgreSQL)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │
         │              ┌────────┴────────┐
         │              │   Services      │
         │              │   - AI/Groq     │
         │              │   - Stripe      │
         │              │   - Redis       │
         │              │   - Email       │
         │              └─────────────────┘
         │
┌────────┴────────┐
│   IndexedDB     │
│   (Offline)     │
└─────────────────┘
```

### Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Next.js 14 + React | SSR, App Router |
| Styling | Tailwind CSS | Utility-first CSS |
| Animations | Framer Motion | Gestures, transitions |
| Icons | Lucide React | Consistent iconography |
| Backend | FastAPI | Async Python API |
| ORM | SQLAlchemy 2.0 | Database operations |
| Migrations | Alembic | Schema versioning |
| AI | Groq API | LLM integration |
| Cache | Redis | Session, rate limiting |
| Queue | ARQ + Redis (legacy) + Celery | Background jobs |

> The backend currently supports both ARQ and Celery: ARQ is retained for legacy background workflows in `backend/worker.py` and `backend/services/bg_tasks.py`, while Celery is used for newer scheduled/task queue processing. This dual runtime is intentional during migration and is expected to be consolidated to Celery once the ARQ-specific flows are fully migrated.

---

## 🔌 API Integration

### Authentication

```typescript
// lib/api/client.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, refresh or redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

### Type-Safe API Calls

```typescript
// types/api.ts
export interface Booking {
  id: string;
  title: string;
  start_time: string;
  end_time: string;
  status: 'pending' | 'confirmed' | 'cancelled';
}

export interface CreateBookingRequest {
  title: string;
  start_time: string;
  end_time: string;
  attendee_email: string;
}

// lib/api/bookings.ts
import api from './client';
import type { Booking, CreateBookingRequest } from '@/types/api';

export const bookingsApi = {
  async list(): Promise<Booking[]> {
    const { data } = await api.get('/api/v1/bookings');
    return data;
  },

  async create(booking: CreateBookingRequest): Promise<Booking> {
    const { data } = await api.post('/api/v1/bookings', booking);
    return data;
  },

  async update(id: string, updates: Partial<Booking>): Promise<Booking> {
    const { data } = await api.put(`/api/v1/bookings/${id}`, updates);
    return data;
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/api/v1/bookings/${id}`);
  },
};
```

### React Query Integration

```typescript
// hooks/useBookings.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { bookingsApi } from '@/lib/api/bookings';

export function useBookings() {
  return useQuery({
    queryKey: ['bookings'],
    queryFn: bookingsApi.list,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useCreateBooking() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: bookingsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings'] });
    },
  });
}
```

### WebSocket Real-time Updates

```typescript
// hooks/useWebSocket.ts
import { useEffect, useRef, useState } from 'react';

export function useWebSocket(url: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<MessageEvent | null>(null);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const socket = new WebSocket(`${url}?token=${token}`);
    
    socket.onopen = () => setIsConnected(true);
    socket.onclose = () => setIsConnected(false);
    socket.onmessage = (event) => setLastMessage(event);
    
    ws.current = socket;

    return () => socket.close();
  }, [url]);

  const send = (data: unknown) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(data));
    }
  };

  return { isConnected, lastMessage, send };
}

// Usage for real-time notifications
export function useNotifications() {
  const { lastMessage } = useWebSocket(
    process.env.NEXT_PUBLIC_WS_URL + '/notifications'
  );

  useEffect(() => {
    if (lastMessage) {
      const notification = JSON.parse(lastMessage.data);
      // Show toast notification
      toast.info(notification.title, {
        description: notification.message,
      });
    }
  }, [lastMessage]);
}
```

---

## 🎯 Feature Implementation

### 1. Calendar Integration

```typescript
// components/Calendar/CalendarView.tsx
'use client';

import { useState } from 'react';
import { Calendar as BigCalendar, dateFnsLocalizer } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay } from 'date-fns';
import enUS from 'date-fns/locale/en-US';
import { useBookings } from '@/hooks/useBookings';
import { DashboardSkeleton } from '@/components/Loading/SkeletonLoader';

const locales = {
  'en-US': enUS,
};

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek,
  getDay,
  locales,
});

export default function CalendarView() {
  const { data: bookings, isLoading } = useBookings();
  const [selectedEvent, setSelectedEvent] = useState(null);

  const events = bookings?.map((booking) => ({
    id: booking.id,
    title: booking.title,
    start: new Date(booking.start_time),
    end: new Date(booking.end_time),
    status: booking.status,
  })) || [];

  if (isLoading) return <DashboardSkeleton />;

  return (
    <div className="h-[600px] bg-slate-800/50 rounded-xl p-4">
      <BigCalendar
        localizer={localizer}
        events={events}
        startAccessor="start"
        endAccessor="end"
        onSelectEvent={setSelectedEvent}
        eventPropGetter={(event) => ({
          className: `rounded-lg px-2 py-1 text-sm ${
            event.status === 'confirmed'
              ? 'bg-green-500/20 text-green-400 border border-green-500/30'
              : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
          }`,
        })}
      />
      
      {selectedEvent && (
        <EventModal
          event={selectedEvent}
          onClose={() => setSelectedEvent(null)}
        />
      )}
    </div>
  );
}
```

### 2. AI Chat Integration

```typescript
// components/AIChat/useAIChat.ts
import { useState, useCallback } from 'react';
import { useMutation } from '@tanstack/react-query';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export function useAIChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const sendMessage = useMutation({
    mutationFn: async (prompt: string) => {
      setIsStreaming(true);
      
      // Add user message
      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: 'user',
        content: prompt,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMessage]);

      // Call API
      const response = await fetch('/api/v1/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          prompt,
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        }),
      });

      const data = await response.json();

      // Add assistant message
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: data.result,
        timestamp: new Date(),
      };
      
      setMessages((prev) => [...prev, assistantMessage]);
      setIsStreaming(false);

      return data;
    },
  });

  return {
    messages,
    isStreaming,
    sendMessage: sendMessage.mutate,
    isLoading: sendMessage.isPending,
  };
}
```

### 3. Offline-First Forms

```typescript
// components/Forms/OfflineForm.tsx
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNetworkStatus } from '@/hooks/useNetworkStatus';
import { offlineQueue } from '@/lib/offlineQueue';
import { toast } from 'sonner';

const bookingSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  start_time: z.string().min(1, 'Start time is required'),
  end_time: z.string().min(1, 'End time is required'),
  attendee_email: z.string().email('Invalid email'),
});

type BookingFormData = z.infer<typeof bookingSchema>;

export default function OfflineBookingForm() {
  const { isOnline } = useNetworkStatus();
  const { register, handleSubmit, formState: { errors }, reset } = useForm<BookingFormData>({
    resolver: zodResolver(bookingSchema),
  });

  const onSubmit = async (data: BookingFormData) => {
    try {
      if (isOnline) {
        // Submit directly
        const response = await fetch('/api/v1/bookings', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
          body: JSON.stringify(data),
        });

        if (!response.ok) throw new Error('Failed to create booking');
        
        toast.success('Booking created successfully');
      } else {
        // Queue for offline sync
        await offlineQueue.addAction('create', data);
        toast.success('Saved offline. Will sync when connected.');
      }

      reset();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Something went wrong');
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {!isOnline && (
        <div className="bg-amber-500/20 border border-amber-500/50 rounded-lg p-3">
          <p className="text-amber-400 text-sm">
            You're offline. Changes will sync when you reconnect.
          </p>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-slate-300 mb-1">
          Title
        </label>
        <input
          {...register('title')}
          className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-4 py-2 text-white"
        />
        {errors.title && (
          <p className="text-red-400 text-sm mt-1">{errors.title.message}</p>
        )}
      </div>

      {/* More fields... */}

      <button
        type="submit"
        className="w-full py-3 bg-blue-600 hover:bg-blue-700 rounded-xl text-white font-medium transition-colors"
      >
        {isOnline ? 'Create Booking' : 'Save Offline'}
      </button>
    </form>
  );
}
```

### 4. Real-time Notifications

```typescript
// components/Notifications/NotificationCenter.tsx
'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Bell, X, Check } from 'lucide-react';

interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  read: boolean;
  timestamp: Date;
}

export default function NotificationCenter() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket(
      `${process.env.NEXT_PUBLIC_WS_URL}/notifications?token=${localStorage.getItem('access_token')}`
    );

    ws.onmessage = (event) => {
      const notification = JSON.parse(event.data);
      setNotifications((prev) => [notification, ...prev]);
    };

    return () => ws.close();
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const markAsRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  };

  const clearAll = () => {
    setNotifications([]);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 hover:bg-slate-800 rounded-lg transition-colors"
      >
        <Bell className="w-5 h-5 text-slate-400" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 rounded-full text-xs text-white flex items-center justify-center">
            {unreadCount}
          </span>
        )}
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            className="absolute right-0 top-full mt-2 w-80 bg-slate-800 rounded-xl border border-slate-700 shadow-xl z-50"
          >
            <div className="flex items-center justify-between p-4 border-b border-slate-700">
              <h3 className="font-semibold text-white">Notifications</h3>
              <button
                onClick={clearAll}
                className="text-sm text-slate-400 hover:text-white"
              >
                Clear all
              </button>
            </div>

            <div className="max-h-80 overflow-y-auto">
              {notifications.length === 0 ? (
                <p className="text-slate-500 text-center py-8">
                  No notifications
                </p>
              ) : (
                notifications.map((notification) => (
                  <div
                    key={notification.id}
                    className={`p-4 border-b border-slate-700/50 hover:bg-slate-700/50 transition-colors ${
                      !notification.read ? 'bg-blue-500/5' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-white font-medium text-sm">
                          {notification.title}
                        </p>
                        <p className="text-slate-400 text-sm mt-1">
                          {notification.message}
                        </p>
                        <p className="text-slate-500 text-xs mt-2">
                          {new Date(notification.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                      {!notification.read && (
                        <button
                          onClick={() => markAsRead(notification.id)}
                          className="p-1 hover:bg-slate-600 rounded"
                        >
                          <Check className="w-4 h-4 text-blue-400" />
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
```

---

## 🔧 Advanced Patterns

### Error Boundary

```typescript
// components/ErrorBoundary.tsx
'use client';

import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
    // Send to error tracking service
  }

  public render() {
    if (this.state.hasError) {
      return (
        this.props.fallback || (
          <div className="flex flex-col items-center justify-center min-h-screen p-4">
            <h2 className="text-xl font-bold text-white mb-2">
              Something went wrong
            </h2>
            <p className="text-slate-400 mb-4">
              {this.state.error?.message}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-600 rounded-lg text-white"
            >
              Reload page
            </button>
          </div>
        )
      );
    }

    return this.props.children;
  }
}
```

### Custom Hooks Library

```typescript
// hooks/useDebounce.ts
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}

// hooks/useLocalStorage.ts
export function useLocalStorage<T>(key: string, initialValue: T) {
  const [storedValue, setStoredValue] = useState<T>(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch {
      return initialValue;
    }
  });

  const setValue = (value: T | ((val: T) => T)) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error(error);
    }
  };

  return [storedValue, setValue] as const;
}

// hooks/useMediaQuery.ts
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const media = window.matchMedia(query);
    if (media.matches !== matches) setMatches(media.matches);
    const listener = () => setMatches(media.matches);
    media.addEventListener('change', listener);
    return () => media.removeEventListener('change', listener);
  }, [matches, query]);

  return matches;
}

// hooks/usePrevious.ts
export function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T>();
  useEffect(() => {
    ref.current = value;
  }, [value]);
  return ref.current;
}
```

### Performance Optimizations

```typescript
// components/VirtualizedList.tsx
'use client';

import { useRef, useCallback } from 'react';
import { useVirtualizer } from '@tanstack/react-virtual';

interface VirtualizedListProps<T> {
  data: T[];
  renderItem: (item: T, index: number) => React.ReactNode;
  itemHeight: number;
  overscan?: number;
}

export default function VirtualizedList<T>({
  data,
  renderItem,
  itemHeight,
  overscan = 5,
}: VirtualizedListProps<T>) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: data.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => itemHeight,
    overscan,
  });

  return (
    <div ref={parentRef} className="h-full overflow-auto">
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: '100%',
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualItem.size}px`,
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            {renderItem(data[virtualItem.index], virtualItem.index)}
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 🧪 Testing & Debugging

### Component Testing

```typescript
// __tests__/components/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import Button from '@/components/Button';

describe('Button', () => {
  it('renders correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('handles click events', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalled();
  });
});
```

### API Testing

```typescript
// __tests__/api/bookings.test.ts
import { bookingsApi } from '@/lib/api/bookings';

// Mock the API client
jest.mock('@/lib/api/client');

describe('Bookings API', () => {
  it('fetches bookings', async () => {
    const mockBookings = [
      { id: '1', title: 'Meeting 1' },
      { id: '2', title: 'Meeting 2' },
    ];
    
    // Mock the API response
    require('@/lib/api/client').default.get.mockResolvedValue({
      data: mockBookings,
    });

    const bookings = await bookingsApi.list();
    expect(bookings).toHaveLength(2);
  });
});
```

### E2E Testing with Playwright

```typescript
// e2e/booking.spec.ts
import { test, expect } from '@playwright/test';

test('create booking flow', async ({ page }) => {
  await page.goto('/dashboard');
  
  // Click create button
  await page.click('[data-testid="create-booking-btn"]');
  
  // Fill form
  await page.fill('[name="title"]', 'Test Meeting');
  await page.fill('[name="start_time"]', '2025-04-15T10:00');
  await page.fill('[name="end_time"]', '2025-04-15T11:00');
  
  // Submit
  await page.click('[type="submit"]');
  
  // Verify success
  await expect(page.locator('[data-testid="success-toast"]')).toBeVisible();
});
```

### Debugging Tools

```typescript
// lib/debug.ts
export const debug = {
  log: (label: string, data: unknown) => {
    if (process.env.NODE_ENV === 'development') {
      console.log(`[${label}]`, data);
    }
  },

  time: (label: string) => {
    if (process.env.NODE_ENV === 'development') {
      console.time(label);
    }
  },

  timeEnd: (label: string) => {
    if (process.env.NODE_ENV === 'development') {
      console.timeEnd(label);
    }
  },
};

// Usage
import { debug } from '@/lib/debug';

debug.time('fetchBookings');
const bookings = await fetchBookings();
debug.timeEnd('fetchBookings');
debug.log('Bookings loaded', bookings);
```

---

## 📚 Additional Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [React Query Guide](https://tanstack.com/query/latest/docs/react/overview)
- [Tailwind CSS Cheatsheet](https://nerdcave.com/tailwind-cheat-sheet)
- [Framer Motion Examples](https://www.framer.com/motion/examples/)

---

*Last updated: April 2025*
