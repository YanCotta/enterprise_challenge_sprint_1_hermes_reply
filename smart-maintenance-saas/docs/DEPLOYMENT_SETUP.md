# Deployment Setup Checklist (.env Canonical Guide)

**Last Updated:** 2025-09-30  
**Status:** V1.0 Production Ready  
**Related:** [v1_release_must_do.md Section 7](./v1_release_must_do.md) - Complete deployment checklist and procedures

**Architecture Diagrams:**
- [Docker Services Architecture](./SYSTEM_AND_ARCHITECTURE.md#26-docker-services-architecture) - Service configuration and dependencies
- [Deployment Architecture](./SYSTEM_AND_ARCHITECTURE.md#appendix-d-deployment-architecture-future-oriented-illustration) - Cloud deployment topology

This document outlines the required environment configuration for deploying Smart Maintenance SaaS. The `.env` file stored at the repository root (`smart-maintenance-saas/.env`) is the authoritative reference for all services (API, UI, MLflow, background agents). Follow the steps below before running docker-compose stacks or provisioning cloud services.

## 1. Prepare the `.env`

1. Make a secure copy of the checked-in `.env` (for example, `cp .env .env.local-prod`).
2. Replace placeholder credentials (`dev_api_key_123`, `dev_secret_key_1234`, etc.) with production-ready secrets generated through your vault or password manager.
3. Protect the resulting file with restricted permissions (`chmod 600 .env.local-prod`) and store it in an encrypted location when not in use.

> **Note:** Do not commit edits containing real secrets. Keep production values out of version control.

## 2. Variable Categories to Validate

| Section | Key Variables | Validation Tips |
|---------|---------------|-----------------|
| Core Runtime | `ENV`, `LOG_LEVEL` | Ensure `ENV=production` for release builds. |
| API Security | `API_KEY`, `SECRET_KEY`, `JWT_SECRET` | Generate high-entropy strings; confirm FastAPI config consumes the same values. |
| Database | `DATABASE_URL` | Verify the DSN uses the async driver (`postgresql+asyncpg://...`) and `ssl=require` if Timescale Cloud is in use. Test connectivity with `poetry run python scripts/check_db.py` (or equivalent). |
| Redis | `REDIS_URL` | Use the `rediss://` scheme for TLS-enabled managed Redis instances. |
| MLflow | `MLFLOW_TRACKING_URI`, `MLFLOW_BACKEND_STORE_URI`, `MLFLOW_ARTIFACT_ROOT`, `AWS_*` | Backend DSN must be synchronous (`postgresql://`). Confirm credentials have access to the specified S3 bucket. |
| UI & Cloud Mode | `API_BASE_URL`, `CLOUD_MODE`, `DEPLOYMENT_ENV` | Set `API_BASE_URL` to the public API endpoint and align `DEPLOYMENT_ENV` with the environment badge you want displayed. |
| Email/Notifications | `EMAIL_SMTP_*` | Leave as disabled placeholders unless email is required; update host/user/pass when enabling notifications. |

## 3. Propagate Secrets to Platforms

- **Docker Compose:** The default `docker-compose.yml` and `docker-compose.production.yml` load the `.env` automatically. Rename your hardened copy back to `.env` (or use `--env-file`) before running `docker compose up`.
- **Render / Railway / Heroku:** Mirror every relevant key/value from the `.env` into the platform’s secret manager. Use clear naming and note rotation owners.
- **CI/CD Pipelines:** Store secrets in the pipeline’s secure variables section. Reference them when building images (`API_KEY=${{ secrets.API_KEY }}`) instead of hardcoding.

## 4. Smoke Validation Checklist

After secrets are in place and services are running, execute the following quick checks:

```bash
# API health endpoints (ensure API_KEY header if required)
curl -H "x-api-key: $API_KEY" https://your-api/health
curl -H "x-api-key: $API_KEY" https://your-api/health/db

# Redis connectivity (inside API container)
poetry run python scripts/check_redis.py

# MLflow readiness
curl https://your-mlflow-host/api/2.0/mlflow/experiments/list

# UI to API smoke (trigger from UI or run smoke script)
poetry run python scripts/smoke_v1.py
```

Document outcomes in `docs/v1_release_must_do.md` under Section 7 (Deployment Checklist) when complete.

## 5. Rotation & Auditing

- Schedule regular secret rotation (API keys, JWT secret, database passwords). Update the `.env` and platform secrets concurrently to avoid drift.
- Maintain an access log noting who changed which value and when.
- Store an encrypted backup of the latest `.env` in your secrets manager for disaster recovery.

Following this checklist ensures every environment uses the same vetted configuration, preventing subtle drift between local, staging, and production deployments.
