## 2025-05-06 - Search Accessibility
**Learning:** Added an `aria-label` attribute directly to the raw `<input>` field used for searching in `Topbar.tsx`. It's a highly visible element missing essential screen reader support.
**Action:** Always check global navigation elements like search inputs for proper labels.
