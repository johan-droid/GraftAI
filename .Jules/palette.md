## 2024-05-07 - Accessible Topbar Interactive Elements
**Learning:** Custom interactive elements (links, buttons, search inputs) in layout components often lack native `focus-visible` styles and proper ARIA labels, making keyboard navigation difficult and screen reading impossible.
**Action:** Always verify that every custom interactive element in a navigation bar has an explicit `aria-label` (if icon-only or generic) and a clear `focus-visible` ring state to ensure WCAG compliance.
## 2026-05-09 - Accessible Icon Buttons in Layout
**Learning:** Custom interactive elements (icon buttons) in the header and mobile sidebar components like `ThemeToggle`, `Modal`, `Header`, and `MobileSidebar` often lack explicit ARIA labels. Since these elements don't contain visual text content, this makes them completely inaccessible for screen reader users.
**Action:** When adding or maintaining icon-only buttons, always ensure an explicit `aria-label` string is provided that describes the action precisely (e.g., "Toggle theme", "Close modal", "Notifications").
