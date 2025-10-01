# Smart Maintenance SaaS

*[**English**](README.md) | [Português](README_PORTUGUES.md)*

**Status:** V1.0 Production Ready | Documentation Synchronized  
**Last Updated:** 2025-09-30

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![Status](https://img.shields.io/badge/Status-V1.0%20Ready-brightgreen)](.)
[![Models](https://img.shields.io/badge/MLflow-17%2B%20Models-blue)](.)
[![Performance](https://img.shields.io/badge/API%20Response-<2s-purple)](.)
[![Cloud](https://img.shields.io/badge/Cloud-Ready-orange)](.)

## Overview

A production-ready predictive maintenance SaaS platform optimized for industrial applications. Features cloud-native deployment (TimescaleDB, Redis, S3), multi-agent orchestration with event-driven workflows, and ML-powered maintenance insights. V1.0 delivers core capabilities with intentional feature deferrals documented in the deployment playbook.

**Architecture Visualizations:** See [System Architecture Diagrams](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#2-system-architecture-visualizations) for comprehensive visual guides including:
- [High-Level System Overview](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#21-high-level-system-overview) - Complete system architecture
- [Multi-Agent System](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#27-complete-multi-agent-system-architecture) - 12 specialized agents
- [Data Ingestion Pipeline](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#29-data-ingestion-and-processing-pipeline) - Event-driven data flow
- [API Endpoints](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#214-api-endpoints-architecture) - REST API structure

## Quick Start

**Prerequisites:** Docker & Docker Compose, cloud services configured

```bash
git clone <repo>
cd enterprise_challenge_sprint_1_hermes_reply/smart-maintenance-saas

# Configure environment
cp .env_example.txt .env
# Fill in cloud credentials (TimescaleDB, Redis, S3, MLflow)

# Deploy
docker compose up -d --build

# Access UI: http://localhost:8501
# API Health: http://localhost:8000/health
```

## Core Capabilities

**V1.0 Delivered:**
- Data ingestion + explorer ([see pipeline diagram](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#29-data-ingestion-and-processing-pipeline))
- ML prediction (auto version resolve) ([see ML pipeline](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#23-mlflow-model-management-pipeline))
- Basic model metadata explorer (state differentiation)
- Drift & anomaly on-demand checks ([see MLOps automation](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#28-mlops-automation-drift-detection-to-retraining))
- Golden Path demo (90s timeout protection) ([see event flow](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#22-production-event-driven-architecture-flow))
- Decision audit log (CSV export)
- Reporting (JSON-only prototype)
- Metrics snapshot (non-streaming)
- Simulation console (normal/drift/anomaly scenarios)
- Central stability layer (safe rerun abstraction)

## Minimal V1.0 Scope vs Deferred

### ✅ V1.0 Delivered Capabilities
1. **Data ingestion + explorer** - Single file ingestion with correlation tracking and pagination
2. **ML prediction** - Auto version resolution with model registry integration (MLflow optional)
3. **Model metadata explorer** - State differentiation (disabled/empty/error/populated)
4. **Drift & anomaly detection** - On-demand KS-test and Isolation Forest analysis
5. **Golden Path demo** - Instrumented workflow with 90s timeout protection and event monitoring
6. **Decision audit log** - Human decisions persisted with filtering and CSV export
7. **Reporting prototype** - JSON report generation with chart previews (artifacts deferred)
8. **Metrics snapshot** - Point-in-time Prometheus metrics (streaming deferred)
9. **Simulation console** - Normal/drift/anomaly test scenarios with latency tracking
10. **Stability layer** - Central safe rerun abstraction preventing runtime crashes

### 🚫 Deferred to V1.5+ (Explicitly Out-of-Scope)
- Report artifacts (file generation/download)
- Real-time metrics streaming  
- Background SHAP processing
- Bulk ingestion & batch prediction
- Multi-sensor correlation / composite analytics
- Model recommendations caching/virtualization
- Advanced notifications UI
- Feature store visualization / lineage
- Governance & retention policies

## Links Matrix

### Authoritative Documentation (Single Source of Truth)
- [V1.0 Deployment Playbook](smart-maintenance-saas/docs/v1_release_must_do.md) - **Canonical reference**: Replaces former backlog, readiness checklist, and audit docs; merged scope, tasks, and deployment procedures
- [UI Redesign Changelog](smart-maintenance-saas/docs/ui_redesign_changelog.md) - V1.0 UI evolution trail with feature implementations and fixes
- [Sprint 4 Changelog](smart-maintenance-saas/docs/legacy/sprint_4_changelog.md) - Cloud deployment milestones, MLflow integration, and infrastructure achievements
- [Executive Summary](smart-maintenance-saas/docs/EXECUTIVE_SUMMARY.md) - System stabilization status and V1.0 readiness confirmation

### Core Documentation
- [System & Architecture](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md) - High-level architecture with comprehensive diagrams ([visualizations index](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#2-system-architecture-visualizations))
- [API Reference](smart-maintenance-saas/docs/api.md) - REST endpoints & integration ([see API architecture diagram](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#214-api-endpoints-architecture))
- [Database Documentation](smart-maintenance-saas/docs/db/README.md) - Schema & TimescaleDB features ([see DB architecture](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#24-timescaledb-performance-architecture))
- [ML Documentation](smart-maintenance-saas/docs/ml/README.md) - Models & pipelines ([see ML pipeline diagram](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#23-mlflow-model-management-pipeline))
- [Security Documentation](smart-maintenance-saas/docs/SECURITY.md) - Security architecture ([see security flow](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#211-security-and-authentication-flow))

### Performance & Testing  
- [Load Test Results](smart-maintenance-saas/docs/legacy/DAY_17_LOAD_TEST_REPORT.md) - 103.8 RPS validation (archived)
- [Performance Results](smart-maintenance-saas/docs/legacy/DAY_18_PERFORMANCE_RESULTS.md) - TimescaleDB optimization (archived)
- [Performance Baseline](smart-maintenance-saas/docs/legacy/PERFORMANCE_BASELINE.md) - SLO targets & metrics (archived)
- [Coverage Plan](smart-maintenance-saas/docs/legacy/COVERAGE_IMPROVEMENT_PLAN.md) - Test coverage strategy (archived)

### Operations & Deployment
- [Cloud Deployment Guide](smart-maintenance-saas/docs/CLOUD_DEPLOYMENT_GUIDE.md) - Platform-specific deployment (Render, Railway, Heroku) with environment setup ([see deployment architecture](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#appendix-d-deployment-architecture-future-oriented-illustration))
- [Deployment Setup](smart-maintenance-saas/docs/DEPLOYMENT_SETUP.md) - Environment configuration and .env management ([see Docker services](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md#26-docker-services-architecture))
- [DVC Setup Guide](smart-maintenance-saas/docs/DVC_SETUP_GUIDE.md) - Data version control setup
- [Development Orientation](smart-maintenance-saas/docs/legacy/DEVELOPMENT_ORIENTATION.md) - Engineering standards (archived)

### Legacy & Historical
- [Legacy Documentation Index](smart-maintenance-saas/docs/legacy/INDEX.md) - Archived historical documents

## Contribution

Contributions welcome for V1.0+ enhancements. Review process:

1. Consult [V1.0 Deployment Playbook](smart-maintenance-saas/docs/v1_release_must_do.md) for current scope and deferred features
2. Verify alignment with delivered capabilities (no V1.0 scope creep)
3. Test changes against existing test suites (see `tests/` directory)
4. Update relevant documentation for architectural or API changes
5. Follow [Security Documentation](smart-maintenance-saas/docs/SECURITY.md) guidelines for security-related changes

---

**V1.0 Release:** All core workflows operational with cloud deployment verified. Backend capabilities at 100% readiness; UI intentionally exposes minimal workflow set per deployment playbook Section 2.

**Next Phase:** V1.1 hardening (enhanced test coverage, metrics percentiles, artifact persistence design) begins after user feedback cycle.
