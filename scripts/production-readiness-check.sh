#!/bin/bash
set -e
echo "Running Production Readiness Check..."
cd frontend && pnpm run build
cd .. && cd backend && poetry run pytest -v
echo "Production Readiness Check Passed!"
