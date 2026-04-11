-- Backfill legacy blank titles so frontend and backend stay consistent.

UPDATE events
SET title = 'Untitled event'
WHERE title IS NULL OR btrim(title) = '';

UPDATE event_types
SET title = 'Booking'
WHERE title IS NULL OR btrim(title) = '';
