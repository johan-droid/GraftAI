/**
 * k6 Load Test Script for GraftAI API
 * Tests API performance under various load conditions
 * 
 * Usage:
 *   k6 run api-load-test.js
 * 
 * Environment Variables:
 *   API_BASE_URL - Base URL of the API (default: http://localhost:8000)
 *   AUTH_TOKEN - Bearer token for authenticated endpoints
 * 
 * Scenarios:
 *   - smoke: Minimal load to verify system works (10 VU, 1 min)
 *   - load: Normal load test (50 VU, ramp up/down, 5 min)
 *   - stress: Stress test (200 VU, find breaking point, 10 min)
 *   - spike: Spike test (sudden 100 VU increase, 3 min)
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend, Counter, Gauge } from 'k6/metrics';
import { randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// Custom metrics
const errorRate = new Rate('errors');
const apiLatency = new Trend('api_latency');
const successfulRequests = new Counter('successful_requests');
const failedRequests = new Counter('failed_requests');
const activeUsers = new Gauge('active_users');

// Configuration
const API_BASE_URL = __ENV.API_BASE_URL || 'http://localhost:8000';
const AUTH_TOKEN = __ENV.AUTH_TOKEN || '';

// Test scenarios
export const options = {
  scenarios: {
    // Smoke test - verify basic functionality
    smoke: {
      executor: 'constant-vus',
      vus: 10,
      duration: '1m',
      exec: 'smokeTest',
      tags: { test_type: 'smoke' },
    },
    
    // Load test - normal traffic simulation
    load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 50 },   // Ramp up
        { duration: '5m', target: 50 }, // Steady state
        { duration: '2m', target: 0 },   // Ramp down
      ],
      exec: 'loadTest',
      tags: { test_type: 'load' },
    },
    
    // Stress test - find breaking point
    stress: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 100 },
        { duration: '5m', target: 200 },
        { duration: '5m', target: 300 },
        { duration: '2m', target: 0 },
      ],
      exec: 'stressTest',
      tags: { test_type: 'stress' },
    },
    
    // Spike test - sudden traffic surge
    spike: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 10 },   // Baseline
        { duration: '30s', target: 100 }, // Spike
        { duration: '2m', target: 100 },  // Sustained spike
        { duration: '30s', target: 10 },   // Recovery
      ],
      exec: 'spikeTest',
      tags: { test_type: 'spike' },
    },
    
    // API specific tests
    auth_api: {
      executor: 'constant-vus',
      vus: 20,
      duration: '3m',
      exec: 'authApiTest',
      tags: { test_type: 'auth' },
    },
    
    ai_chat_api: {
      executor: 'constant-vus',
      vus: 15,
      duration: '3m',
      exec: 'aiChatApiTest',
      tags: { test_type: 'ai_chat' },
    },
  },
  
  thresholds: {
    http_req_duration: ['p(95)<500'],     // 95% of requests under 500ms
    http_req_failed: ['rate<0.1'],         // Error rate under 10%
    errors: ['rate<0.1'],                  // Custom error rate under 10%
    api_latency: ['p(95)<400'],            // API latency under 400ms
  },
};

// Helper functions
function getHeaders(includeAuth = false) {
  const headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'X-Request-ID': `load-test-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
  };
  
  if (includeAuth && AUTH_TOKEN) {
    headers['Authorization'] = `Bearer ${AUTH_TOKEN}`;
  }
  
  return headers;
}

function checkResponse(response, name) {
  const success = check(response, {
    [`${name} status is 200`]: (r) => r.status === 200,
    [`${name} response time < 500ms`]: (r) => r.timings.duration < 500,
    [`${name} has valid JSON`]: (r) => {
      try {
        JSON.parse(r.body);
        return true;
      } catch (e) {
        return false;
      }
    },
  });
  
  errorRate.add(!success);
  apiLatency.add(response.timings.duration);
  
  if (success) {
    successfulRequests.add(1);
  } else {
    failedRequests.add(1);
    console.error(`Failed: ${name} - Status: ${response.status}, Body: ${response.body}`);
  }
  
  return success;
}

// Smoke Test
export function smokeTest() {
  group('Health Checks', () => {
    const response = http.get(`${API_BASE_URL}/health`, {
      headers: getHeaders(),
    });
    checkResponse(response, 'Health Check');
  });
  
  group('Public API', () => {
    const response = http.get(`${API_BASE_URL}/api/v1/public/status`, {
      headers: getHeaders(),
    });
    checkResponse(response, 'Public Status');
  });
  
  sleep(randomIntBetween(1, 3));
}

// Load Test
export function loadTest() {
  activeUsers.add(1);
  
  group('Booking Flow', () => {
    // List bookings
    const listResponse = http.get(`${API_BASE_URL}/api/v1/bookings?limit=20`, {
      headers: getHeaders(true),
    });
    checkResponse(listResponse, 'List Bookings');
    
    sleep(1);
    
    // Get booking details
    let bookings = [];
    if (listResponse.status === 200) {
      try {
        bookings = JSON.parse(listResponse.body || '[]');
      } catch (err) {
        console.error('Failed to parse bookings response:', err, listResponse.body);
      }
    }

    if (Array.isArray(bookings) && bookings.length > 0) {
      const bookingId = bookings[0].id;
      const detailResponse = http.get(`${API_BASE_URL}/api/v1/bookings/${bookingId}`, {
        headers: getHeaders(true),
      });
      checkResponse(detailResponse, 'Get Booking');
    }
  });
  
  group('User API', () => {
    const response = http.get(`${API_BASE_URL}/api/v1/users/me`, {
      headers: getHeaders(true),
    });
    checkResponse(response, 'Get Current User');
  });
  
  sleep(randomIntBetween(2, 5));
  activeUsers.add(-1);
}

// Stress Test
export function stressTest() {
  activeUsers.add(1);
  
  // High-frequency requests to find breaking point
  group('Stress - High Frequency', () => {
    const responses = http.batch([
      ['GET', `${API_BASE_URL}/health`, null, { headers: getHeaders() }],
      ['GET', `${API_BASE_URL}/api/v1/users/me`, null, { headers: getHeaders(true) }],
      ['GET', `${API_BASE_URL}/api/v1/bookings`, null, { headers: getHeaders(true) }],
    ]);
    
    responses.forEach((response, idx) => {
      const names = ['Health', 'User', 'Bookings'];
      checkResponse(response, `Stress ${names[idx]}`);
    });
  });
  
  sleep(randomIntBetween(1, 2));
  activeUsers.add(-1);
}

// Spike Test
export function spikeTest() {
  activeUsers.add(1);
  
  // Rapid requests during spike
  group('Spike - Rapid Requests', () => {
    for (let i = 0; i < 5; i++) {
      const response = http.get(`${API_BASE_URL}/health`, {
        headers: getHeaders(),
      });
      checkResponse(response, `Spike Health ${i}`);
    }
  });
  
  sleep(randomIntBetween(0.5, 1));
  activeUsers.add(-1);
}

// Auth API Test
export function authApiTest() {
  group('Authentication Flow', () => {
    // Login endpoint test
    const loginResponse = http.post(`${API_BASE_URL}/api/v1/auth/login`, JSON.stringify({
      email: 'loadtest@example.com',
      password: 'testpassword',
    }), {
      headers: getHeaders(),
    });
    
    // We expect 401 for invalid credentials, but response should be fast
    check(loginResponse, {
      'Auth response time < 300ms': (r) => r.timings.duration < 300,
      'Auth returns expected status': (r) => [200, 401, 422].includes(r.status),
    });
    
    // Register endpoint test
    const registerResponse = http.post(`${API_BASE_URL}/api/v1/auth/register`, JSON.stringify({
      email: `loadtest_${Date.now()}@example.com`,
      password: 'TestPass123!',
      full_name: 'Load Test User',
    }), {
      headers: getHeaders(),
    });
    
    check(registerResponse, {
      'Register response time < 500ms': (r) => r.timings.duration < 500,
      'Register returns expected status': (r) => [200, 201, 400, 422, 409].includes(r.status),
    });
  });
  
  sleep(randomIntBetween(1, 2));
}

// AI Chat API Test
export function aiChatApiTest() {
  group('AI Chat API', () => {
    const response = http.post(`${API_BASE_URL}/api/v1/ai/chat`, JSON.stringify({
      message: 'Hello, schedule a meeting tomorrow at 2pm',
      conversation_id: `load-test-${Date.now()}`,
    }), {
      headers: getHeaders(true),
    });
    
    // AI requests may take longer
    check(response, {
      'AI Chat status is 200': (r) => r.status === 200,
      'AI Chat response time < 3000ms': (r) => r.timings.duration < 3000,
    });
    
    if (response.status === 200) {
      check(response, {
        'AI Chat returns valid response': (r) => {
          try {
            const body = JSON.parse(r.body);
            return body.content && body.content.length > 0;
          } catch (e) {
            return false;
          }
        },
      });
    }
  });
  
  sleep(randomIntBetween(3, 5)); // Longer sleep for AI requests
}

// Setup and teardown
export function setup() {
  console.log('Starting load test suite...');
  console.log(`Target API: ${API_BASE_URL}`);
  
  // Verify API is reachable
  const healthCheck = http.get(`${API_BASE_URL}/health`);
  if (healthCheck.status !== 200) {
    console.error('API health check failed! Aborting test.');
    return { abort: true };
  }
  
  console.log('API is healthy. Starting tests...');
  return { startTime: Date.now() };
}

export function teardown(data) {
  if (data.abort) {
    console.log('Test aborted due to API unavailability');
    return;
  }
  
  const duration = (Date.now() - data.startTime) / 1000;
  console.log(`\n=== Test Complete ===`);
  console.log(`Duration: ${duration}s`);
  console.log(`Check test output for detailed metrics`);
}
