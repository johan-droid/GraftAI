# Load Testing with k6

This directory contains load testing scripts for GraftAI using k6.

## Prerequisites

1. Install k6:
   ```bash
   # macOS
   brew install k6
   
   # Windows
   choco install k6
   
   # Linux
   sudo apt-get install k6
   ```

2. Set environment variables:
   ```bash
   export API_BASE_URL=http://localhost:8000
   export AUTH_TOKEN=your_jwt_token_here
   ```

## Test Scripts

### 1. API Load Test (`api-load-test.js`)
Comprehensive test covering all API endpoints.

```bash
# Run smoke test only
k6 run -e API_BASE_URL=http://localhost:8000 api-load-test.js --tag test_type=smoke

# Run all scenarios
k6 run -e API_BASE_URL=http://localhost:8000 -e AUTH_TOKEN=token api-load-test.js

# Run specific scenario
k6 run -e API_BASE_URL=http://localhost:8000 api-load-test.js --env EXECUTION_SEGMENT=0:1/4
```

### 2. Workflow Load Test (`workflow-load-test.js`)
Tests workflow engine and DLQ performance.

```bash
k6 run -e API_BASE_URL=http://localhost:8000 -e AUTH_TOKEN=token workflow-load-test.js
```

## Test Scenarios

### Smoke Test (10 VU, 1 min)
- Verifies basic functionality
- Health checks, public API

### Load Test (50 VU, 9 min)
- Ramp up: 2 min to 50 VU
- Steady state: 5 min at 50 VU
- Ramp down: 2 min to 0 VU

### Stress Test (300 VU, 14 min)
- Gradual increase to find breaking point
- Peak: 300 concurrent users

### Spike Test (100 VU spike, 4 min)
- Baseline: 10 VU
- Sudden spike to 100 VU
- Recovery period

## Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| P95 Latency | < 500ms | < 1000ms |
| P99 Latency | < 1000ms | < 2000ms |
| Error Rate | < 1% | < 5% |
| Throughput | > 1000 RPS | > 500 RPS |

## Interpreting Results

### Good Performance
- P95 latency < 500ms
- Error rate < 1%
- No rate limiting errors (429)
- Cache hit ratio > 80%

### Warning Signs
- P95 latency 500-1000ms
- Error rate 1-5%
- Rate limiting triggered
- Memory usage increasing

### Critical Issues
- P95 latency > 1000ms
- Error rate > 5%
- Server errors (5xx)
- Connection timeouts

## CI/CD Integration

```yaml
# .github/workflows/load-test.yml
name: Load Test
on: [deployment_status]
jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup k6
        run: |
          sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
          echo "deb https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update
          sudo apt-get install k6
      - name: Run smoke test
        run: k6 run --env API_BASE_URL=${{ github.event.deployment.payload.web_url }} load-tests/api-load-test.js
```

## Troubleshooting

### Connection Refused
- Verify API is running: `curl http://localhost:8000/health`
- Check firewall settings
- Verify port configuration

### Rate Limiting
- Increase rate limits for testing
- Add test-specific API keys
- Use staging environment

### High Error Rates
- Check server logs
- Verify database connections
- Monitor memory/CPU usage

## Advanced Usage

### Distributed Testing
```bash
k6 run --out influxdb=http://localhost:8086/k6 api-load-test.js
```

### Custom Metrics
```javascript
import { Trend } from 'k6/metrics';
const myTrend = new Trend('my_metric');
myTrend.add(response.timings.duration);
```

### Thresholds
Tests will fail if thresholds are exceeded:
```javascript
thresholds: {
  http_req_duration: ['p(95)<500'],
  http_req_failed: ['rate<0.1'],
}
```

## Support

For k6 documentation: https://k6.io/docs
