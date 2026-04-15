# Database Migration Guide

This document outlines the database migration sequence for GraftAI.

## Migration Order

Migrations must be applied in the following order due to foreign key dependencies:

### 1. Base Tables (Already Applied)
- Users, Bookings, Event Types, Calendar Tokens
- Authentication tables (MFA, Password Reset)

### 2. GDPR Compliance Tables
**File:** `backend/alembic/versions/gdpr_compliance_tables.py`

```bash
alembic upgrade gdpr_compliance
```

Creates:
- `dsr_records` - Data Subject Request tracking
- `dsr_audit_logs` - DSR audit trail
- `data_retention_schedules` - Retention policy configuration
- `consent_records` - User consent management
- `data_processing_records` - RoPA (Records of Processing Activities)
- `data_breach_records` - Data breach notifications

### 3. Team Scheduling Tables
**File:** `backend/alembic/versions/team_scheduling_tables.py`

```bash
alembic upgrade team_scheduling
```

Creates:
- `teams` - Team organizations
- `team_members` - Team membership with roles
- `team_event_types` - Team-specific booking links
- `team_bookings` - Team booking records

### 4. API Keys Tables
**File:** `backend/alembic/versions/api_keys_tables.py`

```bash
alembic upgrade api_keys
```

Creates:
- `api_keys` - Developer API keys with scopes
- `api_key_usage` - API key usage tracking

### 5. Integrations Tables
**File:** `backend/alembic/versions/integrations_tables.py`

```bash
alembic upgrade integrations
```

Creates:
- `integrations` - Third-party service connections (Zapier, Slack, Teams)
- `integration_logs` - Webhook delivery logs

### 6. Email Templates Tables
**File:** `backend/alembic/versions/email_templates_tables.py`

```bash
alembic upgrade email_templates
```

Creates:
- `email_templates` - Customizable email templates
- `email_logs` - Email delivery tracking

### 6. Video Conference Tables
**File:** `backend/alembic/versions/video_conference_tables.py`

```bash
alembic upgrade video_conference
```

Creates:
- `video_conference_configs` - Zoom/Meet/Teams OAuth configurations
- `video_conference_meetings` - Meeting records with join URLs
- `video_conference_recordings` - Cloud recording metadata

### 7. Resource Booking Tables
**File:** `backend/alembic/versions/resource_tables.py`

```bash
alembic upgrade resource_booking
```

Creates:
- `resources` - Rooms, equipment, vehicles, desks
- `resource_bookings` - Resource reservation records
- `resource_maintenance` - Maintenance scheduling

### 8. Automation Tables
**File:** `backend/alembic/versions/automation_tables.py`

```bash
alembic upgrade automation_rules
```

Creates:
- `automation_rules` - AI automation rule configurations
- `automation_executions` - Automation execution logs
- `automation_templates` - Pre-built automation templates

## Quick Migration Commands

### Apply All Migrations
```bash
cd backend
alembic upgrade head
```

### Check Current Version
```bash
cd backend
alembic current
```

### View Migration History
```bash
cd backend
alembic history
```

### Downgrade (Rollback)
```bash
# Rollback one version
alembic downgrade -1

# Rollback to specific version
alembic downgrade gdpr_compliance

# Rollback all
alembic downgrade base
```

## OAuth Token Encryption Backfill

After enabling `OAUTH_TOKEN_ENCRYPTION_KEY` (or rotating from plaintext storage),
backfill existing `user_tokens` rows with:

```bash
cd backend
python scripts/migrate_oauth_token_encryption.py
```

This script is idempotent:
- Plaintext tokens are encrypted and saved.
- Already encrypted rows are unchanged.
- Rows with unreadable ciphertext are reported but not modified.

## Environment Setup

### Development
```bash
# Set environment variables
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/graftai"
export ALEMBIC_CONFIG="backend/alembic.ini"

# Run migrations
alembic upgrade head
```

### Production
```bash
# Use production database URL
export DATABASE_URL="postgresql+asyncpg://prod_user:prod_pass@prod-host/graftai"

# Review pending migrations
alembic upgrade --sql head > migrations.sql

# Apply migrations
alembic upgrade head
```

## Troubleshooting

### Common Issues

**Issue:** `alembic command not found`
**Solution:**
```bash
python -m alembic upgrade head
```

**Issue:** `Database already has tables`
**Solution:** Mark existing tables as current:
```bash
alembic stamp head
```

**Issue:** `Foreign key constraint violation`
**Solution:** Ensure migrations are applied in order, or:
```bash
alembic upgrade <revision_id> --sql > fix.sql
# Review and manually apply fix.sql
```

**Issue:** `Column already exists`
**Solution:** The migration may have already been partially applied. Check:
```bash
alembic current  # Check current version
psql -d graftai -c "\d table_name"  # Check existing columns
```

## Schema Overview

### Core Tables
- **users**: User accounts, authentication, tier info
- **bookings**: Scheduled meetings and appointments
- **event_types**: Booking link configurations
- **user_tokens**: OAuth tokens for calendar sync

### GDPR Tables
- **dsr_records**: Data Subject Requests (access, deletion, etc.)
- **consent_records**: User consent for cookies, analytics, marketing
- **data_breach_records**: Breach notifications per GDPR Article 33
- **data_processing_records**: RoPA compliance documentation

### Team Tables
- **teams**: Organizations with settings
- **team_members**: Users with roles (owner/admin/member/viewer)
- **team_event_types**: Round-robin and collective availability
- **team_bookings**: Team-associated appointments

### Developer Tables
- **api_keys**: Secure API access with scopes
- **integrations**: Webhook configurations
- **email_templates**: Customizable notification templates

## Backup Before Migration

Always backup before running migrations:

```bash
# PostgreSQL
pg_dump -h localhost -U user graftai > backup_$(date +%Y%m%d).sql

# Or with Docker
docker exec postgres-container pg_dump -U user graftai > backup.sql
```

## Verifying Migrations

After applying migrations, verify:

```bash
# Check all tables exist
psql -d graftai -c "\dt"

# Check foreign keys
psql -d graftai -c "\d team_members"

# Run backend health check
curl http://localhost:8000/health
```

## Migration Development

Creating a new migration:

```bash
# Generate automatic migration
alembic revision --autogenerate -m "Add new feature tables"

# Create empty migration
alembic revision -m "Manual migration"

# Edit the generated file in backend/alembic/versions/
```

Best practices:
1. Always review auto-generated migrations
2. Test migrations on a copy of production data
3. Include both upgrade() and downgrade() functions
4. Add indexes for frequently queried columns
5. Use batch operations for large tables

---

*Last updated: January 2025*
