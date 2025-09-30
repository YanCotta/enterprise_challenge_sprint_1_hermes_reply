# Smart Maintenance SaaS - Deployment Setup Guide

## Overview

This guide walks you through deploying the Smart Maintenance SaaS platform on a VM. The deployment uses Docker Compose to orchestrate all services.

## Prerequisites

- Linux VM (Ubuntu 20.04+ recommended) or macOS
- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ RAM
- 20GB+ disk space
- Network access to:
  - Docker Hub (for pulling images)
  - GitHub (for cloning repo)
  - AWS S3 (optional, for MLflow artifacts)

## Quick Start

For experienced users:

```bash
# 1. Clone repository
git clone https://github.com/YanCotta/enterprise_challenge_sprint_1_hermes_reply.git
cd enterprise_challenge_sprint_1_hermes_reply/smart-maintenance-saas

# 2. Create and configure .env
cp .env_example.txt .env
# Edit .env with your values (see Configuration section)

# 3. Deploy
bash scripts/deploy_vm.sh
```

## Detailed Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/YanCotta/enterprise_challenge_sprint_1_hermes_reply.git
cd enterprise_challenge_sprint_1_hermes_reply/smart-maintenance-saas
```

### Step 2: Create Environment Configuration

Create your `.env` file from the example:

```bash
cp .env_example.txt .env
```

### Step 3: Configure Environment Variables

Edit the `.env` file with your actual values. **All values marked as REQUIRED must be set.**

#### Core Settings

```bash
ENV=production
LOG_LEVEL=INFO
```

#### API Security (REQUIRED)

Generate secure random keys:

```bash
# Generate API key
API_KEY=$(openssl rand -hex 32)

# Generate secret key
SECRET_KEY=$(openssl rand -hex 64)

# Generate JWT secret
JWT_SECRET=$(openssl rand -hex 64)

# Add to .env file
echo "API_KEY=${API_KEY}" >> .env
echo "SECRET_KEY=${SECRET_KEY}" >> .env
echo "JWT_SECRET=${JWT_SECRET}" >> .env
```

#### Database Configuration (REQUIRED)

**Option A: Use Local Docker Database (Recommended for testing)**

```bash
DATABASE_URL=postgresql+asyncpg://smart_user:strong_password@db:5432/smart_maintenance_db
```

**Option B: Use TimescaleDB Cloud**

1. Create account at https://www.timescale.com/cloud
2. Create new database
3. Get connection string and convert to asyncpg format:

```bash
# Format: postgresql+asyncpg://user:password@host:port/dbname?sslmode=require
DATABASE_URL=postgresql+asyncpg://your_user:your_password@your_host.timescaledb.cloud:5432/your_db?sslmode=require
```

#### Redis Configuration (REQUIRED)

**Option A: Use Local Docker Redis (Recommended for testing)**

```bash
REDIS_URL=redis://redis:6379
```

**Option B: Use Render Redis**

1. Create account at https://render.com
2. Create new Redis instance
3. Get connection string:

```bash
REDIS_URL=rediss://user:password@your-redis.render.com:6379
```

#### MLflow Configuration (OPTIONAL)

**Option A: Use Local MLflow with Docker (Recommended)**

```bash
MLFLOW_TRACKING_URI=http://mlflow:5000
MLFLOW_BACKEND_STORE_URI=postgresql://smart_user:strong_password@db:5432/smart_maintenance_db
MLFLOW_ARTIFACT_ROOT=./mlflow_data
DISABLE_MLFLOW_MODEL_LOADING=false
```

**Option B: Use MLflow with S3 Artifacts**

1. Create AWS S3 bucket
2. Create IAM user with S3 access
3. Configure:

```bash
MLFLOW_TRACKING_URI=http://mlflow:5000
MLFLOW_BACKEND_STORE_URI=postgresql://smart_user:strong_password@db:5432/smart_maintenance_db
MLFLOW_ARTIFACT_ROOT=s3://your-bucket-name/mlflow-artifacts
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1
DISABLE_MLFLOW_MODEL_LOADING=false
```

**Option C: Disable MLflow (For Offline/Limited Mode)**

```bash
DISABLE_MLFLOW_MODEL_LOADING=true
```

#### UI Configuration

```bash
API_BASE_URL=http://api:8000
```

If deploying behind a reverse proxy, use the public URL:

```bash
API_BASE_URL=https://your-domain.com/api
```

#### Notification Configuration (OPTIONAL)

```bash
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_TLS=true
EMAIL_SMTP_USER=your_email@gmail.com
EMAIL_SMTP_PASS=your_app_password
EMAIL_TO=alerts@your-company.com
```

### Step 4: Validate Configuration

Verify your `.env` file has all required values:

```bash
# Check for required variables
grep -E "^(DATABASE_URL|REDIS_URL|API_KEY|SECRET_KEY|JWT_SECRET)=" .env
```

All variables should have non-empty values after the `=` sign.

### Step 5: Deploy Services

Run the automated deployment script:

```bash
bash scripts/deploy_vm.sh
```

The script will:
1. ✅ Validate .env file
2. ✅ Check Docker availability
3. ✅ Build Docker images
4. ✅ Start all services
5. ✅ Wait for health checks
6. ✅ Run smoke tests

**Expected output:**
```
==================================================
  Smart Maintenance SaaS - VM Deployment
==================================================

Step 1: Validating environment configuration...
✓ Environment configuration validated

Step 2: Checking required environment variables...
✓ All required variables set

...

==================================================
  Deployment Complete!
==================================================

Services are now running:
  - API:       http://localhost:8000
  - UI:        http://localhost:8501
  - API Docs:  http://localhost:8000/docs
```

### Step 6: Verify Deployment

#### Check Service Status

```bash
docker-compose ps
```

Expected output:
```
NAME                     STATUS              PORTS
smart_maintenance_api    Up (healthy)        0.0.0.0:8000->8000/tcp
smart_maintenance_ui     Up                  0.0.0.0:8501->8501/tcp
smart_maintenance_db     Up (healthy)        0.0.0.0:5433->5432/tcp
smart_maintenance_redis  Up (healthy)        0.0.0.0:6379->6379/tcp
mlflow                   Up (healthy)        0.0.0.0:5000->5000/tcp
```

#### Test Health Endpoints

```bash
# API health
curl http://localhost:8000/health

# Database health
curl http://localhost:8000/health/db

# Redis health
curl http://localhost:8000/health/redis
```

#### Access Web Interfaces

- **UI:** http://localhost:8501
- **API Docs:** http://localhost:8000/docs
- **MLflow:** http://localhost:5000

## Common Issues & Solutions

### Issue: Port Already in Use

**Error:** `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Solution:**
```bash
# Find and stop conflicting service
sudo lsof -i :8000
# Or change port in docker-compose.yml
```

### Issue: Health Check Timeout

**Error:** `API health check timed out after 120s`

**Solution:**
```bash
# Check API logs
docker-compose logs api

# Common causes:
# 1. Database connection failed - verify DATABASE_URL
# 2. Redis connection failed - verify REDIS_URL
# 3. Insufficient memory - check `docker stats`
```

### Issue: Database Connection Failed

**Error:** `sqlalchemy.exc.OperationalError: could not connect to server`

**Solution:**
```bash
# Verify DATABASE_URL format
# For local: postgresql+asyncpg://smart_user:strong_password@db:5432/smart_maintenance_db
# For cloud: postgresql+asyncpg://user:pass@host:port/db?sslmode=require

# Test database directly
docker-compose exec db psql -U smart_user -d smart_maintenance_db
```

### Issue: Permission Denied

**Error:** `permission denied while trying to connect to the Docker daemon socket`

**Solution:**
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Or use sudo
sudo docker-compose up -d
```

## Production Recommendations

### 1. Use External Database

For production, use a managed database service:
- TimescaleDB Cloud
- AWS RDS PostgreSQL with TimescaleDB extension
- Azure Database for PostgreSQL

### 2. Use External Redis

For production, use a managed Redis service:
- Render Redis
- AWS ElastiCache
- Azure Cache for Redis

### 3. Configure Reverse Proxy

Use nginx or Traefik for:
- SSL/TLS termination
- Domain routing
- Load balancing

Example nginx configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 4. Set Up Monitoring

Configure Prometheus + Grafana:

```bash
# Add to docker-compose.yml
docker-compose up -d grafana
```

Access Grafana at http://localhost:3000 (default: admin/admin)

### 5. Configure Backups

Set up automated database backups:

```bash
# Add to crontab
0 2 * * * /path/to/smart-maintenance-saas/scripts/backup_db.sh
```

### 6. Resource Limits

Configure resource limits in docker-compose.yml:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

## Maintenance Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f ui
docker-compose logs -f db
```

### Restart Services

```bash
# All services
docker-compose restart

# Specific service
docker-compose restart api
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v
```

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose build --no-cache
docker-compose up -d
```

### Database Backup

```bash
# Create backup
bash scripts/backup_db.sh

# Restore from backup
bash scripts/restore_db.sh backup.sql
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Generate strong random keys for API_KEY, SECRET_KEY, JWT_SECRET
- [ ] Use HTTPS/TLS in production (reverse proxy)
- [ ] Restrict database access to application only
- [ ] Enable firewall (ufw/iptables)
- [ ] Keep Docker and system packages updated
- [ ] Review API key permissions and create separate keys for different users
- [ ] Set up log monitoring and alerting
- [ ] Enable database encryption at rest
- [ ] Configure network isolation between services

## Troubleshooting

### Get Container Status

```bash
docker-compose ps
docker-compose top
docker stats
```

### Check Resource Usage

```bash
# Memory usage
docker stats --no-stream

# Disk usage
docker system df
```

### Access Container Shell

```bash
# API container
docker-compose exec api bash

# Database container
docker-compose exec db bash
```

### Reset Everything

**WARNING: This deletes all data**

```bash
docker-compose down -v
docker system prune -a -f --volumes
rm -rf logs/* mlflow_data/*
```

Then start fresh with `bash scripts/deploy_vm.sh`

## Support

For issues not covered here:

1. Check logs: `docker-compose logs`
2. Review SYSTEM_AUDIT_REPORT.md for detailed architecture
3. Check API documentation: http://localhost:8000/docs
4. Open GitHub issue with:
   - Error message
   - Relevant logs
   - Environment details (OS, Docker version)

## Next Steps

After successful deployment:

1. ✅ Test UI at http://localhost:8501
2. ✅ Explore API docs at http://localhost:8000/docs
3. ✅ Run validation tests (see SYSTEM_AUDIT_REPORT.md)
4. ✅ Configure monitoring and alerting
5. ✅ Set up automated backups
6. ✅ Review security checklist
7. ✅ Train team on operational procedures

---

**Last Updated:** 2025-01-02  
**Version:** 1.0
