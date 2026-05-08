## 2024-05-07 - Accessible Topbar Interactive Elements
**Learning:** Custom interactive elements (links, buttons, search inputs) in layout components often lack native `focus-visible` styles and proper ARIA labels, making keyboard navigation difficult and screen reading impossible.
**Action:** Always verify that every custom interactive element in a navigation bar has an explicit `aria-label` (if icon-only or generic) and a clear `focus-visible` ring state to ensure WCAG compliance.
