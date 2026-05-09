## 2024-05-07 - Accessible Topbar Interactive Elements
**Learning:** Custom interactive elements (links, buttons, search inputs) in layout components often lack native `focus-visible` styles and proper ARIA labels, making keyboard navigation difficult and screen reading impossible.
**Action:** Always verify that every custom interactive element in a navigation bar has an explicit `aria-label` (if icon-only or generic) and a clear `focus-visible` ring state to ensure WCAG compliance.
## 2024-05-18 - Added ARIA labels to IconButtons
**Learning:** Material UI `IconButton` components lacking `aria-label`s represent a significant accessibility gap for navigational and notification elements (e.g., in `Header.tsx` and `MobileSidebar.tsx`). Screen readers rely on these attributes for purely icon-based interactions.
**Action:** Ensure all `IconButton` components have descriptive `aria-label`s (e.g., "Notifications", "Open mobile menu", "Close mobile menu") to maintain WCAG compliance and improve screen reader experiences.
