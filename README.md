# Smart Maintenance SaaS

*[**English**](README.md) | [Português](README_PORTUGUES.md)*

**Status:** Stable (Minimal V1.0 Scope) | Readiness: 94.5% | Deferred Features Tracked  
**Last Synchronized:** 2025-12-19

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
[![Status](https://img.shields.io/badge/Status-V1.0%20Ready-brightgreen)](.)
[![Models](https://img.shields.io/badge/MLflow-17%2B%20Models-blue)](.)
[![Performance](https://img.shields.io/badge/API%20Response-<2s-purple)](.)
[![Cloud](https://img.shields.io/badge/Cloud-Ready-orange)](.)

## DOCUMENTATION OUTDATED, WILL BE UPDATED BY 10/03, AT V1.0 RELEASE

## Overview

A production-ready predictive maintenance platform delivering V1.0 minimal scope with 94.5% readiness. Features cloud-native deployment, multi-agent orchestration, and data-driven maintenance insights optimized for industrial applications.

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
- Data ingestion + explorer  
- ML prediction (auto version resolve)
- Basic model metadata explorer (state differentiation)
- Drift & anomaly on-demand checks
- Golden Path demo (90s timeout protection)
- Decision audit log (CSV export)
- Reporting (JSON-only prototype)
- Metrics snapshot (non-streaming)
- Simulation console (normal/drift/anomaly scenarios)
- Central stability layer (safe rerun abstraction)

## Minimal V1.0 Scope vs Deferred

### ✅ V1.0 Minimal Scope (Delivered - 94.5% Ready)
1. **Data ingestion + explorer** - Single file ingestion with correlation tracking
2. **ML prediction** - Auto version resolve (SHAP intentionally deferred)  
3. **Basic model metadata explorer** - State differentiation (disabled/empty/error/populated)
4. **Drift & anomaly on-demand checks** - Manual trigger analysis
5. **Golden Path demo** - Instrumented workflow with 90s timeout protection
6. **Decision audit log** - Human decisions persisted with CSV export
7. **Reporting** - JSON-only prototype (artifact downloads deferred)
8. **Metrics snapshot** - Point-in-time metrics (streaming deferred)
9. **Simulation console** - Normal/drift/anomaly test scenarios
10. **Stability layer** - Central safe rerun abstraction

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

### Authoritative Documentation (Truth Sources)
- [Executive Summary](smart-maintenance-saas/docs/EXECUTIVE_SUMMARY.md) - System stabilization status
- [Prioritized Backlog](smart-maintenance-saas/docs/PRIORITIZED_BACKLOG.md) - V1.0 scope & deferred features  
- [V1.0 Readiness Checklist](smart-maintenance-saas/docs/V1_READINESS_CHECKLIST.md) - 94.5% readiness assessment
- [System Capabilities & UI Redesign](smart-maintenance-saas/docs/SYSTEM_CAPABILITIES_AND_UI_REDESIGN.md) - Complete capability matrix
- [UI Redesign Changelog](smart-maintenance-saas/docs/ui_redesign_changelog.md) - V1.0 evolution trail

### Core Documentation
- [System & Architecture](smart-maintenance-saas/docs/SYSTEM_AND_ARCHITECTURE.md) - High-level architecture
- [API Reference](smart-maintenance-saas/docs/api.md) - REST endpoints & integration
- [Database Documentation](smart-maintenance-saas/docs/db/README.md) - Schema & TimescaleDB features
- [ML Documentation](smart-maintenance-saas/docs/ml/README.md) - Models & pipelines
- [Security Documentation](smart-maintenance-saas/docs/SECURITY.md) - Security architecture

### Performance & Testing  
- [Performance Baseline](smart-maintenance-saas/docs/PERFORMANCE_BASELINE.md) - SLO targets & metrics
- [Load Test Results](smart-maintenance-saas/docs/DAY_17_LOAD_TEST_REPORT.md) - 103.8 RPS validation
- [Test Plan V1](smart-maintenance-saas/docs/TEST_PLAN_V1.md) - Test strategy framework
- [Coverage Plan](smart-maintenance-saas/docs/COVERAGE_IMPROVEMENT_PLAN.md) - Test coverage strategy

### Operations & Deployment
- [Cloud Deployment Guide](smart-maintenance-saas/docs/CLOUD_DEPLOYMENT_GUIDE.md) - Cloud setup & provisioning  
- [DVC Setup Guide](smart-maintenance-saas/docs/DVC_SETUP_GUIDE.md) - Data version control
- [Development Orientation](smart-maintenance-saas/docs/DEVELOPMENT_ORIENTATION.md) - Engineering standards

### Legacy & Historical
- [Legacy Documentation Index](smart-maintenance-saas/docs/legacy/INDEX.md) - Archived historical documents

## Contribution

This is V1.0 production-ready software. For contributions:

1. Review authoritative scope in V1_READINESS_CHECKLIST.md
2. Align with minimal V1.0 feature set (no scope creep)  
3. Test changes against existing test suite
4. Update documentation for any architectural changes
5. Follow security audit checklist for security-related changes

---

**V1.0 Achievement:** 94.5% production readiness with all core workflows operational and deployment blockers resolved.

**Next Phase:** V1.1 hardening (enhanced test coverage, metrics percentiles, artifact persistence design) begins after user feedback cycle.
