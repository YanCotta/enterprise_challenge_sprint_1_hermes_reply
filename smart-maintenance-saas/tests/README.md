# Smart Maintenance SaaS - Test Documentation

**Last Updated:** 2025-10-03  
**Status:** V1.0 Critical Path Coverage  
**Related:** [v1_release_must_do.md Section 6](../docs/legacy/v1_release_must_do.md) - Testing & validation plan

Test organization, execution guide, and coverage status for the Smart Maintenance SaaS platform.

- **[Test Documentation](./README.md)** - Test organization and execution guide
- **[Coverage Improvement Plan](../docs/COVERAGE_IMPROVEMENT_PLAN.md)** - Test coverage strategy and current status

## Machine Learning & Data Science

### ML Documentation

- **[ML Documentation](../docs/ml/README.md)** - Machine learning models and pipelines
- **[Models Summary](../docs/MODELS_SUMMARY.md)** - Overview of all 17+ production models
- **[Project Gauntlet Plan](../docs/PROJECT_GAUNTLET_PLAN.md)** - Real-world dataset integration execution

## Security & Operations

### Security Documentation

- **[Security Documentation](../docs/SECURITY.md)** - Security architecture and implementation
- **[Security Audit Checklist](../docs/SECURITY_AUDIT_CHECKLIST.md)** - Comprehensive security audit framework

### Service Documentation

- **[Anomaly Service](../services/anomaly_service/README.md)** - Future anomaly detection microservice
- **[Prediction Service](../services/prediction_service/README.md)** - Future ML prediction microservice

---

*This index is automatically maintained and appears at the top of all documentation files for easy navigation.*

---

# Testing Strategy (Synchronized with Changelog Days 4–23)

Status: 410 PASSED / 1 FAILED (known low‑severity scheduling edge case)

---

## 1. Objectives

Ensure:
- Functional correctness across ingestion → anomaly → prediction → drift → retrain.
- Performance & scalability baselines (load, query optimization).
- Resilience under infra faults (Redis / DB latency, network partitions).
- Security controls (auth, rate limiting, dependency scanning).
- ML lifecycle integrity (model reproducibility, hash stability, drift automation).

---

## 2. Layered Test Taxonomy

| Layer | Scope | Key Focus | Changelog Link |
|-------|-------|-----------|----------------|
| Unit | Pure functions, feature transformers, utility classes | Determinism, edge cases | Days 8–10 (feature eng) |
| Integration | DB, Redis, event bus, model loader, drift logic | Schema, indexing, retries | Days 12,13,18 |
| End-to-End | Full workflow (ingest→anomaly→prediction→(sched)→drift) | Cross-component flow | Days 12–13 |
| Load (Locust) | High concurrency endpoints & registry | Latency, throughput SLOs | Day 17 |
| Resilience / Chaos | Toxiproxy (latency, timeouts, partitions) | Graceful degradation, retries | Day 15 |
| Security | Rate limiting, auth rejection, Snyk, dependency scan | DoS protection, supply chain | Days 16,21 |
| ML Integrity | Model hash validation, feature contract, drift detection | Reproducibility, lifecycle | Days 21,23 |
| Data Export | Full + incremental CSV correctness | Timestamp delta logic | Day 14 |
| Performance DB | Index & CAGG impact | Query plan / speed gain | Day 18 |

---

## 3. Current Test Status

| Metric | Value |
|--------|-------|
| Total Tests | 411 |
| Passed | 410 |
| Failed | 1 (Scheduling slot availability timing) |
| Success Rate | 99.8% |
| Coverage (Line) | ≥80% (CI enforced) |

Failing Test: `tests/e2e/test_e2e_full_system_workflow.py::test_full_workflow_from_ingestion_to_scheduling`  
Reason: Calendar window edge near business-hour cutoff → no technician slot. Business logic validated manually; deferral accepted (see Day 12/15 recovery notes).

---

## 4. Day-to-Test Mapping (Traceability)

| Day(s) | Feature / Change | Representative Tests |
|--------|------------------|----------------------|
| 4 | Idempotent ingestion (Idempotency-Key) + request IDs | api ingest duplicate test |
| 6 | Structured logging, event retry | integration event bus retry test |
| 7 | Dataset & docs readiness | data seeding validation tests |
| 8–10 | Feature engineering, anomaly & forecast models | unit/ml feature transformer tests |
| 10.5 | Forecast tuning challenger evaluation | ML integrity comparison tests |
| 11 | MLflow loader + registry load | registry load / model cache tests |
| 12 | Predict endpoint recovery + composite index | prediction path integration test |
| 13 | Drift endpoint (KS test) + async infra | e2e drift workflow test |
| 13.5–13.8 | MLflow persistence & multi‑model catalog | model hash & loader tests |
| 14 | Incremental export | export incremental append tests |
| 15 | Redis idempotency + resilience (Toxiproxy) | resilience tests (redis timeout) |
| 16 | Rate limiting (slowapi) | rate limit exceed test |
| 17 | 50-user load baseline | locust scenario (manual / CI optional) |
| 18 | Timescale CAGG & index perf | aggregation speed / row reduction assertion |
| 19–20 | Microservice scaffolding (dormant) | presence / health stub tests |
| 21 | Model hash validation CI job | hash baseline comparison |
| 23 | Drift agent + retrain agent events | simulated event emission & cooldown tests |

---

## 5. Directory Structure (Relevant)

```
tests/
  unit/              # Pure logic & transformers
  integration/       # DB / Redis / event bus / drift
  e2e/               # Multi-step workflows
  api/               # Endpoint contract & auth/rate limit
  data/              # Generators / fixtures
  performance/ (opt) # DB/query benchmarks
  conftest.py        # Async loop, fixtures, testcontainers
```

---

## 6. Key Fixtures & Infrastructure

| Fixture | Purpose | Notes |
|---------|---------|-------|
| event_loop (session) | Stable asyncio loop | Prevents cross-loop errors (Day 13) |
| db_session | Async DB session bound to test DB / testcontainer | Ensures isolation |
| redis_client | Idempotency + pub/sub simulation | Falls back if offline |
| toxiproxy_client | Injects latency / timeouts | Resilience assertions |
| model_registry_tmp | Loads MLflow artifacts (read-only) | Caches run URIs |

---

## 7. Markers & Selection

| Marker | Usage |
|--------|-------|
| unit | Fast isolated logic |
| integration | External services (DB/Redis) |
| e2e | Full business flow |
| slow | Optional long or perf |
| db | Direct DB dependency |
| smoke | Minimal deploy gate |
| resilience | Chaos / fault injection |

Examples:
```
pytest -m unit
pytest -m "integration and not slow"
pytest -m resilience -k redis
```

---

## 8. Running Tests

| Scenario | Command |
|----------|---------|
| Full suite (host) | `pytest` |
| Unit only | `pytest -m unit` |
| Integration only | `pytest -m integration` |
| E2E workflows | `pytest tests/e2e/` |
| With coverage | `pytest --cov=apps --cov=core` |
| Single test debug | `pytest tests/e2e/test_drift_workflow.py::test_drift_detected` |
| Inside container | `docker compose exec api pytest -m api` |

**Note:** Tests are executed directly via `pytest` (no `poetry run` prefix needed). When running inside containers, the Python environment at `/opt/venv` is already activated via the entrypoint, so `docker compose exec api pytest` works without additional setup.

---

## 9. Load & Performance Testing

Locust (baseline 50 users / 3m):
```
docker compose exec api locust -f locustfile.py --host http://localhost:8000 --users 50 --spawn-rate 10 --run-time 3m --headless --print-stats
```
KPIs (Day 17):
- Peak RPS: 103.8
- Avg RPS: 88.8
- P95: 2ms; P99: 3ms
- Max: 124ms

DB Aggregation (Day 18):
- CAGG speed gain: 37.3%
- Rows scanned reduction: 83.3%

---

## 10. ML Integrity & Hash Validation

| Aspect | Mechanism |
|--------|-----------|
| Feature Contract | `feature_names.txt` persisted with model |
| Hash Baseline | `baseline_hashes.json` compared in CI |
| Drift Tests | KS p-value + PSI (agent scripts) |
| Retrain Tests | Event → cooldown → version increment assertion |
| Model Loader | Run URI fallback (prevents registry partial issues) |

Run manual hash validation:
```
python scripts/validate_model_hashes.py
```

---

## 11. Resilience & Chaos Tests

| Fault | Injection | Expected Behavior |
|-------|-----------|------------------|
| Redis timeout | Toxiproxy timeout toxic | Idempotency disabled warning; ingestion proceeds |
| DB latency | Latency toxic (e.g. 500ms) | Retry budget respected; SLA monitored |
| Network partition | Bandwidth/timeout + cut | Event retries (tenacity) escalate then DLQ hook |
| Combined | Sequential toxics | Degradation logged; no crash |

---

## 12. Security & Rate Limiting Tests

| Test | Validation |
|------|-----------|
| Missing API key | 403 |
| Invalid key | 403 (no timing leak) |
| Rate limit exceed (drift endpoint) | 429 with retry headers |
| Dependency scan (CI) | Snyk job fail on high/critical |
| Input schema | Pydantic validation rejects malformed payloads |

---

## 13. Known Limitations

| Area | Detail | Mitigation |
|------|--------|-----------|
| Scheduling E2E | Time-of-day slot scarcity | Mock calendar / widen window future |
| Multi-replica idempotency | In-memory duplication not tested cluster-wide | Redis cluster test (future) |
| Long-horizon drift | Limited synthetic volume | Add historical backfill fixtures |
| Forecast backtest | Not continuous in CI | Scheduled periodic job (roadmap) |

---

## 14. CI Pipeline (Relevant Jobs)

| Job | Purpose |
|-----|---------|
| lint-type | Style & (optionally) mypy/static checks |
| tests | Executes full suite (excl. optional slow) |
| security-scan | Snyk + bandit + safety |
| model-hash-validation | Ensures artifact integrity |
| ml-train-validation | Re-trains anomaly / forecast (repro check) |
| (optional) load-test | Short read-only performance smoke |

---

## 15. Adding Tests (Checklist)

1. Identify layer & marker.
2. Use existing fixtures (avoid new global state).
3. Keep test ≤2s (unit) or justify `slow`.
4. Assert structure + boundary cases (not only "happy path").
5. Add docstring: intent & linkage to changelog day if applicable.
6. If new migration required for test data pattern—document rationale.

---

## 16. Troubleshooting Matrix

| Symptom | Cause | Action |
|---------|-------|--------|
| Async loop errors | Multiple event loops | Ensure session-scoped `event_loop` fixture |
| Model 404 in predict test | Registry not seeded | Run training Make target or use synthetic model fixture |
| Drift test returns insufficient data | Window too large / fresh DB | Seed readings before call |
| Hash mismatch failure | Model re-trained unintentionally | Reproduce locally; update baseline only if validated |
| Rate limit flakiness | Shared API key across parallel tests | Use unique test key per case |
| Redis connection refused | Container start order / network latency | Re-run after confirming service health |

---

## 17. Minimal Example (Pattern)

```python
@pytest.mark.integration
async def test_drift_endpoint_detects_no_drift(async_client, seeded_sensor_data):
    resp = await async_client.post("/api/v1/ml/check_drift", json={
        "sensor_id": "sensor-001",
        "window_minutes": 30,
        "p_value_threshold": 0.05,
        "min_samples": 10
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "p_value" in data
    assert data["reference_count"] >= 0
```

---

## 18. Exit Criteria Verification

| Criterion | Status |
|-----------|--------|
| Core workflows covered | ✅ |
| ML lifecycle reproducibility enforced | ✅ |
| Performance SLO validated | ✅ |
| Drift automation tested | ✅ |
| Security (rate limit + auth) verified | ✅ |
| Resilience scenarios covered | ✅ |
| Remaining test gap low risk | ✅ |

---

## 19. References

- Changelog: `../../30-day-sprint-changelog.md`
- Performance Baseline: `../docs/PERFORMANCE_BASELINE.md`
- DB Architecture: `../docs/db/README.md`
- ML Platform: `../docs/ml/README.md`
- Security Model: `../docs/SECURITY.md`
- Migration Strategy: `../docs/MICROSERVICE_MIGRATION_STRATEGY.md`

---

## 20. Summary

Test suite provides high-confidence coverage of functional flows, ML integrity, performance, resilience, and security controls with traceability to sprint deliverables. Single known failure is a low-impact scheduling edge case; all critical SLO and lifecycle assurances pass.

---
./scripts/run_tests.sh -m integration

# Executar testes sem usar container Docker
./scripts/run_tests.sh --no-container

# Executar testes com relatório de cobertura
./scripts/run_tests.sh --cov
```

## Configuração do Banco de Dados de Teste

A conexão do banco de dados de teste é configurada via arquivo `.env.test` ou variáveis de ambiente:

- Ao usar a abordagem de container Docker, detalhes de conexão são gerenciados automaticamente
- Ao usar a abordagem de banco direto (`--no-container`), a URL do banco de teste é determinada de:
  1. A variável de ambiente `DATABASE_TEST_URL`, se definida
  2. A `DATABASE_URL` padrão com o nome do banco acrescido de `_test`

## Melhores Práticas

1. **Isolamento**: Cada teste deve ser independente e não deixar efeitos colaterais
2. **Fixtures**: Use fixtures do pytest para configuração e limpeza de testes
3. **Assíncrono**: Use `@pytest.mark.asyncio` para testes assíncronos
4. **Marcadores**: Aplique marcadores apropriados para categorizar testes
5. **Mocking**: Use mocks para serviços externos quando apropriado
6. **Cobertura**: Busque alta cobertura de testes, especialmente para componentes críticos
