/**
 * k6 Load Test Script for GraftAI Workflow Engine
 * Tests workflow execution performance and DLQ handling
 * 
 * Usage:
 *   k6 run workflow-load-test.js
 */

import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend } from 'k6/metrics';
import { randomString, randomIntBetween } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

const errorRate = new Rate('workflow_errors');
const workflowLatency = new Trend('workflow_latency');

const API_BASE_URL = __ENV.API_BASE_URL || 'http://localhost:8000';
const AUTH_TOKEN = __ENV.AUTH_TOKEN || '';

export const options = {
  stages: [
    { duration: '1m', target: 10 },   // Warm up
    { duration: '3m', target: 30 },   // Ramp up
    { duration: '5m', target: 30 },   // Steady state
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'],
    http_req_failed: ['rate<0.05'],
    workflow_errors: ['rate<0.05'],
  },
};

function getHeaders() {
  return {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${AUTH_TOKEN}`,
  };
}

export default function() {
  group('Workflow Management', () => {
    // List workflows
    const listResponse = http.get(`${API_BASE_URL}/api/v1/workflows`, {
      headers: getHeaders(),
    });
    
    const success = check(listResponse, {
      'List workflows status 200': (r) => r.status === 200,
      'List workflows response time < 500ms': (r) => r.timings.duration < 500,
    });
    
    errorRate.add(!success);
    workflowLatency.add(listResponse.timings.duration);
    
    // Create workflow
    const workflowData = {
      name: `Load Test Workflow ${randomString(8)}`,
      description: 'Created by load test',
      trigger: 'BOOKING_CREATED',
      is_active: true,
    };
    
    const createResponse = http.post(
      `${API_BASE_URL}/api/v1/workflows`,
      JSON.stringify(workflowData),
      { headers: getHeaders() }
    );
    
    const createSuccess = check(createResponse, {
      'Create workflow success': (r) => [200, 201].includes(r.status),
      'Create workflow response time < 500ms': (r) => r.timings.duration < 500,
    });
    
    errorRate.add(!createSuccess);
    
    if (createSuccess && createResponse.status === 200) {
      const workflow = JSON.parse(createResponse.body);
      
      // Add step to workflow
      const stepData = {
        action_type: 'EMAIL',
        action_config: {
          to: '{{attendee_email}}',
          subject: 'Test',
          body: 'Test body',
        },
        delay_minutes: 0,
        step_number: 1,
      };
      
      const stepResponse = http.post(
        `${API_BASE_URL}/api/v1/workflows/${workflow.id}/steps`,
        JSON.stringify(stepData),
        { headers: getHeaders() }
      );
      
      check(stepResponse, {
        'Add step success': (r) => [200, 201].includes(r.status),
      });
      
      // Cleanup - delete workflow
      http.del(`${API_BASE_URL}/api/v1/workflows/${workflow.id}`, null, {
        headers: getHeaders(),
      });
    }
  });
  
  group('Trigger Actions', () => {
    // Test workflow triggers
    const triggerResponse = http.post(
      `${API_BASE_URL}/api/v1/workflows/trigger`,
      JSON.stringify({
        trigger_type: 'BOOKING_CREATED',
        test_data: {
          attendee_email: 'test@example.com',
          attendee_name: 'Test User',
          booking_title: 'Test Meeting',
          booking_time: new Date().toISOString(),
        },
      }),
      { headers: getHeaders() }
    );
    
    check(triggerResponse, {
      'Trigger workflow accepted': (r) => [200, 202].includes(r.status),
    });
  });
  
  sleep(randomIntBetween(1, 3));
}
