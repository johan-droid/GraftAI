# GraftAI Documentation

## Index

- [Architecture overview](./architecture/overview.md) — frontend/backend boundaries, data flow
- [Local setup](./development/local-setup.md) — reproducible dev environment
- [Vercel deployment](./deployment/vercel.md) — frontend build, env, routing
- [Render deployment](./deployment/render.md) — API, worker, database, queues
- [API overview](./api/overview.md) — entrypoint, auth, contracts
- [Repository audit](./audits/repository-audit.md) — findings and structural changes

## Reference (existing, kept as-is)

- [auth_openapi.yaml](./auth_openapi.yaml) — Auth API OpenAPI subset
- [RATE_LIMITING.md](./RATE_LIMITING.md) — Redis rate limiter: tiers, hashing, refresh
- [migrations/](./migrations) — API-key migration scripts and SQL
