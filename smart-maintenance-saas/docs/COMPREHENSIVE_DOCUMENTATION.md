# Comprehensive Documentation Index (V1.0 Consolidated)

**Status:** Active (Superseded authoritative deep-dive now lives in `UNIFIED_SYSTEM_DOCUMENTATION.md`)
**Last Updated:** September 25, 2025
**Purpose:** This file serves as a navigational index to the retained, long-lived documentation set required for operating, extending, and auditing the Smart Maintenance SaaS platform post V1.0.

> CENTRAL SOURCE OF TRUTH → Refer to **`UNIFIED_SYSTEM_DOCUMENTATION.md`** for the consolidated system state, gap analysis, and V1.0 remediation tracking. This index is intentionally lightweight and curated.

---
## 1. Core System Overview
- [Unified System Documentation](./UNIFIED_SYSTEM_DOCUMENTATION.md) – Master system state & roadmap
- [System and Architecture](./SYSTEM_AND_ARCHITECTURE.md) – High-level architecture & component model (kept lean; detailed narratives moved to unified doc)
- [Development Orientation](./DEVELOPMENT_ORIENTATION.md) – Onboarding & internal engineering standards
- [Future Roadmap](./FUTURE_ROADMAP.md) – Post-V1 strategic evolution

## 2. API & Interfaces
- [API Reference](./api.md) – REST endpoints, auth, rate limits, payload contracts
- UI Reference (Streamlit) – See unified document (UI section centralization)

## 3. Data & Storage
- [Database Documentation](./db/README.md) – Schema, indexes, TimescaleDB features
- [ERD Source](./db/erd.dbml) – Entity relationship model
- [Schema DDL](./db/schema.sql) – Canonical SQL schema
- Vector Store: ChromaDB usage documented in unified doc (LearningAgent section)

## 4. Machine Learning & MLOps
- [ML Overview](./ml/README.md) – Training, feature engineering, pipelines
- [Models Summary](./MODELS_SUMMARY.md) – Registry contents & performance matrix
- [Project Gauntlet Plan](./PROJECT_GAUNTLET_PLAN.md) – Real dataset integration execution & validation

## 5. Performance & Testing
- [Performance Baseline](./PERFORMANCE_BASELINE.md) – Validated SLOs + load metrics (kept updated)
- [Day 17 Load Test Report](./DAY_17_LOAD_TEST_REPORT.md) – 103.8 RPS validation evidence
- [Day 18 Performance Results](./DAY_18_PERFORMANCE_RESULTS.md) – TimescaleDB optimization outcomes
- [Load Testing Instructions](./LOAD_TESTING_INSTRUCTIONS.md) – Reproduction guide
- [Coverage Improvement Plan](./COVERAGE_IMPROVEMENT_PLAN.md) – Testing maturation strategy

## 6. Security & Compliance
- [Security Model](./SECURITY.md) – Threat model & mitigations
- [Security Audit Checklist](./SECURITY_AUDIT_CHECKLIST.md) – Audit execution artifact
- Secure Secrets & Rotation: See unified doc (Security Operations section)

## 7. Operations & Deployment
- [Cloud Deployment Guide](./CLOUD_DEPLOYMENT_GUIDE.md) – Environment provisioning & deployment steps
- [Microservice Migration Strategy](./MICROSERVICE_MIGRATION_STRATEGY.md) – Planned decomposition
- S3 Artifact Mapping: See `S3_ARTIFACT_MAPPING.md` if retained (verify during cleanup)

## 8. Event & Agent Framework
- Agent definitions, lifecycle events, routing semantics, and orchestration are now fully centralized in `UNIFIED_SYSTEM_DOCUMENTATION.md` (supersedes deep duplication formerly present in architecture doc).

## 9. Historical / Program Documentation
- [30-Day Sprint Changelog](./30-day-sprint-changelog.md) – Strategic & operational history
- Final Sprint Summary: Consolidated into unified doc

## 10. Deprecated / Removed (Not Reintroduced)
The following prior analysis or interim documents were intentionally consolidated or removed to reduce duplication and drift risk:
- Old multi-part architecture deep dives (merged)
- Interim anomaly detection notes (merged)
- Early planning scratch files

## 11. How to Maintain This Index
| Action | Trigger | Owner | SLA |
|--------|--------|-------|-----|
| Add new doc link | New persistent reference doc added | Tech Lead | < 24h |
| Remove stale link | File deleted or merged into unified doc | Any Contributor | Immediate |
| Revalidate cross-links | Quarterly or major release | Documentation Owner | Quarterly |
| Sync with Unified Doc | Structural shift in system scope | Tech Lead | Within sprint |

## 12. Quick Cross-Link Integrity Checklist
- [ ] `UNIFIED_SYSTEM_DOCUMENTATION.md` exists and is current
- [ ] All relative links resolve (manual or CI doc link checker)
- [ ] No references to deleted interim analysis files
- [ ] Performance section reflects latest validated run
- [ ] Security checklist still aligned with deployed architecture

---
### Change Log (for this file only)
| Date | Change | Author |
|------|--------|--------|
| 2025-09-25 | Initial creation of consolidated index replacing legacy comprehensive doc variant | AI Assistant |

---
**Principle:** Minimize duplication. Deep content belongs in the unified doc or the domain-specific file; this index points, it doesn’t repeat.
