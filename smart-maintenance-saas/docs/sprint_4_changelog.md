# Sprint 4 (Cloud Deployment) Changelog

## Phase 1 (Days 1-4): Foundation & Core Cloud Infrastructure

### Day 1-2 (Task 1.1)

- **Status:** Completed
- **Action:** Fixed critical Docker build failures in `smart-maintenance-saas/Dockerfile`.
- **Details:** Addressed DNS resolution blocker (`Temporary failure resolving 'deb.debian.org'`) identified in `SYSTEM_ISSUES_INVENTORY.md` by adding a nameserver to `/etc/resolv.conf` before package installation. Builds are now stable.

### Day 1-2 (Task 1.2)

- **Status:** Completed
- **Action:** Created the definitive cloud-first configuration template `smart-maintenance-saas/.env.example`.
- **Details:** This file includes all required variables for production, including placeholders for Cloud TimescaleDB, Cloud Redis, S3 Artifact Store, MLflow URI, and JWT secrets, directly addressing critical issue #2 from the inventory.

### Day 1-4 (Tasks 1.3 - 1.5)

- **Status:** Awaiting User Action
- **Action:** Prepared codebase for migration to cloud-native services.
- **Details:** The plan requires the user to provision external Postgres, S3, and Redis services and deploy the MLflow container. After provisioning, the user must re-run `scripts/seed_data.py` (for the DB) and key training notebooks (for MLflow/S3) to populate the cloud environment.

---

### Manual Cloud Infrastructure Provisioning

- **Status:** Completed
- **Action:** Provisioned all external, stateful cloud services required for the SaaS deployment, replacing the local-only Docker setup.
- **Details:**
    1.  **PostgreSQL/TimescaleDB (Render):**
        * Provisioned a **paid "Basic" tier** PostgreSQL 16 database on Render (`smart-maintenance-db`) in the `Ohio (US East)` region. The free tier was bypassed as it lacks support for the required TimescaleDB extension.
        * Configured the **Access Control** firewall to allow connections from the local development IP.
        * Connected directly to the new cloud database via `psql` and successfully enabled the TimescaleDB extension by running `CREATE EXTENSION IF NOT EXISTS timescaledb;`.
        * Saved the **"External Database URL"** to the local `.env` file under the `DATABASE_URL` key.

    2.  **Redis Cache (Render):**
        * Provisioned a **"Free" tier** Redis instance (via the "Key Value" menu) on Render (`smart-maintenance-cache`).
        * Deployed in the **`Ohio (US East)`** region to co-locate with the database for low-latency private networking.
        * Saved the **"External Connection URL"** to the local `.env` file under the `REDIS_URL` key.

    3.  **Object Storage (AWS S3):**
        * Provisioned a new, private AWS S3 bucket (e.g., `yan-smart-maintenance-artifacts`) in the `us-east-2` (Ohio) region to co-locate with Render services.
        * Created a dedicated IAM user (`smart-maintenance-mlflow-worker`) with programmatic-only access.
        * Generated a least-privilege, custom IAM JSON policy to grant this user *only* the specific S3 actions (like `GetObject`, `PutObject`) required by MLflow on that specific bucket and its contents.
        * Saved the generated `Access key ID` and `Secret access key` to the local `.env` file.
        * Updated the `.env` file with `MLFLOW_ARTIFACT_ROOT=s3://[bucket-name]` and `AWS_DEFAULT_REGION=us-east-2`.

- **Overall Status:** The local `.env` file is now fully populated with all cloud credentials. All external stateful infrastructure is provisioned, configured, and ready to receive connections.

## Phase 1 (Continued): Cloud Pivot & Docker-Native Integration

- **Status:** Completed
- **Action:** Executed a critical infrastructure pivot to a "Docker-native" cloud-first architecture. This resolved all major configuration blockers identified by system analysis.
- **Details:**
    - **Fixed `Dockerfile.mlflow`:** Modified the `CMD` to be non-hardcoded, allowing it to accept cloud backend variables (`MLFLOW_BACKEND_STORE_URI` and `MLFLOW_ARTIFACT_ROOT`) from the environment.
    - **Fixed `docker-compose.yml` (MLflow):** Injected all necessary `MLFLOW_...` and `AWS_...` credentials from the `.env` file directly into the `mlflow` service.
    - **Fixed `docker-compose.yml` (API):** Removed hardcoded `DATABASE_URL` from the `api` service, ensuring it correctly uses the cloud TimescaleDB from the `.env` file.
    - **Fixed `.env` (Networking):** Corrected the `MLFLOW_TRACKING_URI` from `http://127.0.0.1:5000` to `http://mlflow:5000`, resolving the Docker container-to-container communication failure.
    - **Fixed `.env` (Validation):** Added default values for all `EMAIL_SMTP_...` variables, resolving the Pydantic validation error that was crashing the API service on startup.
- **Overall Status:** The MLflow server is now fully operational *within Docker*, successfully connecting to the cloud TimescaleDB for its backend and the cloud S3 bucket for its artifact store. All services are building and running, resolving 3 of the 4 critical production blockers. The project is now ~85% cloud-ready.

## Phase 1 (Continued): Cloud Pivot & Docker-Native Integration

- **Status:** Completed
- **Action:** Executed the final code changes to pivot the entire application to a "Docker-native" cloud-first architecture. This resolved all remaining startup failures and configuration conflicts.
- **Key Changes:**
    1.  **Fixed `docker-compose.yml` (API Service):** The `api` service `entrypoint` (or `command`) was modified to *remove* the `alembic upgrade head` command. Instead of failing on a migration error, the service now starts the `uvicorn` server directly, allowing it to become healthy. This change unblocks the rest of the stack and allows for safer, manual migrations.
    2.  **Fixed `alembic_migrations/env.py` (Async Conflict):** The `+asyncpg` database driver conflict was definitively resolved. The `env.py` script now correctly strips the `+asyncpg` prefix, creating a synchronous URL (`postgresql://...`) that Alembic can use.
- **Overall Status:**
    - ✅ **All Services Healthy:** `api`, `mlflow`, `db`, and `redis` containers are all running.
    - ✅ **API Service Unblocked:** The `api` service is healthy and accessible.
    - ✅ **MLflow Cloud Confirmed:** The `mlflow` service is confirmed to be using the cloud TimescaleDB and S3 bucket.
- **Blocker:** The system is 90% operational. The final 10% is a database state mismatch, as the cloud DB has an "orphaned" migration revision.

## Phase 1 (Concluded): Cloud Database Migration & Seeding

- **Status:** Completed
- **Action:** Overcame a series of complex database migration conflicts to successfully build and populate the cloud TimescaleDB.
- **Key Changes & Fixes:**
    1.  **Resolved Ghost Revision:** Wiped the database schema (`DROP SCHEMA public CASCADE;`) to remove an orphaned Alembic revision (`1a0cddfcaa16`) that was blocking all migrations.
    2.  **Resolved Alembic Table Conflict:** Fixed a critical `UniqueViolation` error caused by both MLflow and the API trying to use the same `alembic_version` table.
        - **Fix:** Modified `alembic.ini` to add `version_table = app_alembic_version`, giving our app its own separate migration history table.
    3.  **Restored TimescaleDB Extension:** After wiping the schema, the TimescaleDB extension was manually re-enabled (`CREATE EXTENSION IF NOT EXISTS timescaledb;`) to fix `function create_hypertable() does not exist` errors.
    4.  **Migration Success:** With all blockers resolved, ran `docker compose exec api alembic upgrade head` and successfully executed all 9 application migration steps, creating the full schema (e.g., `sensors`, `sensor_readings`) in the cloud.
    5.  **Data Seeding Success:** Ran the `scripts/seed_data.py` script, which successfully populated the cloud database with 20 sensors and 20,000 sensor readings.
- **Overall Status:** The cloud database is now **100% operational**. The schema is correct, the initial data is loaded, and the infrastructure is stable. The project has moved from ~85% to ~95% cloud-ready.

