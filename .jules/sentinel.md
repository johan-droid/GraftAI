## 2026-05-08 - SSRF Vulnerability in Webhook Service
**Vulnerability:** The `WebhookService.send_webhook` method accepted arbitrary URLs without validation, allowing Server-Side Request Forgery (SSRF) against internal network resources.
**Learning:** Outbound requests initiated by background tasks or user-configured webhooks must be validated to prevent attackers from targeting private subnets (e.g., `169.254.169.254` AWS metadata endpoint, `localhost`, `10.0.0.0/8`).
**Prevention:** Always use `backend.utils.ssrf.is_safe_url` to filter loopback, private, and reserved IPs before executing HTTP requests with `httpx` or similar clients.
