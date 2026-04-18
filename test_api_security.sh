#!/bin/bash
# API Security Tests (run with backend running on localhost:8000)

echo "=================================="
echo "API Security Tests"
echo "=================================="

BASE_URL="http://localhost:8000"

echo ""
echo "1. Testing webhook authentication (should return 401)"
curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/bookings/webhook/automation-complete" \
  -H "Content-Type: application/json" \
  -d '{"booking_id": "test", "automation_id": "test", "status": "completed"}'
echo " - Expected: 401"

echo ""
echo "2. Testing webhook with wrong secret (should return 401)"
curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/bookings/webhook/automation-complete" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: wrong-secret" \
  -d '{"booking_id": "test", "automation_id": "test", "status": "completed"}'
echo " - Expected: 401"

echo ""
echo "3. Testing Razorpay webhook without signature (should return 403)"
curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/billing/razorpay/webhook" \
  -H "Content-Type: application/json" \
  -d '{"event": "payment.captured"}'
echo " - Expected: 403"

echo ""
echo "4. Testing CSRF protection on public booking (should return 403 without origin)"
curl -s -o /dev/null -w "%{http_code}" -X POST "$BASE_URL/api/public/events/testuser/testevent/book" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", "email": "test@test.com", "start_time": "2024-12-01T10:00:00"}'
echo " - Expected: 403"

echo ""
echo "5. Health check (should return 200)"
curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health"
echo " - Expected: 200"

echo ""
echo "=================================="
echo "API Tests Complete"
echo "=================================="
