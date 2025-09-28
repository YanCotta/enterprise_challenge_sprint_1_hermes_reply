# Smart Maintenance SaaS – Work Status Guide

Last updated: 2025-09-28

## Current Focus

- Finalize validation of production-critical flows after restoring ML endpoints.
- Prepare to rerun the smoke script and golden path demo with ML-backed anomaly detection now working.

## Completed

- Re-enabled MLflow model loading with S3 artifact access and stable backend store.
- Rebuilt stack and confirmed MLflow service health.
- Implemented S3 fallback model loading plus feature schema parsing in `apps/ml/model_loader.py`.
- Hardened `/api/v1/ml/predict` flexible feature handling and SHAP reporting.
- Reworked anomaly detection feature engineering to generate lag/scale features and validated endpoints with normal/anomalous payloads.
- Ran `scripts/smoke_v1.py` inside the API container; flow passed with ingestion verification warning (10 attempts, eventual consistency).

## In Progress

- Maintain this living guide (update as tasks progress).

## Upcoming / To Do

- Run `scripts/smoke_v1.py` inside the API container to verify ingest → predict → decision → metrics path.
- Execute `scripts/test_golden_path_integration.py` (or equivalent golden path demo) to ensure orchestration works with ML artifacts.
- Capture outputs/logs from smoke and golden path runs for upcoming UI verification.

## Blockers & Notes

- None at the moment; anomaly detection endpoint now responds with 200 for both nominal and anomalous scenarios. Monitor sensor ingestion verification latency (smoke script needed 10 attempts, returned WARN).
- Keep AWS credentials available for S3-backed model loading during upcoming tests.

---

_Keep this file updated after each major step so future iterations stay aligned._
