import re

with open('backend/api/bookings.py', 'r') as f:
    content = f.read()

content = content.replace(
    'booking_data.attendees[0] if booking_data.attendees else current_user.email',
    'booking_data.attendees[0] if getattr(booking_data, "attendees", []) else current_user.email'
)

with open('backend/api/bookings.py', 'w') as f:
    f.write(content)

with open('backend/services/usage.py', 'r') as f:
    content = f.read()

# Make sure usage doesn't fail
content = content.replace(
    'getattr(user, f"daily_{feature.split(\'_\')[1]}_count", None)',
    'getattr(user, f"daily_{feature.split(\'_\')[1]}_count", None) if "_" in feature else None'
)

with open('backend/services/usage.py', 'w') as f:
    f.write(content)
