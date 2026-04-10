# GraftAI API Documentation

Complete API reference for the GraftAI scheduling platform.

## Base URL

```
Production: https://api.graftai.com/api/v1
Development: http://localhost:8000/api/v1
```

## Authentication

All API endpoints require authentication via Bearer token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

Or via API Key (for developer access):

```
X-API-Key: graft_your_api_key_here
```

## Rate Limiting

- Standard users: 100 requests per minute
- API Key access: Configurable per key (default: 1000 per hour)
- Rate limit headers included in responses:
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Requests remaining in current window
  - `X-RateLimit-Reset`: Timestamp when limit resets

---

## Authentication Endpoints

### POST /auth/login
Authenticate a user and receive JWT tokens.

**Request:**
```json
{
  "username": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### POST /auth/register
Register a new user account.

**Request:**
```json
{
  "full_name": "John Doe",
  "email": "john@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "message": "Verification code sent to email",
  "email": "john@example.com"
}
```

### POST /auth/verify-email
Verify email with OTP code.

**Request:**
```json
{
  "email": "john@example.com",
  "code": "123456"
}
```

### GET /auth/google/login
Initiate Google OAuth flow.

### GET /auth/microsoft/login
Initiate Microsoft OAuth flow.

---

## User Endpoints

### GET /users/me
Get current user profile.

**Response:**
```json
{
  "id": "usr_abc123",
  "email": "john@example.com",
  "full_name": "John Doe",
  "tier": "pro",
  "daily_ai_limit": 200,
  "daily_sync_limit": 50,
  "created_at": "2024-01-15T10:30:00Z",
  "preferences": {
    "timezone": "America/New_York",
    "week_start": "monday"
  }
}
```

### PUT /users/me
Update user profile.

**Request:**
```json
{
  "full_name": "John Doe Updated",
  "preferences": {
    "timezone": "America/Los_Angeles"
  }
}
```

---

## Calendar Endpoints

### GET /calendar/events
List calendar events.

**Query Parameters:**
- `start_date` (ISO datetime) - Start of range
- `end_date` (ISO datetime) - End of range
- `provider` (optional) - Filter by provider (google, microsoft, apple)

**Response:**
```json
{
  "events": [
    {
      "id": "evt_123",
      "title": "Team Standup",
      "start_time": "2024-01-15T10:00:00Z",
      "end_time": "2024-01-15T10:30:00Z",
      "provider": "google",
      "is_busy": true
    }
  ]
}
```

### POST /calendar/sync
Trigger calendar synchronization.

**Response:**
```json
{
  "synced_events": 5,
  "providers": ["google", "microsoft"],
  "completed_at": "2024-01-15T12:00:00Z"
}
```

### POST /calendar/google/connect
Get Google OAuth authorization URL.

**Response:**
```json
{
  "auth_url": "https://accounts.google.com/o/oauth2/auth?..."
}
```

### POST /calendar/microsoft/connect
Get Microsoft OAuth authorization URL.

---

## Booking Endpoints

### GET /bookings
List all bookings.

**Query Parameters:**
- `status` (optional) - Filter by status (confirmed, pending, cancelled)
- `start_date` (optional) - Filter by date range
- `end_date` (optional)

**Response:**
```json
{
  "bookings": [
    {
      "id": "bk_123",
      "title": "Product Demo",
      "start_time": "2024-01-15T14:00:00Z",
      "end_time": "2024-01-15T15:00:00Z",
      "attendee_name": "Jane Smith",
      "attendee_email": "jane@client.com",
      "status": "confirmed",
      "confirmation_code": "ABC123",
      "meeting_link": "https://meet.google.com/abc-defg-hij"
    }
  ],
  "total": 42,
  "page": 1,
  "per_page": 20
}
```

### POST /bookings
Create a new booking.

**Request:**
```json
{
  "title": "Consultation Call",
  "start_time": "2024-01-20T15:00:00Z",
  "end_time": "2024-01-20T16:00:00Z",
  "attendee_name": "Client Name",
  "attendee_email": "client@example.com",
  "attendee_phone": "+1234567890",
  "description": "Initial consultation",
  "event_type_id": "evt_type_123"
}
```

### GET /bookings/{booking_id}
Get booking details.

### PUT /bookings/{booking_id}
Update a booking.

### DELETE /bookings/{booking_id}
Cancel a booking.

---

## Event Types Endpoints

### GET /event-types
List all event types (booking link configurations).

**Response:**
```json
{
  "event_types": [
    {
      "id": "et_123",
      "name": "30 Minute Meeting",
      "slug": "30min",
      "duration": 30,
      "description": "Quick introductory call",
      "is_active": true,
      "public_url": "https://graftai.com/book/john/30min",
      "settings": {
        "buffer_before": 5,
        "buffer_after": 5,
        "min_notice_hours": 4
      }
    }
  ]
}
```

### POST /event-types
Create a new event type.

**Request:**
```json
{
  "name": "Strategy Session",
  "slug": "strategy",
  "duration": 60,
  "description": "Deep dive strategy discussion",
  "is_active": true,
  "settings": {
    "buffer_before": 15,
    "buffer_after": 15,
    "min_notice_hours": 24,
    "max_booking_days": 14
  }
}
```

### GET /event-types/{event_type_id}/availability
Get availability for an event type.

**Query Parameters:**
- `start_date` - Start date (ISO)
- `end_date` - End date (ISO)

**Response:**
```json
{
  "availability": [
    {
      "date": "2024-01-15",
      "slots": [
        {
          "start": "09:00",
          "end": "09:30",
          "available": true
        },
        {
          "start": "09:30",
          "end": "10:00",
          "available": false
        }
      ]
    }
  ]
}
```

---

## Team Endpoints

### POST /teams
Create a new team.

**Request:**
```json
{
  "name": "Engineering Team",
  "slug": "engineering",
  "description": "Engineering department scheduling"
}
```

### GET /teams
List teams the user belongs to.

### GET /teams/{team_id}
Get team details.

### POST /teams/{team_id}/members
Add a member to the team.

**Request:**
```json
{
  "email": "newmember@company.com",
  "role": "member"  // owner, admin, member, viewer
}
```

### GET /teams/{team_id}/members
List team members.

### POST /teams/{team_id}/event-types
Create a team event type.

**Request:**
```json
{
  "name": "Sales Call",
  "slug": "sales-call",
  "duration": 30,
  "assignment_type": "round_robin",  // all, specific, round_robin
  "assigned_members": ["user_1", "user_2"]
}
```

---

## Billing Endpoints

### POST /billing/stripe/create-checkout-session
Create a Stripe checkout session for subscription.

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/p/cs_test_...",
  "session_id": "cs_test_..."
}
```

### POST /billing/stripe/create-portal-session
Create a Stripe customer portal session.

**Response:**
```json
{
  "portal_url": "https://billing.stripe.com/session/..."
}
```

### GET /billing/stripe/config
Get Stripe publishable key.

---

## API Key Endpoints

### POST /api-keys
Create a new API key.

**Request:**
```json
{
  "name": "Production Integration",
  "scopes": ["read", "write"],
  "expires_days": 90
}
```

**Response:**
```json
{
  "id": "key_123",
  "name": "Production Integration",
  "key": "graft_aBcDeFgHiJkLmNoP...",
  "key_prefix": "graft_aBcD",
  "scopes": ["read", "write"],
  "created_at": "2024-01-15T10:30:00Z"
}
```

**⚠️ Important:** The full API key is only shown once on creation. Store it securely.

### GET /api-keys
List all API keys (masked).

### DELETE /api-keys/{key_id}
Revoke an API key.

### GET /api-keys/{key_id}/usage
Get API key usage statistics.

---

## Integration Endpoints

### GET /integrations
List all integrations.

### POST /integrations
Create a new integration.

**Request:**
```json
{
  "provider": "slack",  // zapier, slack, teams, custom
  "name": "Slack Notifications",
  "webhook_url": "https://hooks.slack.com/services/...",
  "events": [
    "booking.created",
    "booking.cancelled"
  ],
  "config": {
    "channel": "#bookings"
  }
}
```

### POST /integrations/{integration_id}/test
Send a test webhook.

### GET /integrations/{integration_id}/logs
Get webhook delivery logs.

---

## Email Template Endpoints

### GET /email-templates
List available email templates.

### POST /email-templates
Create a custom email template.

**Request:**
```json
{
  "name": "Custom Welcome",
  "slug": "custom_welcome",
  "subject": "Welcome, {{user_name}}!",
  "html_body": "<h1>Welcome {{user_name}}!</h1><p>Thanks for joining.</p>",
  "available_variables": ["user_name", "app_url"],
  "primary_color": "#6366f1"
}
```

### POST /email-templates/{template_id}/render
Preview template rendering.

**Request:**
```json
{
  "variables": {
    "user_name": "John Doe"
  }
}
```

### POST /email-templates/{template_id}/send-test
Send a test email.

---

## GDPR Compliance Endpoints

### POST /gdpr/dsr/submit
Submit a Data Subject Request (DSR).

**Request:**
```json
{
  "request_type": "access",  // access, rectification, erasure, portability
  "description": "Request all my personal data"
}
```

### GET /gdpr/consent
Get current consent status.

### PUT /gdpr/consent
Update consent preferences.

**Request:**
```json
{
  "essential": true,
  "analytics": true,
  "marketing": false,
  "ai_training": false
}
```

### POST /gdpr/data/export
Request data export.

### POST /gdpr/data/delete
Request account and data deletion.

---

## Analytics Endpoints

### GET /analytics/overview
Get high-level analytics.

**Response:**
```json
{
  "total_bookings": 152,
  "total_revenue": 2888.00,
  "active_users": 45,
  "avg_booking_duration": 45.5,
  "conversion_rate": 0.15
}
```

### GET /analytics/bookings/timeline
Get booking metrics over time.

**Query Parameters:**
- `days` - Number of days to analyze (1-365)

### GET /analytics/realtime
Get real-time metrics.

---

## AI Endpoints

### POST /ai/suggest-times
Get AI-suggested meeting times.

**Request:**
```json
{
  "attendees": ["user@example.com"],
  "duration_minutes": 30,
  "preferred_days": ["monday", "tuesday", "wednesday"],
  "preferred_time_start": "09:00",
  "preferred_time_end": "17:00"
}
```

**Response:**
```json
{
  "suggestions": [
    {
      "start_time": "2024-01-15T14:00:00Z",
      "end_time": "2024-01-15T14:30:00Z",
      "score": 0.95,
      "reason": "All attendees available, preferred time"
    }
  ]
}
```

### POST /ai/natural-language
Parse natural language scheduling requests.

**Request:**
```json
{
  "query": "Find a 30-min slot next week with the engineering team"
}
```

---

## Webhook Events

When you configure integrations, GraftAI sends webhook events to your URL:

### Event Format

```json
{
  "event": "booking.created",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "booking_id": "bk_123",
    "title": "Product Demo",
    "start_time": "2024-01-15T14:00:00Z",
    ...
  }
}
```

### Event Types

| Event | Description |
|-------|-------------|
| `booking.created` | New booking created |
| `booking.updated` | Booking details changed |
| `booking.cancelled` | Booking cancelled |
| `booking.completed` | Meeting completed |
| `user.registered` | New user signed up |
| `payment.received` | Payment processed |
| `team.member_joined` | New team member added |
| `team.member_left` | Team member removed |

### Signature Verification

Webhooks include a signature header for security:

```
X-GraftAI-Signature: sha256=<hex_signature>
```

Verify using HMAC-SHA256 with your webhook secret:

```python
import hmac
import hashlib

expected = hmac.new(
    webhook_secret.encode(),
    payload.encode(),
    hashlib.sha256
).hexdigest()

is_valid = hmac.compare_digest(f"sha256={expected}", signature_header)
```

---

## Error Handling

All errors follow this format:

```json
{
  "detail": "Error message",
  "code": "ERROR_CODE",
  "status": 400
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Invalid input data |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

---

## SDK and Libraries

Official SDKs:
- **Python**: `pip install graftai`
- **JavaScript/TypeScript**: `npm install @graftai/sdk`
- **Ruby**: `gem install graftai`

---

## Support

- **Documentation**: https://docs.graftai.com
- **API Status**: https://status.graftai.com
- **Support Email**: api-support@graftai.com
- **Developer Community**: https://community.graftai.com

---

*Last updated: January 2025*
