# Backend - Next-Gen AI SaaS Scheduler

This folder contains all backend code, services, and configuration for the project.

## Tech Stack
- Python (FastAPI for AI/logic microservices)
- PostgreSQL (Neon/Supabase)
- Redis (Upstash)
- tRPC (TypeScript, for API contracts)
- Zod (validation)
- LangChain/LangGraph (AI orchestration)
- Pinecone/pgvector (vector DB)
- Temporal.io/BullMQ (background jobs)
- Sentry, Axiom (monitoring)
- Nylas/Cal.com API (calendar sync)

## Structure
- `/models` — database models and migrations
- `/services` — business logic, AI, and integrations
- `/api` — FastAPI endpoints
- `/jobs` — background/edge jobs
- `/auth` — authentication/authorization
- `/utils` — helpers and shared code

## Getting Started
1. Set up Python environment (venv, poetry, or conda)
2. Install dependencies (requirements.txt/pyproject.toml)
3. Configure environment variables (.env)
4. Run database migrations
5. Start FastAPI server

---
See project root README for full-stack instructions.