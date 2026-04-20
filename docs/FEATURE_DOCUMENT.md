# Feature Document

## Product Summary
GraftAI is a programmable scheduling and AI-enabled bookings platform for teams that need deep calendar integration, quota-aware ticketing, and rich dashboard telemetry.

## Key Features

### 1. User Authentication
- Standard sign-in and social login with Google and Microsoft.
- Magic link and session restore support.
- User profile and preferences management.

### 2. Dashboard Experience
- Team and account overview with usage metrics.
- Analytics pages for scheduling performance.
- Plugin management and integrations.
- Billing and plan management in the dashboard.

### 3. Booking and Calendar Workflows
- Public-facing booking pages with dynamic availability.
- Event booking, cancellation, and rescheduling flows.
- Calendar sync with external providers via connector routes.
- Automated booking rules and AI recommendations.

### 4. AI & Proactive Assistance
- AI-driven scheduling suggestions and proactive workflows.
- Background AI tasks accessible through `/api/proactive`.
- Quota-aware AI usage tracking and team limits.

### 5. Offline and Performance Enhancements
- Service worker caching for static routes and assets.
- Fast load behavior for public pages and dashboard components.
- Client-side retry and queue support for degraded network conditions.

### 6. Security and Governance
- Scoped JWT-based access control.
- Audit logging for auth flows and booking decisions.
- Environment-driven secret management.

## Business Value
- Reduces scheduling friction across teams and customers.
- Improves booking conversion through AI-enabled recommendations.
- Provides visibility into usage, quota, and calendar health.
- Supports resilient workflows with offline caching and retry logic.

## Target Users
- Product and engineering teams managing meetings and event capacity.
- Customer-facing operations that need smart booking pages.
- Admins who require quota and billing oversight.

## Roadmap Considerations
- Expand plugin marketplace and automation rules.
- Add additional calendar provider connectors.
- Harden AI provider fallback and response validation.
- Improve developer documentation and CI/CD readiness.
