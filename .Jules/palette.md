## 2024-05-07 - Accessible Topbar Interactive Elements
**Learning:** Custom interactive elements (links, buttons, search inputs) in layout components often lack native `focus-visible` styles and proper ARIA labels, making keyboard navigation difficult and screen reading impossible.
**Action:** Always verify that every custom interactive element in a navigation bar has an explicit `aria-label` (if icon-only or generic) and a clear `focus-visible` ring state to ensure WCAG compliance.

## 2024-05-11 - Add missing ARIA labels to MUI IconButton components
**Learning:** Found an accessibility issue pattern specific to MUI's `<IconButton>` wrapper components where they lacked accessible names (`aria-label`) when used as icon-only buttons. This is a critical issue for screen readers.
**Action:** Always verify that `<IconButton>` and other interactive icon-wrapper components have descriptive `aria-label`s or use `<Tooltip>` with accessible wrappers when implementing icon-only actions to adhere to a11y standards.
