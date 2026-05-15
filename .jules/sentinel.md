## 2025-05-08 - Added SSRF protection for outgoing webhooks
**Vulnerability:** The application was making outbound HTTP requests (webhooks) without validating the destination IP. This could allow an attacker to target internal services on the local network (e.g. `localhost` or private network IPs).
**Learning:** Initial SSRF validation logic relied solely on IPv4 resolution, which could be bypassed using IPv6 (e.g., `http://[::1]`).
**Prevention:** To effectively mitigate SSRF, URLs must be validated by resolving hostnames to *all* IP addresses (both IPv4 and IPv6) using `socket.getaddrinfo`, then checking each against loopback, private, and reserved ranges using Python's `ipaddress` module.

## 2026-05-11 - Replaced insecure randomness for client-side IDs
**Vulnerability:** Use of `Math.random()` for generating identifiers in the offline queue and toast system. `Math.random()` is not cryptographically secure and can lead to predictable IDs.
**Learning:** Predictive identifiers can sometimes be exploited in timing attacks or for cache poisoning if they are used in externally visible contexts.
**Prevention:** Use `crypto.randomUUID()` for generating secure, non-predictable unique identifiers in the frontend.
