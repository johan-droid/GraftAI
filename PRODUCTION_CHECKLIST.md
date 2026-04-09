# 🚀 GraftAI Production Deployment Checklist

Before deploying GraftAI to production, complete all items below:

## ✅ Environment Configuration

- [ ] Copy `.env.example` to `.env` (production version)
- [ ] Set `ENV=production`
- [ ] Set `DEBUG=false` (CRITICAL - never leave true in production)
- [ ] Generate a strong `SECRET_KEY` using:
  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- [ ] Update `FRONTEND_URL` to your actual production domain (e.g., https://graftai.yourdomain.com)
- [ ] Update `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_API_BASE_URL` to production API endpoints

## ✅ Database Setup

- [ ] Set up PostgreSQL (not SQLite) for production
- [ ] Update `DATABASE_URL` with production PostgreSQL credentials
- [ ] Run migrations: `alembic upgrade head`
- [ ] Verify database backups are configured
- [ ] Test database restore procedures

## ✅ Security & Authentication

- [ ] Generate and configure a strong `SECRET_KEY`
- [ ] Set `ALGORITHM=HS256` (or RS256 for additional security)
- [ ] Configure `ACCESS_TOKEN_EXPIRE_MINUTES` appropriately
- [ ] Enable HTTPS/TLS for all endpoints
- [ ] Configure CORS properly (use actual domain in `FRONTEND_URL`)
- [ ] Set secure browser headers in `next.config.ts`
- [ ] Install and configure SSL certificate

## ✅ OAuth Integrations

- [ ] Register OAuth applications on Google Cloud Console
  - [ ] Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
  - [ ] Update `GOOGLE_REDIRECT_URI` to production callback URL
- [ ] Register OAuth applications on Azure Portal (Microsoft)
  - [ ] Set `MICROSOFT_CLIENT_ID` and `MICROSOFT_CLIENT_SECRET`
  - [ ] Update `MICROSOFT_REDIRECT_URI` to production callback URL
- [ ] Test OAuth flows end-to-end in staging first

## ✅ Payment Processing

- [ ] Configure Stripe for production
  - [ ] Set `STRIPE_SECRET_KEY` and `STRIPE_PUBLISHABLE_KEY`
  - [ ] Set `STRIPE_WEBHOOK_SECRET` for webhook verification
- [ ] OR Configure Razorpay
  - [ ] Set `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`
- [ ] Test payment flows with test cards
- [ ] Configure webhook handlers for payment events

## ✅ Email Service

- [ ] Configure Resend (recommended)
  - [ ] Set `RESEND_API_KEY`
  - [ ] Set `SMTP_FROM_EMAIL` to your domain
- [ ] OR Configure SMTP directly
  - [ ] Set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`
- [ ] Test email delivery with test accounts

## ✅ Cache & Background Jobs

- [ ] Set up Redis for production
  - [ ] Update `REDIS_URL` with production Redis connection
  - [ ] Configure Redis persistence and backups
- [ ] Configure background job worker (`arq`)
- [ ] Set up job monitoring and logging

## ✅ AI & LLM Services

- [ ] Configure default LLM model (`LLM_MODEL`)
- [ ] Set `OPENAI_API_KEY` for GPT models
  - [ ] Set appropriate rate limits
- [ ] OR Set `GROQ_API_KEY` for Groq models
- [ ] Test model responses with production data
- [ ] Configure fallback models if primary is unavailable

## ✅ Monitoring & Observability

- [ ] Set up Sentry error tracking
  - [ ] Configure `SENTRY_DSN`
  - [ ] Set `SENTRY_ENVIRONMENT=production`
- [ ] Configure application logging
- [ ] Set up performance monitoring (APM)
- [ ] Configure alerts for critical errors
- [ ] Set up uptime monitoring

## ✅ AWS Integration (if using S3)

- [ ] Create AWS IAM user for S3 access
  - [ ] Set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
  - [ ] Set `AWS_S3_BUCKET_NAME`
  - [ ] Set `AWS_REGION`
- [ ] Configure S3 bucket policies and CORS
- [ ] Test file uploads and downloads

## ✅ Deployment Infrastructure

- [ ] Configure Docker images for production
- [ ] Set up CI/CD pipeline (GitHub Actions, etc.)
- [ ] Configure automated backups
- [ ] Set up health checks and monitoring
- [ ] Document deployment procedure
- [ ] Plan rollback strategy

## ✅ Frontend Configuration

- [ ] Build frontend: `npm run build` in frontend directory
- [ ] Verify `next.config.ts` production settings
- [ ] Test CSP headers and security policies
- [ ] Verify service worker is disabled in development
- [ ] Test responsive design on production domain

## ✅ Testing & Validation

- [ ] Run all backend tests: `pytest`
- [ ] Run lint checks: `npm run lint` (frontend)
- [ ] Security scan for dependencies
- [ ] Load testing
- [ ] End-to-end testing in staging environment
- [ ] Test all OAuth integrations
- [ ] Test payment processing
- [ ] Test email delivery

## ✅ Documentation & Knowledge Transfer

- [ ] Update API documentation
- [ ] Document deployment procedure
- [ ] Create runbooks for common operations
- [ ] Document emergency procedures
- [ ] Set up team access to production systems
- [ ] Train team on monitoring and alerts

## ✅ Pre-Deployment Final Checks

- [ ] Review `.gitignore` - ensure secrets won't be committed
- [ ] Verify `.env.example` doesn't contain real secrets
- [ ] Check environment variables are all set correctly
- [ ] Test health checks: `GET /api/v1/health` or similar
- [ ] Verify database migrations are up to date
- [ ] Confirm all external API credentials are valid

## ✅ Post-Deployment

- [ ] Monitor error tracking (Sentry) for issues
- [ ] Check application logs for errors
- [ ] Verify all features are working
- [ ] Test user registration and login flows
- [ ] Confirm email notifications are being sent
- [ ] Monitor performance metrics
- [ ] Have rollback procedure ready

---

## 🔐 Security Best Practices

- Never commit `.env` files or secrets to Git
- Use strong, unique passwords for all services
- Rotate API keys regularly
- Enable two-factor authentication where available
- Keep dependencies up to date
- Regular security audits
- Monitor for suspicious activity

## 📞 Support

For issues or questions, refer to:
- Backend: `/backend/README.md`
- Frontend: `/frontend/README.md`
- Architecture: `/ARCHITECTURE.md`
- Technical Spec: `/PROJECT_TECHNICAL_SPEC.md`

---

**Last Updated**: 2026-04-09  
**Status**: Production Ready When All Steps Completed ✅
