## 2025-05-08 - Added SSRF protection for outgoing webhooks
**Vulnerability:** The application was making outbound HTTP requests (webhooks) without validating the destination IP. This could allow an attacker to target internal services on the local network (e.g. `localhost` or private network IPs).
**Learning:** Initial SSRF validation logic relied solely on IPv4 resolution, which could be bypassed using IPv6 (e.g., `http://[::1]`).
**Prevention:** To effectively mitigate SSRF, URLs must be validated by resolving hostnames to *all* IP addresses (both IPv4 and IPv6) using `socket.getaddrinfo`, then checking each against loopback, private, and reserved ranges using Python's `ipaddress` module.

## 2025-05-18 - Privilege Escalation via User-Modifiable Preferences
**Vulnerability:** Admin access endpoints in `analytics_routes.py` and `email_template_routes.py` relied on an ad-hoc `_is_admin` function that checked `user.preferences.get("role")`. Since `preferences` is user-modifiable via `/api/v1/users/me/profile`, any user could grant themselves admin rights by sending `{"preferences": {"role": "admin"}}`.
**Learning:** Security checks were duplicated in ad-hoc functions across the codebase instead of using a centralized dependency injection. Furthermore, relying on untrusted, user-controllable data (like JSON preference fields) for authorization checks is a critical security risk.
**Prevention:** Always use centralized, trusted authorization logic (`require_admin` dependency in `backend.auth.schemes`) for role-based access control. Never use user-modifiable fields (like `preferences`) for critical authorization decisions; rely exclusively on trusted, protected database columns (e.g., `is_superuser`, `tier`).
