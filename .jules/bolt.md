## 2024-05-18 - [O(N) Complexity in React Render Loops]
**Learning:** Re-evaluating large collections (like filtering 100+ events and parsing multiple Date objects) within a grid mapping (like a 35-day calendar grid) creates an O(N*M) time complexity during *each* render frame, drastically reducing UI responsiveness. The calendar view previously executed Date parses thousands of times per re-render.
**Action:** Always pre-process flat lists into lookup maps (e.g. `Map<number, Event[]>`) using `useMemo` *before* the render loop, achieving O(1) lookups per grid cell.
