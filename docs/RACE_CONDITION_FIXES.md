# Race Condition & Cache Poisoning Fixes - Implementation Summary

## Overview
This document details the implementation of four critical phases to eliminate race conditions and cache poisoning in the GraftAI booking system.

---

## Phase 1: Offline Booking Mirage - Fail Fast for Critical Mutations

### Problem
Users could queue booking requests while offline (e.g., on subway). When reconnecting, the backend would reject the booking due to DB locks, causing silent failures after users thought their meeting was confirmed.

### Solution
**File Modified:** `frontend/src/lib/api-client-enhanced.ts`

**Implementation:**
```typescript
const CRITICAL_MUTATION_ENDPOINTS = ['/api/v1/bookings', '/api/v1/payments'];

// In fetchWithOfflineSupport method:
const isCritical = CRITICAL_MUTATION_ENDPOINTS.some(critical => endpoint.includes(critical));
const isPostOrPut = options.method === "POST" || options.method === "PUT";

if (!networkMonitor.isOnline() && isCritical && isPostOrPut) {
  throw new Error("OFFLINE_CRITICAL: You must be online to confirm a booking or make a payment.");
}
```

**Result:** Critical booking and payment mutations now fail immediately when offline, preventing false confirmations.

---

## Phase 2: Double-Click Race Conditions - Idempotency Keys

### Problem
Impatient users double-clicking "Confirm Booking" would send concurrent POST requests, bypassing UI loading states and creating duplicate bookings.

### Solution
**File Modified:** `frontend/src/app/(public)/book/page.tsx`

**Implementation:**
1. **Generate idempotency key once on form mount:**
```typescript
import { v4 as uuidv4 } from 'uuid';

const idempotencyKey = useRef(uuidv4());
```

2. **UI safeguard against double-clicks:**
```typescript
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  if (isSubmitting) return; // Prevent concurrent submissions
  setIsSubmitting(true);
  // ...
}
```

3. **Send idempotency key with request:**
```typescript
const booking = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/public/${username}/${eventType}/book`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "X-Idempotency-Key": idempotencyKey.current,
  },
  body: JSON.stringify({...})
});
```

**Dependencies Added:**
- `uuid`: ^11.0.5
- `@types/uuid`: ^10.0.0

**Result:** Each booking form generates a unique idempotency key. Backend can detect and reject duplicate requests with the same key.

---

## Phase 3: Next.js Cache Poisoning on Availability

### Problem
Next.js App Router aggressively caches fetch calls by default. Users would see stale availability data (e.g., 3:00 PM slot shown as available when it was booked 10 minutes ago).

### Solution

#### 3A: Cache-Busted Availability Fetcher
**File Modified:** `frontend/src/lib/availability/calendar.ts`

```typescript
export async function getAvailableSlots(username: string, date: string) {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/availability?user=${username}&date=${date}`, {
    cache: 'no-store', // NON-NEGOTIABLE FOR SCHEDULING APPS
    headers: {
      'Content-Type': 'application/json'
    }
  });

  if (!res.ok) throw new Error('Failed to fetch availability');
  return res.json();
}
```

#### 3B: Force Dynamic Rendering
**File Created:** `frontend/src/app/(public)/[username]/[event_type]/layout.tsx`

```typescript
export const dynamic = 'force-dynamic';
export const revalidate = 0;

export default function BookingLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
```

**Result:** 
- All availability fetches bypass Next.js cache
- Booking pages are never statically generated
- Users always see real-time availability

---

## Phase 4: Service Worker Caching Exclusions

### Problem
Service worker could cache public booking pages, serving stale HTML with outdated availability data.

### Solution
**File Modified:** `frontend/src/sw.ts`

**Implementation:**
```typescript
self.addEventListener("fetch", (event: FetchEvent) => {
  const url = new URL(event.request.url);
  
  // Bypass API routes
  if (url.pathname.startsWith("/api/")) {
    event.stopImmediatePropagation();
    event.respondWith(fetch(event.request));
    return;
  }
  
  // PHASE 4: Bypass booking routes (/:username/:event_type and /book)
  const bookingRoutePattern = /^\/[^/]+\/[^/]+$/; // Matches /:username/:event_type
  if (bookingRoutePattern.test(url.pathname) || url.pathname.startsWith("/book")) {
    event.stopImmediatePropagation();
    event.respondWith(fetch(event.request));
    return;
  }
});
```

**Result:** Service worker uses NetworkOnly strategy for all booking routes, ensuring fresh data.

---

## Installation Instructions

1. **Install dependencies:**
```bash
cd frontend
npm install
```

2. **Rebuild service worker:**
```bash
npm run build
```

3. **Clear browser cache and service workers:**
- Open DevTools → Application → Service Workers → Unregister
- Clear Site Data
- Hard refresh (Ctrl+Shift+R / Cmd+Shift+R)

---

## Backend Requirements

To fully support these changes, the backend must implement:

### 1. Idempotency Key Handling
**File:** `backend/api/bookings.py` (or equivalent)

```python
from fastapi import Header

@router.post("/api/v1/public/{username}/{event_type}/book")
async def book_public_event(
    username: str,
    event_type: str,
    payload: BookingCreate,
    x_idempotency_key: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    # Check if this idempotency key was already processed
    if x_idempotency_key:
        result = await db.execute(
            select(BookingTable).where(
                BookingTable.idempotency_key == x_idempotency_key
            )
        )
        booking = result.scalar_one_or_none()
        if booking:
            # Return the cached booking instead of creating a duplicate
            return booking
    
    # Create new booking with idempotency key
    booking = BookingTable(
        id=generate_uuid(),
        idempotency_key=x_idempotency_key,
        # ... other fields
    )
    # ...
```

### 2. Database Migration
Add idempotency_key column to bookings table:

```sql
ALTER TABLE bookings ADD COLUMN idempotency_key VARCHAR(255) UNIQUE;
CREATE INDEX idx_bookings_idempotency_key ON bookings(idempotency_key);
```

---

## Testing Checklist

### Phase 1: Offline Booking
- [ ] Disconnect network
- [ ] Try to book a slot
- [ ] Verify immediate error: "You must be online to confirm a booking"
- [ ] Verify no request is queued

### Phase 2: Double-Click Protection
- [ ] Rapidly click "Confirm Booking" multiple times
- [ ] Verify only one booking is created
- [ ] Check backend logs for duplicate idempotency key rejection

### Phase 3: Cache Busting
- [ ] Book a slot
- [ ] Immediately refresh the availability page
- [ ] Verify the booked slot is no longer shown
- [ ] Check Network tab: cache should be "no-store"

### Phase 4: Service Worker
- [ ] Open DevTools → Application → Service Workers
- [ ] Navigate to booking page
- [ ] Verify requests bypass service worker (check Network tab)
- [ ] Verify no booking routes are cached

---

## Performance Impact

### Positive
- **Eliminated race conditions:** No more duplicate bookings
- **Real-time accuracy:** Users always see current availability
- **Better UX:** Clear offline error messages

### Neutral
- **Slightly more network requests:** Availability data is never cached
- **Minimal overhead:** Idempotency key generation is negligible

### Mitigation
- Backend should implement aggressive caching with short TTLs (5-10 seconds)
- Use Redis for idempotency key storage with automatic expiration
- Consider implementing optimistic UI updates with rollback

---

## Monitoring & Alerts

### Metrics to Track
1. **Duplicate booking attempts:** Count of rejected idempotency keys
2. **Offline booking attempts:** Count of OFFLINE_CRITICAL errors
3. **Cache hit rate:** Should be 0% for availability endpoints
4. **Booking success rate:** Should increase after implementation

### Recommended Alerts
- Alert if duplicate bookings > 5% of total bookings
- Alert if offline booking attempts spike (indicates UX issue)
- Alert if availability cache hit rate > 0%

---

## Rollback Plan

If issues arise:

1. **Revert Phase 2 (Idempotency):**
   - Remove `X-Idempotency-Key` header from booking request
   - Keep UI safeguard (`if (isSubmitting) return`)

2. **Revert Phase 3 (Cache Busting):**
   - Remove `cache: 'no-store'` from availability fetcher
   - Delete layout.tsx with `dynamic = 'force-dynamic'`

3. **Revert Phase 4 (Service Worker):**
   - Remove booking route bypass from sw.ts
   - Rebuild and redeploy service worker

4. **Revert Phase 1 (Offline Fail-Fast):**
   - Remove CRITICAL_MUTATION_ENDPOINTS check
   - Allow offline queueing for all mutations

---

## Future Enhancements

1. **Optimistic Locking:** Add version numbers to availability data
2. **WebSocket Updates:** Push real-time availability changes to clients
3. **Conflict Resolution UI:** Show alternative slots when booking fails
4. **Rate Limiting:** Prevent abuse of idempotency key generation
5. **Analytics:** Track booking funnel drop-off rates

---

## References

- [Next.js Data Fetching](https://nextjs.org/docs/app/building-your-application/data-fetching/fetching-caching-and-revalidating)
- [Service Worker API](https://developer.mozilla.org/en-US/docs/Web/API/Service_Worker_API)
- [Idempotency Keys Best Practices](https://stripe.com/docs/api/idempotent_requests)
- [HTTP Caching](https://developer.mozilla.org/en-US/docs/Web/HTTP/Caching)

---

**Status:** ✅ IMPLEMENTED
**Last Updated:** 2025-01-21
**Author:** GraftAI Engineering Team
