# Legacy Documentation Index

**Last Updated:** 2025-10-03  
**Status:** Archived - Historical reference only

> **Important:** This directory contains documents predating the V1.0 production release and scope consolidation. For current system documentation, refer to [V1_UNIFIED_DEPLOYMENT_CHECKLIST.md](../V1_UNIFIED_DEPLOYMENT_CHECKLIST.md) and [UNIFIED_CLOUD_DEPLOYMENT_GUIDE.md](../UNIFIED_CLOUD_DEPLOYMENT_GUIDE.md) as the single sources of truth. The legacy [v1_release_must_do.md](./v1_release_must_do.md) is also available as a historical reference.

## Purpose

These documents are preserved for:
- Historical development context and audit trail
- Understanding architecture evolution decisions  
- Sprint milestone achievements (cloud deployment, MLflow integration)
- Deprecated feature analysis from pre-V1.0 planning

**Warning:** These documents may contain outdated claims, deprecated features, or references to superseded files. Always cross-reference with current authoritative documentation before relying on their content.

## Archived Documents

### Historical Changelogs
| File | Description | Key Content | Date Range |
|------|-------------|-------------|------------|
| [30-day-sprint-changelog.md](./30-day-sprint-changelog.md) | Sprint 3 development log | Early multi-agent development, performance testing | Pre-2025-09-23 |
| [sprint_4_changelog.md](./sprint_4_changelog.md) | Sprint 4 cloud deployment achievements | TimescaleDB/Redis/S3 provisioning, MLflow S3 integration, 17+ models trained | 2025-09-23 to 2025-09-24 |

### Archived System Documentation
| File | Original Purpose | Superseded By | Notes |
|------|-----------------|---------------|-------|
| [UI_FEATURES_LEGACY.md](./UI_FEATURES_LEGACY.md) | V1.0 UI hardening requirements | [v1_release_must_do.md Section 2.2](../v1_release_must_do.md) | Pre-consolidation UI analysis |
| [UNIFIED_SYSTEM_DOCUMENTATION_LEGACY_UI.md](./UNIFIED_SYSTEM_DOCUMENTATION_LEGACY_UI.md) | Pre-V1.0 unified system doc | [v1_release_must_do.md](../v1_release_must_do.md) | Predates playbook consolidation |
| [COVERAGE_IMPROVEMENT_PLAN.md](./COVERAGE_IMPROVEMENT_PLAN.md) | Test coverage strategy | [v1_release_must_do.md Section 6](../v1_release_must_do.md) | Testing now in playbook |
| [DEVELOPMENT_ORIENTATION.md](./DEVELOPMENT_ORIENTATION.md) | Engineering standards | Still relevant; archived for reference | Development guidelines |
| [FUTURE_ROADMAP.md](./FUTURE_ROADMAP.md) | Strategic planning | [v1_release_must_do.md Section 3](../v1_release_must_do.md) | Deferred features documented in playbook |

### Performance & Testing (Archived)
| File | Description | Status | Notes |
|------|-------------|--------|-------|
| [DAY_17_LOAD_TEST_REPORT.md](./DAY_17_LOAD_TEST_REPORT.md) | Load test validation (103.8 RPS) | Historical evidence | Performance validated |
| [DAY_18_PERFORMANCE_RESULTS.md](./DAY_18_PERFORMANCE_RESULTS.md) | TimescaleDB optimization results | Historical evidence | 37.3% improvement documented |
| [PERFORMANCE_BASELINE.md](./PERFORMANCE_BASELINE.md) | SLO targets and metrics | Historical reference | Targets met in V1.0 |
| [LOAD_TESTING_INSTRUCTIONS.md](./LOAD_TESTING_INSTRUCTIONS.md) | Load testing guide | Historical reference | Tools and methodology |

### Security (Archived)
| File | Description | Notes |
|------|-------------|-------|
| [SECURITY_AUDIT_CHECKLIST.md](./SECURITY_AUDIT_CHECKLIST.md) | Security audit framework | Key findings integrated into v1_release_must_do.md Section 2.1 |

### Strategic Planning (Archived)
| File | Description | Status |
|------|-------------|--------|
| [MICROSERVICE_MIGRATION_STRATEGY.md](./MICROSERVICE_MIGRATION_STRATEGY.md) | Future microservice migration strategy | Post-V1.0 consideration; current monolith architecture meets V1.0 needs |
| [PROJECT_GAUNTLET_PLAN.md](./PROJECT_GAUNTLET_PLAN.md) | Real dataset integration execution | Completed; 17+ models trained per sprint_4_changelog.md |

## For Current System Documentation

**Single Source of Truth:** [v1_release_must_do.md](../v1_release_must_do.md) - V1.0 Deployment Playbook

This playbook consolidates and replaces:
- Former Prioritized Backlog
- V1 Readiness Checklist
- System Capabilities & UI Redesign doc
- Standalone must-do lists
- Latest system audit reports

**Additional Authoritative References:**
1. [EXECUTIVE_SUMMARY.md](../EXECUTIVE_SUMMARY.md) - System status aligned with playbook
2. [ui_redesign_changelog.md](../ui_redesign_changelog.md) - V1.0 UI evolution trail
3. [COMPREHENSIVE_DOCUMENTATION.md](../COMPREHENSIVE_DOCUMENTATION.md) - Complete documentation index
4. [SYSTEM_AND_ARCHITECTURE.md](../SYSTEM_AND_ARCHITECTURE.md) - High-level architecture

---

**Archival Policy:** Documents remain in `legacy/` for audit trail and historical context. They are not updated post-archival. Any contradictions with current documentation should be resolved in favor of the V1.0 Deployment Playbook.