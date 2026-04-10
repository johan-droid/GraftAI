# 🎨 GraftAI Frontend Documentation

> **Mobile-First** | **Minimalist Design** | **Buttery Smooth** | **Developer-Friendly**

## 📱 Core Design Philosophy

### Mobile-First Approach
Every component is designed for mobile first, then enhanced for larger screens:
- **Touch targets**: Minimum 44x44px for all interactive elements
- **Gestures**: Swipe, pull-to-refresh, long-press actions
- **Bottom navigation**: Thumb-friendly navigation on mobile
- **Responsive grids**: Flexible layouts that adapt to any screen size

### Minimalist UI Principles
- **Clean surfaces**: Dark theme with glassmorphism effects
- **Whitespace**: Generous padding and breathing room
- **Typography**: Clear hierarchy with consistent font weights
- **Colors**: Limited palette with purposeful accent usage
- **Animations**: Subtle, purposeful motion that guides users

### Buttery Smooth Interactions
- **Page transitions**: Blur fade with spring physics
- **Loading states**: Shimmer skeletons with gradient effects
- **Micro-interactions**: Scale, opacity, and position animations
- **60fps**: GPU-accelerated transforms and opacity changes

---

## 🧩 Component Library

### Loading Components

#### `PageTransition`
Full-page loading overlay with animated logo and particle effects.

```tsx
import PageTransition from '@/components/Loading/PageTransition';

<PageTransition isLoading={isLoading}>
  <YourPageContent />
</PageTransition>
```

**Features:**
- Animated gradient logo with glow effect
- Floating particle background
- Typing indicator animation
- Blur fade content reveal

#### Skeleton Loaders
Content-aware loading placeholders with shimmer effects.

```tsx
import { 
  DashboardSkeleton, 
  EventItemSkeleton, 
  TableSkeleton 
} from '@/components/Loading/SkeletonLoader';

// Full page loading
<DashboardSkeleton />

// Individual components
<EventItemSkeleton />
<TableSkeleton rows={5} />
```

**Available Skeletons:**
- `DashboardSkeleton` - Full dashboard layout
- `EventItemSkeleton` - List item placeholder
- `CalendarDaySkeleton` - Calendar day view
- `StatsRowSkeleton` - Statistics row
- `TableSkeleton` - Data table
- `ChatMessageSkeleton` - Chat message
- `FormSkeleton` - Form fields

### Mobile Components

#### `BottomNav`
Thumb-friendly bottom navigation with floating action button.

```tsx
import BottomNav from '@/components/Mobile/BottomNav';

// Add to your layout
<BottomNav />
```

**Features:**
- Active state indicators with spring animation
- Floating action button with glow effect
- Safe area support for notched devices
- Smooth icon transitions

#### `PullToRefresh`
Native-like pull-to-refresh for mobile lists.

```tsx
import PullToRefresh from '@/components/Mobile/PullToRefresh';

<PullToRefresh onRefresh={async () => await fetchData()}>
  <YourList />
</PullToRefresh>
```

**Features:**
- Elastic pull animation
- Progress indicator bar
- Rotating refresh icon
- Spring physics release

#### `SwipeableCard`
Reveal actions with swipe gestures.

```tsx
import SwipeableCard from '@/components/Mobile/SwipeableCard';

<SwipeableCard
  onDelete={() => handleDelete()}
  onEdit={() => handleEdit()}
  onComplete={() => handleComplete()}
>
  <YourCardContent />
</SwipeableCard>
```

**Features:**
- Left swipe: Delete action
- Right swipe: Edit/Complete actions
- Spring snap back animation
- Visual feedback during swipe

### AI Components

#### `FloatingAIButton`
Floating action button for AI assistant with ripple effect.

```tsx
import FloatingAIButton from '@/components/AIChat/FloatingButton';

// Add to your layout
<FloatingAIButton />
```

#### `ChatPanel`
Full-featured AI chat interface with streaming responses.

**Features:**
- Quick action buttons
- Message history
- Typing indicators
- Markdown rendering

#### `AIInsightWidgets`
Dashboard widgets showing AI-powered insights.

**Features:**
- Optimal meeting time suggestions
- Conflict predictions
- Productivity scores
- Resource utilization recommendations
- Dismissible with animation

### Automation Components

#### `AutomationDashboard`
Manage AI automation rules and view execution history.

**Features:**
- Rule statistics
- Toggle enable/disable
- Activity feed with confidence scores
- Rule editor integration

#### `RuleEditor`
Visual automation rule builder.

**Features:**
- Condition builder
- Action selector
- Confidence threshold slider
- Test functionality
- Template support

### Sync Components

#### `SyncStatusIndicator`
Real-time sync status with manual trigger.

```tsx
import SyncStatusIndicator from '@/components/SyncStatusIndicator';

// Add to your layout (top-right recommended)
<SyncStatusIndicator />
```

**Features:**
- Online/offline status
- Pending action count
- Last sync timestamp
- Manual sync button
- Visual badges for each state

---

## 🎨 Design System

### Color Palette

```css
/* Primary Colors */
--color-primary: #3B82F6;      /* Blue 500 */
--color-primary-dark: #1D4ED8; /* Blue 700 */

/* Accent Colors */
--color-accent-purple: #8B5CF6; /* Purple 500 */
--color-accent-pink: #EC4899;   /* Pink 500 */

/* Background Colors */
--color-bg-dark: #0F172A;       /* Slate 900 */
--color-bg-card: #1E293B;       /* Slate 800 */
--color-bg-elevated: #334155;   /* Slate 700 */

/* Text Colors */
--color-text-primary: #F8FAFC;   /* Slate 50 */
--color-text-secondary: #94A3B8; /* Slate 400 */
--color-text-muted: #64748B;     /* Slate 500 */

/* Semantic Colors */
--color-success: #10B981; /* Emerald 500 */
--color-warning: #F59E0B; /* Amber 500 */
--color-error: #EF4444;   /* Red 500 */
```

### Typography Scale

| Style | Size | Weight | Usage |
|-------|------|--------|-------|
| Display | 2.5rem (40px) | 700 | Page titles |
| H1 | 2rem (32px) | 700 | Section headers |
| H2 | 1.5rem (24px) | 600 | Card titles |
| H3 | 1.25rem (20px) | 600 | Subsection |
| Body | 1rem (16px) | 400 | Paragraphs |
| Small | 0.875rem (14px) | 400 | Labels |
| Caption | 0.75rem (12px) | 500 | Metadata |

### Spacing Scale

```css
--space-1: 0.25rem;  /* 4px */
--space-2: 0.5rem;   /* 8px */
--space-3: 0.75rem;  /* 12px */
--space-4: 1rem;     /* 16px */
--space-5: 1.25rem;  /* 20px */
--space-6: 1.5rem;   /* 24px */
--space-8: 2rem;     /* 32px */
--space-10: 2.5rem;  /* 40px */
--space-12: 3rem;    /* 48px */
```

### Border Radius

```css
--radius-sm: 0.375rem;  /* 6px */
--radius-md: 0.5rem;    /* 8px */
--radius-lg: 0.75rem;   /* 12px */
--radius-xl: 1rem;      /* 16px */
--radius-2xl: 1.5rem;   /* 24px */
```

### Shadows & Glassmorphism

```css
/* Card Shadow */
--shadow-card: 0 4px 6px -1px rgba(0, 0, 0, 0.3);

/* Elevated Shadow */
--shadow-elevated: 0 10px 15px -3px rgba(0, 0, 0, 0.4);

/* Glassmorphism */
.glass {
  background: rgba(30, 41, 59, 0.7);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
}
```

---

## 🚀 Animation System

### Spring Physics

```tsx
const spring = {
  type: 'spring',
  stiffness: 300,
  damping: 30,
};

const bounce = {
  type: 'spring',
  stiffness: 400,
  damping: 10,
};
```

### Page Transitions

```tsx
const pageTransition = {
  initial: { opacity: 0, filter: 'blur(10px)' },
  animate: { opacity: 1, filter: 'blur(0px)' },
  exit: { opacity: 0, filter: 'blur(10px)' },
  transition: { duration: 0.5, ease: [0.4, 0, 0.2, 1] }
};
```

### Micro-interactions

```tsx
// Hover scale
<motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>

// Fade in up
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ delay: 0.1 }}
>

// Stagger children
<motion.div variants={container}>
  {items.map((item) => (
    <motion.div key={item.id} variants={item} />
  ))}
</motion.div>
```

---

## 📋 Developer Use Cases

### 1. Dashboard Implementation

```tsx
import PageTransition from '@/components/Loading/PageTransition';
import { DashboardSkeleton } from '@/components/Loading/SkeletonLoader';
import InsightWidgets from '@/components/AIInsights/InsightWidgets';
import SyncStatusIndicator from '@/components/SyncStatusIndicator';
import FloatingAIButton from '@/components/AIChat/FloatingButton';

export default function Dashboard() {
  const [isLoading, setIsLoading] = useState(true);
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchDashboardData().then((data) => {
      setData(data);
      setIsLoading(false);
    });
  }, []);

  return (
    <PageTransition isLoading={isLoading}>
      <div className="min-h-screen bg-slate-950 pb-20 lg:pb-0">
        <SyncStatusIndicator />
        
        <main className="p-4 sm:p-6 lg:p-8 space-y-6">
          <header className="flex items-center justify-between">
            <h1 className="text-2xl sm:text-3xl font-bold text-white">
              Dashboard
            </h1>
          </header>

          {/* AI Insights */}
          <InsightWidgets />

          {/* Main Content */}
          {isLoading ? (
            <DashboardSkeleton />
          ) : (
            <DashboardContent data={data} />
          )}
        </main>

        <FloatingAIButton />
      </div>
    </PageTransition>
  );
}
```

### 2. Mobile List with Pull-to-Refresh

```tsx
import PullToRefresh from '@/components/Mobile/PullToRefresh';
import SwipeableCard from '@/components/Mobile/SwipeableCard';
import { EventItemSkeleton } from '@/components/Loading/SkeletonLoader';

export default function EventList() {
  const [events, setEvents] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const refreshData = async () => {
    const data = await fetchEvents();
    setEvents(data);
  };

  return (
    <div className="min-h-screen bg-slate-950">
      <PullToRefresh onRefresh={refreshData}>
        <div className="p-4 space-y-3">
          {isLoading ? (
            <>
              <EventItemSkeleton />
              <EventItemSkeleton />
              <EventItemSkeleton />
            </>
          ) : (
            events.map((event) => (
              <SwipeableCard
                key={event.id}
                onDelete={() => deleteEvent(event.id)}
                onEdit={() => editEvent(event.id)}
              >
                <EventCard event={event} />
              </SwipeableCard>
            ))
          )}
        </div>
      </PullToRefresh>

      <BottomNav />
    </div>
  );
}
```

### 3. Offline-Aware Form

```tsx
import { useNetworkStatus } from '@/hooks/useNetworkStatus';
import { offlineQueue } from '@/lib/offlineQueue';

export default function BookingForm() {
  const { isOnline, pendingCount } = useNetworkStatus();
  const [formData, setFormData] = useState({});

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (isOnline) {
      // Submit directly
      await createBooking(formData);
    } else {
      // Queue for later sync
      await offlineQueue.addAction('create', formData);
      toast.success('Saved offline. Will sync when online.');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4 p-4">
      {!isOnline && (
        <div className="bg-amber-500/20 border border-amber-500/50 rounded-lg p-3 flex items-center gap-2">
          <WifiOff className="w-5 h-5 text-amber-400" />
          <span className="text-amber-400 text-sm">
            Working offline. {pendingCount} changes pending.
          </span>
        </div>
      )}

      {/* Form fields */}
      
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

### 4. Animation Wrapper Component

```tsx
'use client';

import { motion } from 'framer-motion';

interface AnimatedListProps {
  children: React.ReactNode;
  staggerDelay?: number;
}

export function AnimatedList({ children, staggerDelay = 0.05 }: AnimatedListProps) {
  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={{
        hidden: { opacity: 0 },
        visible: {
          opacity: 1,
          transition: {
            staggerChildren: staggerDelay,
          },
        },
      }}
    >
      {children}
    </motion.div>
  );
}

export function AnimatedItem({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0 },
      }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
    >
      {children}
    </motion.div>
  );
}

// Usage
<AnimatedList staggerDelay={0.1}>
  {items.map((item) => (
    <AnimatedItem key={item.id}>
      <Card data={item} />
    </AnimatedItem>
  ))}
</AnimatedList>
```

---

## 🔧 Utility Hooks

### `useNetworkStatus`

```tsx
import { useNetworkStatus } from '@/hooks/useNetworkStatus';

function MyComponent() {
  const { isOnline, syncStatus, pendingCount, lastSyncTime } = useNetworkStatus();

  return (
    <div>
      <span>{isOnline ? 'Online' : 'Offline'}</span>
      <span>{pendingCount} pending changes</span>
    </div>
  );
}
```

### `useOfflineQueue`

```tsx
import { offlineQueue } from '@/lib/offlineQueue';

// Add action to queue
await offlineQueue.addAction('create', { title: 'Meeting', ... });

// Get pending count
const count = await offlineQueue.getActionCount();

// Manual sync
await offlineQueue.manualSync();
```

---

## 📱 Responsive Breakpoints

```css
/* Mobile First Approach */

/* Base - Mobile */
/* Styles for screens < 640px */

/* sm - Small tablets */
@media (min-width: 640px) { }

/* md - Tablets */
@media (min-width: 768px) { }

/* lg - Desktop */
@media (min-width: 1024px) { }

/* xl - Large desktop */
@media (min-width: 1280px) { }

/* 2xl - Extra large */
@media (min-width: 1536px) { }
```

### Common Responsive Patterns

```tsx
// Grid that goes from 1 col (mobile) to 4 cols (desktop)
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">

// Padding that increases on larger screens
<div className="p-4 sm:p-6 lg:p-8">

// Text size that scales
<h1 className="text-xl sm:text-2xl lg:text-3xl">

// Show/hide based on screen size
<div className="hidden lg:block"> {/* Desktop only */}
<div className="lg:hidden"> {/* Mobile only */}
```

---

## 🎭 Best Practices

### Performance
- Use `transform` and `opacity` for animations (GPU-accelerated)
- Lazy load components with `dynamic` imports
- Use `will-change` sparingly on animated elements
- Implement virtual scrolling for long lists

### Accessibility
- Maintain 4.5:1 contrast ratio for text
- Use semantic HTML elements
- Add `aria-label` to icon-only buttons
- Support keyboard navigation
- Test with screen readers

### Mobile UX
- Keep primary actions within thumb reach
- Use bottom sheets for secondary actions
- Implement haptic feedback where appropriate
- Test on real devices, not just simulators

### Offline First
- Always assume the user might be offline
- Queue actions for later sync
- Show clear offline indicators
- Allow users to retry failed syncs

---

## 📚 Additional Resources

- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Framer Motion API](https://www.framer.com/motion/)
- [Next.js App Router](https://nextjs.org/docs/app)
- [Web Animations API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Animations_API)

---

*Last updated: April 2025*
