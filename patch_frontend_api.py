import re

with open('frontend/src/lib/api.ts', 'r') as f:
    content = f.read()

# Fix getPublicEventAvailability to call `/public/users/{username}/{event_type}/availability`
old_month_url = "`/public/events/${encodeURIComponent(username)}/${encodeURIComponent(eventType)}/availability`"
new_month_url = "`/public/users/${encodeURIComponent(username)}/${encodeURIComponent(eventType)}/availability`"
content = content.replace(old_month_url, new_month_url)

# Fix getPublicEventAvailabilityByDate to call `/public/users/{username}/{event_type}/daily_availability`
old_date_url = "`/public/users/${encodeURIComponent(username)}/${encodeURIComponent(eventType)}/availability`"
new_date_url = "`/public/users/${encodeURIComponent(username)}/${encodeURIComponent(eventType)}/daily_availability`"

# Be careful, the previous code had changed it. Let's see what is currently in api.ts
