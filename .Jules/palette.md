## 2024-05-07 - Accessible Topbar Interactive Elements
**Learning:** Custom interactive elements (links, buttons, search inputs) in layout components often lack native `focus-visible` styles and proper ARIA labels, making keyboard navigation difficult and screen reading impossible.
**Action:** Always verify that every custom interactive element in a navigation bar has an explicit `aria-label` (if icon-only or generic) and a clear `focus-visible` ring state to ensure WCAG compliance.

## 2024-05-10 - Icon-only buttons lacking ARIA labels
**Learning:** Found that multiple icon-only buttons (using Lucide icons) across various components (TeamMembersList.tsx, TimeRangeEditor.tsx) lacked aria-label attributes, rendering them inaccessible to screen readers. This seems to be a common oversight when rapidly developing UI with inline SVG components.
**Action:** Ensure all interactive elements, particularly those relying solely on visual iconography, are provided with descriptive aria-labels to meet accessibility standards.
