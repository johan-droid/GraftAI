## 2024-05-18 - [O(N) Complexity in React Render Loops]
**Learning:** Re-evaluating large collections (like filtering 100+ events and parsing multiple Date objects) within a grid mapping (like a 35-day calendar grid) creates an O(N*M) time complexity during *each* render frame, drastically reducing UI responsiveness. The calendar view previously executed Date parses thousands of times per re-render.
**Action:** Always pre-process flat lists into lookup maps (e.g. `Map<number, Event[]>`) using `useMemo` *before* the render loop, achieving O(1) lookups per grid cell.

## 2024-05-18 - [Intl.DateTimeFormat vs toLocaleString in Render Loops]
**Learning:** Using `Date.prototype.toLocaleTimeString()` or `Date.prototype.toLocaleDateString()` inside a render loop (especially within nested `.map()` functions like rendering calendar events) is a massive performance bottleneck. These methods instantiate a new internal formatter on every call, taking roughly ~0.7-1ms per call. For 1000 events, this takes ~750ms and completely blocks the main thread.
**Action:** Always pre-instantiate and cache `Intl.DateTimeFormat` objects outside of React components. Calling `.format()` on a cached formatter is ~200x faster than calling `.toLocaleString()`.
