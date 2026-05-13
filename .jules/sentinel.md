## 2025-05-08 - Added SSRF protection for outgoing webhooks
**Vulnerability:** The application was making outbound HTTP requests (webhooks) without validating the destination IP. This could allow an attacker to target internal services on the local network (e.g. `localhost` or private network IPs).
**Learning:** Initial SSRF validation logic relied solely on IPv4 resolution, which could be bypassed using IPv6 (e.g., `http://[::1]`).
**Prevention:** To effectively mitigate SSRF, URLs must be validated by resolving hostnames to *all* IP addresses (both IPv4 and IPv6) using `socket.getaddrinfo`, then checking each against loopback, private, and reserved ranges using Python's `ipaddress` module.
## 2025-03-09 - Fix suffix bypass in Teams webhook validation
**Vulnerability:** Suffix bypass in URL validation `host.endswith("office.com")` allowing domains like `malicious-office.com`.
**Learning:** Checking for suffixes in domains is prone to spoofing.
**Prevention:** Always use strict domain matching (`host == "domain.com" or host.endswith(".domain.com")`).
