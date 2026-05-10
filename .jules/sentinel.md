## 2026-05-10 - Teams Webhook Domain Validation Bypass
**Vulnerability:** The function `_validate_teams_webhook_url` in `backend/services/dlq_handlers.py` used `.endswith("office.com")` and `.endswith("microsoft.com")` to validate the webhook URL. This allowed malicious domains like `malicious-office.com` or `malicious-microsoft.com` to bypass the validation.
**Learning:** Using `.endswith` on string-based domains is insufficient to prevent domain prefix spoofing, leaving systems open to SSRF or phishing vectors when making outbound requests to third parties.
**Prevention:** Always check for exact domain matches (e.g. `host == "office.com"`) or specific subdomain boundaries (e.g. `host.endswith(".office.com")`).
